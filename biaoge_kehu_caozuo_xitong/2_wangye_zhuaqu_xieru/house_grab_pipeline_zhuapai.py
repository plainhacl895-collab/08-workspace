# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
房源抓取单入口总控脚本。

唯一正式入口：
    cmd /c D:\ExcelData\RUN_HOUSE_GRAB.cmd
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


WORK_DIR = Path(r"D:\ExcelData")
RUNTIME_DIR = WORK_DIR / "_house_grab_runtime"
LOG_DIR = WORK_DIR / "_house_grab_logs"
BACKUP_DIR = WORK_DIR / "_house_grab_backups"
LOG_FILE = LOG_DIR / "house_grab.log"
LOCK_FILE = RUNTIME_DIR / ".house_grab.lock"
DATA_JSON = RUNTIME_DIR / "data.json"
DATA_TMP = RUNTIME_DIR / "data.tmp"
EXCEL_FILE = WORK_DIR / "daily_followup.xlsm"
RESULT_JSON = RUNTIME_DIR / "last_run_result.json"
RESULT_TXT = RUNTIME_DIR / "last_run_result.txt"

STAGE1 = WORK_DIR / "stage1_grab.py"
STAGE3 = WORK_DIR / "stage3_write.py"

EXPECTED_DISTRICTS = ["长宁", "静安", "黄浦", "徐汇", "普陀", "闵行", "虹口", "杨浦", "嘉定", "浦东"]
RECENT_DAYS = 3
MIN_PRICE = 700.0
MAX_PRICE = 10000.0
MIN_ACCEPTABLE_ROWS = 1500
MIN_DISTRICTS_WITH_DATA = 8
SHEET_INDEX = 4
START_ROW = 4

MAX_RETRY_GRAB = 2
MAX_RETRY_WRITE = 1


class PipelineFailure(RuntimeError):
    pass


def log(stage: str, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stage}] {message}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {line}\n")
    
    # 同时写入临时状态文件，方便实时监控
    status_file = RUNTIME_DIR / "grab_status.txt"
    status_file.write_text(f"{timestamp} - {line}", encoding="utf-8")


def send_telegram_notification(payload: dict) -> None:
    """房源抓取完成后发送 Telegram 通知"""
    try:
        success = payload.get('success', False)
        data_count = payload.get('data_count', 0)
        excel_rows = payload.get('excel_rows', 0)
        message = payload.get('message', '')
        district_counts = payload.get('district_counts', {})
        started_at = payload.get('started_at', '')
        finished_at = payload.get('finished_at', '')
        
        # 计算耗时
        duration = "未知"
        if started_at and finished_at:
            try:
                start = datetime.strptime(started_at, "%Y-%m-%d %H:%M:%S")
                end = datetime.strptime(finished_at, "%Y-%m-%d %H:%M:%S")
                delta = end - start
                minutes = int(delta.total_seconds() // 60)
                seconds = int(delta.total_seconds() % 60)
                duration = f"{minutes}分{seconds}秒"
            except Exception:
                pass
        
        # 构建各区数据
        district_text = ""
        if district_counts:
            district_lines = []
            for district, count in district_counts.items():
                if count > 0:
                    district_lines.append(f"  {district}: {count}套")
            if district_lines:
                district_text = "\n\n📍 各区分布:\n" + "\n".join(district_lines)
        
        if success:
            text = f"🍡 <b>房源抓取完成！</b>\n\n"
            text += f"✅ 状态：成功\n"
            text += f"⏱️ 耗时：{duration}\n"
            text += f"📊 抓取到 <b>{data_count}</b> 套房源\n"
            text += f"💾 Excel 行数：{excel_rows}\n"
            text += district_text
            text += f"\n\n💬 详情：{message}"
        else:
            text = f"❌ <b>房源抓取失败！</b>\n\n"
            text += f"❌ 状态：失败\n"
            text += f"⏱️ 耗时：{duration}\n"
            text += f"📊 抓取到 <b>{data_count}</b> 套房源\n"
            text += f"💬 错误：{message}"
        
        # 佳佳的 Telegram ID
        chat_id = "8724466632"
        # 团团 Bot Token
        bot_token = "8705450288:AAExGrG5ZIKt3wUnoAZ2Bll4W2StzDVCOYY"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        data = urllib.parse.urlencode(params).encode()
        
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            if result.get("ok"):
                log("控制", "Telegram 通知已发送")
            else:
                log("控制", f"Telegram API 返回错误：{result}")
    except Exception as e:
        log("控制", f"发送 Telegram 通知失败：{e}")


def write_result(payload: dict) -> None:
    RESULT_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"success: {payload.get('success')}",
        f"started_at: {payload.get('started_at', '')}",
        f"finished_at: {payload.get('finished_at', '')}",
        f"message: {payload.get('message', '')}",
        f"data_count: {payload.get('data_count', 0)}",
        f"excel_rows: {payload.get('excel_rows', 0)}",
    ]
    if payload.get("district_counts"):
        district_text = ", ".join(f"{k}:{v}" for k, v in payload["district_counts"].items())
        lines.append(f"district_counts: {district_text}")
    if payload.get("backup_path"):
        lines.append(f"backup_path: {payload['backup_path']}")
    if payload.get("current_stage"):
        lines.append(f"current_stage: {payload['current_stage']}")
    RESULT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_log_tail(lines: int = 40) -> list[str]:
    if not LOG_FILE.exists():
        return []
    try:
        content = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        return content[-lines:]
    except Exception:
        return []


