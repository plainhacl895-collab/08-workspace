# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""阶段 3：离线写入 Excel，并保持模板样式一致。默认不允许单独运行。

【重要】使用 win32com 而非 openpyxl，确保保留 VBA 宏代码。
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 导入 win32com（用于 Excel 操作，保留宏）
try:
    import win32com.client
    import pythoncom
except ImportError:
    win32com = None
    pythoncom = None


# 脚本所在目录（工作区 tools）
SCRIPT_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = SCRIPT_DIR / "_house_grab_runtime"
LOG_DIR = SCRIPT_DIR / "_house_grab_logs"
BACKUP_DIR = SCRIPT_DIR / "_house_grab_backups"
DATA_JSON = RUNTIME_DIR / "data.json"
EXCEL_FILE = Path(r"D:\Unique work form\daily_followup.xlsm")
LOG_FILE = LOG_DIR / "house_grab.log"
SHEET_INDEX = 4
HEADER_ROW = 3  # 表头行
START_ROW = 4   # 数据起始行
TOTAL_COLUMNS = 12
CLEAR_COLUMNS = 14
COMMUNITY_COLUMN = 3
HOUSE_ID_COLUMN = 13
DETAIL_URL_COLUMN = 14
MAX_RETRY = 2
PROGRESS_STEP = 200
MAX_BACKUPS_KEEP = 12
AGE_LIBRARY_SHEET_INDEX = 8


def log(stage: str, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stage}] {message}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {line}\n")


def direct_run_allowed() -> bool:
    return os.environ.get("HOUSE_GRAB_PIPELINE_RUN") == "1" or "--direct" in sys.argv[1:]


def resolve_block_code(house: dict) -> str:
    block_code = str(house.get("block_code", "") or "").strip()
    if block_code:
        return block_code

    plate = str(house.get("plate", "") or "").strip()
    house_code = str(house.get("house_code", "") or "").strip()
    if plate and house_code:
        return f"{plate}{house_code}"
    if house_code:
        return house_code

    house_id = str(house.get("house_id", "") or "").strip()
    if plate and house_id:
        return f"{plate}{house_id}"
    return house_id


def normalize_community_name(value: object) -> str:
    text = str(value or "").strip().replace("\u3000", " ")
    return "".join(text.split()).lower()


def load_age_lookup_from_excel(excel_app, workbook) -> dict[str, str]:
    """从小区房龄库加载房龄数据"""
    try:
        # 尝试按名称获取
        if "小区房龄库" in [ws.Name for ws in workbook.Worksheets]:
            ws = workbook.Worksheets("小区房龄库")
        else:
            # 按索引获取
            ws = workbook.Worksheets(AGE_LIBRARY_SHEET_INDEX)
        
        lookup: dict[str, str] = {}
        last_row = ws.UsedRange.Rows.Count
        
        for row_index in range(1, last_row + 1):
            community_name = ws.Cells(row_index, 1).Value
            age_value = ws.Cells(row_index, 2).Value
            
            if not community_name or age_value in (None, ""):
                continue
            
            key = normalize_community_name(str(community_name))
            lookup.setdefault(key, str(age_value).strip())
        
        return lookup
    except Exception as e:
        log("阶段 3", f"警告：房龄库加载失败：{e}")
        return {}


def resolve_age(house: dict, age_lookup: dict[str, str]) -> str:
    for candidate in [
        house.get("community_name"),
        house.get("community"),
        house.get("title"),
    ]:
        key = normalize_community_name(candidate)
        if key and key in age_lookup:
            return age_lookup[key]
    return str(house.get("age", "") or "").strip()


def resolve_detail_url(house: dict) -> str:
    detail_url = str(house.get("url", "") or "").strip()
    if detail_url:
        return detail_url

    house_id = str(house.get("house_id", "") or "").strip()
    if house_id:
        return f"https://house.link.lianjia.com/housedel/view?housedelCode={house_id}"
    return ""


def backup_workbook() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"{EXCEL_FILE.stem}.stage3_backup.{timestamp}{EXCEL_FILE.suffix}"
    shutil.copy2(EXCEL_FILE, backup_path)
    return backup_path