def check_lock() -> bool:
    if not LOCK_FILE.exists():
        return False

    try:
        pid = int(LOCK_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        LOCK_FILE.unlink(missing_ok=True)
        return False

    try:
        os.kill(pid, 0)
        return True
    except Exception:
        LOCK_FILE.unlink(missing_ok=True)
        return False


def set_lock() -> None:
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")


def release_lock() -> None:
    LOCK_FILE.unlink(missing_ok=True)


def cleanup_previous_outputs() -> None:
    for path in [DATA_JSON, DATA_TMP, RESULT_JSON, RESULT_TXT]:
        if path.exists():
            path.unlink()


def cleanup_data_outputs() -> None:
    for path in [DATA_JSON, DATA_TMP]:
        if path.exists():
            path.unlink()


def kill_excel_processes() -> None:
    log("控制", "清理 Excel 相关进程")
    subprocess.run(["taskkill", "/F", "/IM", "excel.exe"], capture_output=True)
    subprocess.run(["taskkill", "/F", "/IM", "dllhost.exe"], capture_output=True)
    time.sleep(3)


def run_stage(script_path: Path, stage_name: str, max_retry: int) -> dict:
    if not script_path.exists():
        raise PipelineFailure(f"{stage_name} 脚本不存在：{script_path}")

    env = os.environ.copy()
    env["HOUSE_GRAB_PIPELINE_RUN"] = "1"

    last_return_code = None
    for attempt in range(1, max_retry + 1):
        log("控制", f"执行 {stage_name}：第 {attempt}/{max_retry} 次")
        started = time.time()
        result = subprocess.run(
            [sys.executable, str(script_path)],
            env=env,
            cwd=str(WORK_DIR),
            capture_output=False,
        )
        elapsed = round(time.time() - started, 1)
        last_return_code = result.returncode
        log("控制", f"{stage_name} 返回码：{result.returncode}，耗时 {elapsed} 秒")
        if result.returncode == 0:
            return {
                "name": stage_name,
                "success": True,
                "attempt": attempt,
                "returncode": 0,
                "seconds": elapsed,
            }
        if attempt < max_retry:
            log("控制", f"{stage_name} 失败，10 秒后重试")
            time.sleep(10)

    return {
        "name": stage_name,
        "success": False,
        "attempt": max_retry,
        "returncode": last_return_code,
    }


def parse_recent_flag(list_date: str) -> bool:
    list_date = (list_date or "").strip()
    if list_date.endswith("天前"):
        raw_days = list_date[:-2].strip()
        try:
            return int(raw_days) <= RECENT_DAYS
        except ValueError:
            return False
    if "小时之前" in list_date:
        return True
    return False


def build_data_summary() -> dict:
    if not DATA_JSON.exists():
        return {
            "count": 0,
            "district_counts": {},
            "districts_with_data": 0,
            "missing_districts": EXPECTED_DISTRICTS[:],
            "min_price": None,
            "max_price": None,
            "missing_id_count": 0,
            "duplicate_id_count": 0,
            "invalid_district_count": 0,
            "out_of_price_count": 0,
            "rule_violation_count": 0,
            "block_code_empty_count": 0,
            "community_formula_bad_count": 0,
        }

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise PipelineFailure("data.json 不是数组结构")

    district_counter: Counter[str] = Counter()
    min_price: float | None = None
    max_price: float | None = None
    missing_id_count = 0
    duplicate_id_count = 0
    invalid_district_count = 0
    out_of_price_count = 0
    rule_violation_count = 0
    block_code_empty_count = 0
    community_formula_bad_count = 0
    seen_ids: set[str] = set()

    for item in data:
        district = str(item.get("district", "") or "").strip()
        if district:
            district_counter[district] += 1
        if district not in EXPECTED_DISTRICTS:
            invalid_district_count += 1

        house_id = str(item.get("house_id", "") or "").strip()
        if not house_id:
            missing_id_count += 1
        elif house_id in seen_ids:
            duplicate_id_count += 1
        else:
            seen_ids.add(house_id)

        price = float(item.get("price", 0) or 0)
        min_price = price if min_price is None else min(min_price, price)
        max_price = price if max_price is None else max(max_price, price)
        if price < MIN_PRICE or price > MAX_PRICE:
            out_of_price_count += 1

        score = float(item.get("score", 0) or 0)
        list_date = str(item.get("list_date", "") or "")
        if score < 6 and not parse_recent_flag(list_date):
            rule_violation_count += 1

        block_code = str(item.get("block_code", "") or "").strip()
        if not block_code:
            block_code_empty_count += 1

        community = str(item.get("community", "") or "").strip()
        if not community.startswith("=HYPERLINK("):
            community_formula_bad_count += 1

    district_counts = {district: district_counter.get(district, 0) for district in EXPECTED_DISTRICTS}
    missing_districts = [district for district in EXPECTED_DISTRICTS if district_counts.get(district, 0) <= 0]

    return {
        "count": len(data),
        "district_counts": district_counts,
        "districts_with_data": sum(1 for count in district_counts.values() if count > 0),
        "missing_districts": missing_districts,
        "min_price": min_price,
        "max_price": max_price,
        "missing_id_count": missing_id_count,
        "duplicate_id_count": duplicate_id_count,
        "invalid_district_count": invalid_district_count,
        "out_of_price_count": out_of_price_count,
        "rule_violation_count": rule_violation_count,
        "block_code_empty_count": block_code_empty_count,
        "community_formula_bad_count": community_formula_bad_count,
    }


def validate_data_summary(summary: dict) -> None:
    count = int(summary.get("count", 0) or 0)
    if count <= 0:
        raise PipelineFailure("抓取结果为空")
    if count < MIN_ACCEPTABLE_ROWS:
        raise PipelineFailure(f"抓取结果仅 {count} 套，低于最低阈值 {MIN_ACCEPTABLE_ROWS} 套")

    districts_with_data = int(summary.get("districts_with_data", 0) or 0)
    if districts_with_data < MIN_DISTRICTS_WITH_DATA:
        missing = "、".join(summary.get("missing_districts", [])) or "未知"
        raise PipelineFailure(f"仅 {districts_with_data} 个区有数据，缺失区：{missing}")

    if int(summary.get("missing_id_count", 0) or 0) > 0:
        raise PipelineFailure(f"存在 {summary['missing_id_count']} 套房源缺少 house_id")
    if int(summary.get("duplicate_id_count", 0) or 0) > 0:
        raise PipelineFailure(f"存在 {summary['duplicate_id_count']} 套重复 house_id")
    if int(summary.get("invalid_district_count", 0) or 0) > 0:
        raise PipelineFailure(f"存在 {summary['invalid_district_count']} 套房源区字段异常")
    if int(summary.get("out_of_price_count", 0) or 0) > 0:
        raise PipelineFailure(f"存在 {summary['out_of_price_count']} 套房源超出 {MIN_PRICE}-{MAX_PRICE} 万")
    if int(summary.get("rule_violation_count", 0) or 0) > 0:
        raise PipelineFailure(f"存在 {summary['rule_violation_count']} 套房源不满足房源分/近期规则")
    if int(summary.get("block_code_empty_count", 0) or 0) > 0:
        raise PipelineFailure(f"存在 {summary['block_code_empty_count']} 套房源缺少板块编码")
    if int(summary.get("community_formula_bad_count", 0) or 0) > 0:
        raise PipelineFailure(f"存在 {summary['community_formula_bad_count']} 套房源小区字段不是超链接公式")

    min_price = summary.get("min_price")
    max_price = summary.get("max_price")
    if min_price is None or max_price is None:
        raise PipelineFailure("无法计算价格范围")
    if min_price < MIN_PRICE or max_price > MAX_PRICE:
        raise PipelineFailure(f"价格范围异常：{min_price}-{max_price} 万")


def verify_saved_rows(path: Path) -> int:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    sheet_name = f"xl/worksheets/sheet{SHEET_INDEX}.xml"

    with ZipFile(path) as zf:
        xml = ET.fromstring(zf.read(sheet_name))

    rows = xml.find("x:sheetData", ns)
    if rows is None:
        return 0

    count = 0
    for row in rows.findall("x:row", ns):
        row_number = int(row.attrib.get("r", "0"))
        if row_number < START_ROW:
            continue
        has_value = False
        for cell in row.findall("x:c", ns):
            if (
                cell.find("x:v", ns) is not None
                or cell.find("x:is", ns) is not None
                or cell.find("x:f", ns) is not None
            ):
                has_value = True
                break
        if has_value:
            count += 1
    return count


def find_latest_backup() -> str:
    backups = sorted(
        BACKUP_DIR.glob("daily_followup.stage3_backup.*.xlsm"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return str(backups[0]) if backups else ""


def fail_and_exit(
    started_at: str,
    current_stage: str,
    message: str,
    summary: dict | None,
    stage_results: list[dict],
) -> int:
    summary = summary or build_data_summary()
    payload = {
        "entrypoint": str(WORK_DIR / "house_grab_pipeline.py"),
        "started_at": started_at,
        "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": False,
        "message": message,
        "data_count": int(summary.get("count", 0) or 0),
        "excel_rows": verify_saved_rows(EXCEL_FILE) if EXCEL_FILE.exists() else 0,
        "district_counts": summary.get("district_counts", {}),
        "backup_path": "",
        "stages": stage_results,
        "current_stage": current_stage,
        "log_tail": read_log_tail(),
    }
    write_result(payload)
    send_telegram_notification(payload)
    print("PIPELINE_RESULT: FAIL", flush=True)
    return 1


def main() -> int:
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_stage = "初始化"
    stage_results: list[dict] = []
    data_summary: dict | None = None

    try:
        # 发送开始通知
        log("控制", "房源抓取任务启动")
        try:
            import urllib.parse
            import urllib.request
            chat_id = "8724466632"
            bot_token = "8705450288:AAExGrG5ZIKt3wUnoAZ2Bll4W2StzDVCOYY"
            start_text = f"🍡 <b>房源抓取启动！</b>\n\n⏰ 时间：{started_at}\n📝 开始抓取上海各区房源..."
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            params = {"chat_id": chat_id, "text": start_text, "parse_mode": "HTML"}
            data = urllib.parse.urlencode(params).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            log("控制", f"发送开始通知失败：{e}")

        if check_lock():
            payload = {
                "entrypoint": str(WORK_DIR / "house_grab_pipeline.py"),
                "started_at": started_at,
                "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "success": False,
                "message": "已有抓取任务正在运行，请稍后再试",
                "data_count": 0,
                "excel_rows": 0,
                "district_counts": {},
                "backup_path": "",
                "stages": [],
                "current_stage": "锁检查",
                "log_tail": read_log_tail(),
            }
            write_result(payload)
            send_telegram_notification(payload)
            print("PIPELINE_RESULT: FAIL", flush=True)
            return 1

        set_lock()
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        cleanup_previous_outputs()
        write_result(
            {
                "entrypoint": str(WORK_DIR / "house_grab_pipeline.py"),
                "started_at": started_at,
                "finished_at": "",
                "success": False,
                "message": "流程已启动",
                "data_count": 0,
                "excel_rows": 0,
                "district_counts": {},
                "backup_path": "",
                "stages": [],
                "current_stage": "启动",
            }
        )

        current_stage = "阶段 1 抓取"
        for round_index in range(1, MAX_RETRY_GRAB + 1):
            cleanup_data_outputs()
            stage_name = f"阶段 1 抓取（总控重试 {round_index}/{MAX_RETRY_GRAB}）"
            result = run_stage(STAGE1, stage_name, 1)
            stage_results.append(result)

            if not result["success"]:
                if round_index < MAX_RETRY_GRAB:
                    log("控制", f"{stage_name} 失败，10 秒后整轮重抓")
                    time.sleep(10)
                    continue
                raise PipelineFailure(f"{stage_name} 执行失败，返回码 {result['returncode']}")

            data_summary = build_data_summary()
            try:
                validate_data_summary(data_summary)
                break
            except PipelineFailure as exc:
                log("控制", f"{stage_name} 结果校验失败：{exc}")
                if round_index < MAX_RETRY_GRAB:
                    log("控制", "10 秒后重新抓取整轮数据")
                    time.sleep(10)
                    continue
                raise

        if data_summary is None:
            raise PipelineFailure("未生成抓取结果摘要")

        current_stage = "阶段 3 写入 Excel"
        kill_excel_processes()
        write_result(
            {
                "entrypoint": str(WORK_DIR / "house_grab_pipeline.py"),
                "started_at": started_at,
                "finished_at": "",
                "success": False,
                "message": "阶段 1 已完成，准备写入 Excel",
                "data_count": int(data_summary.get("count", 0) or 0),
                "excel_rows": 0,
                "district_counts": data_summary.get("district_counts", {}),
                "backup_path": "",
                "stages": stage_results,
                "current_stage": current_stage,
            }
        )

        stage3_result = run_stage(STAGE3, "阶段 3 写入 Excel", MAX_RETRY_WRITE)
        stage_results.append(stage3_result)
        if not stage3_result["success"]:
            raise PipelineFailure(f"阶段 3 写入 Excel 失败，返回码 {stage3_result['returncode']}")

        excel_rows = verify_saved_rows(EXCEL_FILE)
        data_count = int(data_summary.get("count", 0) or 0)
        if excel_rows != data_count:
            raise PipelineFailure(f"Excel 实际数据行数 {excel_rows} 与抓取条数 {data_count} 不一致")

        # 【新增】刷新团团助手缓存，确保后续查询能读到最新房源
        log("控制", "刷新团团助手缓存")
        try:
            refresh_script = str(WORK_DIR / "tools" / "RUN_TUANTUAN_qidong.cmd")
            subprocess.run(
                ["cmd", "/c", refresh_script, "refresh"],
                cwd=str(WORK_DIR),
                capture_output=False,
                timeout=120,
            )
            log("控制", "OK: 缓存刷新完成")
        except Exception as exc:
            log("控制", f"WARNING: 缓存刷新失败：{exc}（不影响已写入的房源数据）")

        # 【新增】打开 Excel 并定位到房源表第一行，方便查看
        log("控制", "打开 Excel 并定位到房源表...")
        try:
            import win32com.client
            xl = win32com.client.Dispatch("Excel.Application")
            wb = xl.Workbooks.Open(str(EXCEL_FILE), False, False, 5, "000")
            ws = wb.Worksheets.Item(4)  # 房源表
            xl.Visible = True
            ws.Activate()
            wb.Activate()
            # 定位到房源表第一行（表头）
            cell = ws.Cells(3, 1)  # 第 3 行第 1 列（表头）
            cell.Select()
            xl.ActiveWindow.ScrollRow = 3
            xl.ActiveWindow.ScrollColumn = 1
            log("控制", "OK: Excel 已打开并定位到房源表")
        except Exception as exc:
            log("控制", f"WARNING: 打开 Excel 失败：{exc}（不影响已写入的房源数据）")

        backup_path = find_latest_backup()
        current_stage = "完成"
        payload = {
            "entrypoint": str(WORK_DIR / "house_grab_pipeline.py"),
            "started_at": started_at,
            "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "success": True,
            "message": f"抓取并写入成功，共 {data_count} 套，Excel 行数 {excel_rows}",
            "data_count": data_count,
            "excel_rows": excel_rows,
            "district_counts": data_summary.get("district_counts", {}),
            "backup_path": backup_path,
            "stages": stage_results,
            "current_stage": current_stage,
        }
        write_result(payload)
        send_telegram_notification(payload)
        print("PIPELINE_RESULT: SUCCESS", flush=True)
        print(f"PIPELINE_HOUSES: {data_count}", flush=True)
        print(f"PIPELINE_EXCEL_ROWS: {excel_rows}", flush=True)
        return 0

    except PipelineFailure as exc:
        return fail_and_exit(started_at, current_stage, str(exc), data_summary, stage_results)
    except Exception as exc:
        return fail_and_exit(started_at, current_stage, f"未处理异常：{exc}", data_summary, stage_results)
    finally:
        release_lock()


if __name__ == "__main__":
    if os.environ.get("HOUSE_GRAB_CMD_ENTRY") != "1" and "--direct" not in sys.argv[1:]:
        print("ERROR: 请运行 D:\\ExcelData\\RUN_HOUSE_GRAB.cmd，不要直接运行 house_grab_pipeline.py")
        sys.exit(2)
    sys.exit(main())