def cleanup_old_backups(max_keep: int = MAX_BACKUPS_KEEP) -> None:
    backups = sorted(
        BACKUP_DIR.glob("daily_followup.stage3_backup.*.xlsm"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for old_backup in backups[max_keep:]:
        old_backup.unlink(missing_ok=True)


def verify_saved_rows(path: Path) -> int:
    """验证保存后的行数"""
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


def _force_kill_excel(except_pids=None) -> None:
    """强制杀掉所有 Excel 进程（防止僵尸进程锁定文件）"""
    import subprocess
    try:
        subprocess.run(["taskkill", "/F", "/IM", "EXCEL.EXE"], check=False, capture_output=True)
    except Exception:
        pass


def _check_file_is_readonly() -> bool:
    """检测目标文件是否被其他进程锁定"""
    try:
        with open(EXCEL_FILE, "a"):
            return False
    except PermissionError:
        return True


def run_write() -> tuple[bool, str]:
    stage = "阶段 3"
    log(stage, "开始离线写入 Excel（使用 win32com，保留宏）")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_JSON.exists():
        return False, f"data.json 不存在：{DATA_JSON}"
    if not EXCEL_FILE.exists():
        return False, f"Excel 文件不存在：{EXCEL_FILE}"

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    count = len(data)
    log(stage, f"读取到 {count} 套房源")
    if count == 0:
        return False, "没有可写入的数据"

    # 🔒 保护机制 1：写入前清理残留 Excel 进程
    log(stage, "🔧 清理可能残留的 Excel 进程...")
    _force_kill_excel()
    time.sleep(2)

    if _check_file_is_readonly():
        log(stage, "❌ 文件仍被锁定，可能被用户手动打开")
        return False, "文件被其他程序占用，请先关闭 Excel 中的 daily_followup.xlsm"

    backup_path = backup_workbook()
    cleanup_old_backups()
    log(stage, f"已备份工作簿：{backup_path.name}")

    excel = None
    wb = None
    
    try:
        # 创建 Excel 实例
        log(stage, "创建 Excel 实例...")
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        # 打开工作簿
        log(stage, f"打开工作簿：{EXCEL_FILE}")
        wb = excel.Workbooks.Open(str(EXCEL_FILE))
        
        # 获取目标工作表
        target_sheet_name = "房      源"
        try:
            ws = wb.Worksheets(target_sheet_name)
        except:
            ws = wb.Worksheets(SHEET_INDEX)
        
        log(stage, f"目标工作表：{ws.Name}")
        
        # 加载房龄库
        log(stage, "加载房龄库...")
        age_lookup = load_age_lookup_from_excel(excel, wb)
        log(stage, f"房龄库加载完成：{len(age_lookup)} 条记录")
        
        # 计算房龄匹配
        matched_age_count = 0
        for house in data:
            age = resolve_age(house, age_lookup)
            if age:
                matched_age_count += 1
        log(stage, f"房龄自动匹配：{matched_age_count}/{count} 套")
        
        # 清空旧数据
        max_row = ws.UsedRange.Rows.Count
        log(stage, f"清空旧数据区域：第 {START_ROW} 行到第 {max_row} 行")
        
        if max_row >= START_ROW:
            # 清空数据区域（保留表头）
            ws.Range(ws.Cells(START_ROW, 1), ws.Cells(max_row, CLEAR_COLUMNS)).ClearContents()
        
        # 写入新数据
        log(stage, "开始写入新数据...")
        
        headers = [
            "行政区",
            "plate_code",
            "小区",
            "户型",
            "面积",
            "总价 (万)",
            "单价",
            "楼层",
            "房源分",
            "创建时间",
            "维护人",
            "房龄",
            "house_id",
            "detail_url",
        ]
        
        # 检查表头是否存在
        existing_header = ws.Cells(HEADER_ROW, 1).Value
        if existing_header in (None, ""):
            log(stage, "表头为空，写入新表头")
            for col_idx, header in enumerate(headers, start=1):
                ws.Cells(HEADER_ROW, col_idx).Value = header
        else:
            log(stage, f"表头已存在（{existing_header}），跳过表头写入")
        
        # 隐藏辅助列
        ws.Columns("M:M").Hidden = True
        ws.Columns("N:N").Hidden = True
        
        # 批量构建数据数组（减少 COM 调用次数）
        log(stage, "批量构建写入数据...")
        data_2d = []
        for house in data:
            row_data = [
                house.get("district", ""),
                resolve_block_code(house),
                house.get("community", ""),
                house.get("layout", ""),
                house.get("area", ""),
                house.get("price", 0),
                house.get("unit_price", ""),
                house.get("floor", ""),
                house.get("score", 0),
                house.get("list_date", ""),
                house.get("maintainer", ""),
                resolve_age(house, age_lookup),
                str(house.get("house_id", "") or "").strip(),
                resolve_detail_url(house),
            ]
            data_2d.append(row_data)

        # 一次性写入整个区域（41,580 次调用 → 1 次调用）
        log(stage, "批量写入数据到 Excel...")
        start_cell = ws.Cells(START_ROW, 1)
        end_cell = ws.Cells(START_ROW + count - 1, 14)
        ws.Range(start_cell, end_cell).Value = data_2d
        log(stage, f"已写入 {count}/{count} 行")
        
        # 设置筛选范围
        last_row = START_ROW + count - 1
        filter_ref = f"A{HEADER_ROW}:N{last_row}"
        ws.AutoFilterMode = False
        ws.Range(ws.Cells(HEADER_ROW, 1), ws.Cells(last_row, 14)).AutoFilter()
        log(stage, f"设置筛选范围：{filter_ref}")
        
        # 保存工作簿
        log(stage, "保存工作簿...")
        wb.Save()
        log(stage, "数据写入完成，文件已保存")
        
        # 关闭工作簿和 Excel
        log(stage, "关闭 Excel...")
        wb.Close(SaveChanges=False)
        excel.Quit()
        log(stage, "✅ Excel 已正常关闭")
        
        # 释放 COM 对象
        import pythoncom
        try:
            pythoncom.CoUninitialize()
        except:
            pass
        
        # 验证保存结果
        saved_rows = verify_saved_rows(EXCEL_FILE)
        log(stage, f"保存后校验到 {saved_rows} 行数据")
        
        if saved_rows != count:
            return False, f"Excel 实际数据行数 {saved_rows} 与 JSON 条数 {count} 不一致"
        
        log(stage, "已跳过宏：区域房龄刷新（该宏会截断房源行数）")
        return True, f"写入完成，共 {count} 套"

    except Exception as exc:
        log(stage, f"ERROR: {exc}")
        import traceback
        log(stage, traceback.format_exc())
        
        # 出错时清理资源
        try:
            if wb:
                wb.Close(SaveChanges=False)
            if excel:
                excel.Quit()
            log(stage, "✅ Excel 已通过异常处理关闭")
        except:
            pass
        
        return False, f"写入失败：{exc}"
    
    finally:
        # 🔒 保护机制 3：确保所有 Excel 进程被清理（防止僵尸进程）
        log(stage, "🔧 最终清理：强制释放所有 Excel 进程...")
        _force_kill_excel()
        time.sleep(1)
        log(stage, "✅ 清理完成")


def main() -> int:
    for attempt in range(1, MAX_RETRY + 1):
        log("阶段 3", f"写入尝试 {attempt}/{MAX_RETRY}")
        success, message = run_write()
        if success:
            log("阶段 3", message)
            return 0
        log("阶段 3", f"ERROR: {message}")
        if attempt < MAX_RETRY:
            log("阶段 3", "2 秒后重试")
            time.sleep(2)

    log("阶段 3", "ERROR: 多次重试后仍然失败")
    return 1


if __name__ == "__main__":
    if not direct_run_allowed():
        print("ERROR: 请运行 RUN_HOUSE_GRAB.cmd，不要单独运行 stage3_write.py")
        sys.exit(2)
    sys.exit(main())
