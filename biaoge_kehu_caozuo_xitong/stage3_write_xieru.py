# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""阶段 3：离线写入 Excel，并保持模板样式一致。默认不允许单独运行。"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import time
import warnings
import xml.etree.ElementTree as ET
from copy import copy
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

import win32com.client

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


ROOT_DIR = Path(r"D:\Unique work form")
RUNTIME_DIR = ROOT_DIR / "_house_grab_runtime"
LOG_DIR = ROOT_DIR / "_house_grab_logs"
BACKUP_DIR = ROOT_DIR / "_house_grab_backups"
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

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


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


def load_age_lookup_from_excel(workbook) -> dict[str, str]:
    """从 Excel 房龄库加载数据（win32com 版本）"""
    try:
        ws = workbook.Worksheets("小区房龄库")
    except:
        ws = workbook.Worksheets(AGE_LIBRARY_SHEET_INDEX)

    lookup = {}
    for row_index in range(1, ws.UsedRange.Rows.Count + 1):
        community_name = ws.Cells(row_index, 1).Value
        age_value = ws.Cells(row_index, 2).Value
        key = normalize_community_name(community_name)
        if not key or age_value in (None, ""):
            continue
        lookup[key] = str(age_value).strip()

    return lookup


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


def build_rows(data: list[dict], age_lookup: dict[str, str]) -> list[list]:
    rows: list[list] = []
    for house in data:
        house_id = str(house.get("house_id", "") or "").strip()
        rows.append(
            [
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
                house_id,
                resolve_detail_url(house),
            ]
        )
    return rows


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


def load_target_sheet(workbook):
    if "房      源" in workbook.sheetnames:
        return workbook["房      源"]
    return workbook.worksheets[SHEET_INDEX - 1]


def collect_template(ws) -> tuple[list, float | None]:
    # 【简化】不复制复杂样式，只记录行高
    # 字体样式直接用 win32com 设置
    try:
        row_height = ws.Rows(START_ROW).RowHeight
    except:
        row_height = None
    return [], row_height


def apply_row_style(ws, row_index: int, template_styles: list, template_row_height: float | None) -> None:
    # 【简化】使用 win32com 设置基本样式
    if template_row_height is not None:
        try:
            ws.Rows(row_index).RowHeight = template_row_height
        except:
            pass

    # 设置小区单元格字体为黑色、无下划线
    try:
        community_cell = ws.Cells(row_index, COMMUNITY_COLUMN)
        community_cell.Font.Color = 0  # 黑色
        community_cell.Font.Underline = False
    except:
        pass


def clear_old_rows(ws, last_row: int) -> None:
    for row_index in range(START_ROW, last_row + 1):
        for column in range(1, CLEAR_COLUMNS + 1):
            ws.cell(row_index, column).value = None


def run_write() -> tuple[bool, str]:
    stage = "阶段 3"
    log(stage, "开始离线写入 Excel")
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

    backup_path = backup_workbook()
    cleanup_old_backups()
    log(stage, f"已备份工作簿：{backup_path.name}")

    import pythoncom
    pythoncom.CoInitialize()
    
    excel = None
    wb = None
    try:
        log(stage, "创建 Excel 实例...")
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        log(stage, "打开 Excel 文件...")
        wb = excel.Workbooks.Open(str(EXCEL_FILE))
        log(stage, f"已打开：{EXCEL_FILE.name}")
        ws = wb.Worksheets(SHEET_INDEX)
        log(stage, f"工作表：{ws.Name}")
        
        age_lookup = load_age_lookup_from_excel(wb)
        rows = build_rows(data, age_lookup)
        log(stage, f"房龄自动匹配：{len([r for r in rows if r[11]])}/{count} 套")

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

        # 清空旧数据
        max_row = ws.UsedRange.Rows.Count
        log(stage, f"清空旧数据区域：第 {START_ROW} 行到第 {max_row} 行")
        for row_index in range(START_ROW, max_row + 1):
            for col in range(1, CLEAR_COLUMNS + 1):
                ws.Cells(row_index, col).Value = None

        # 检查表头
        existing_header = ws.Cells(HEADER_ROW, 1).Value
        if existing_header is None or str(existing_header).strip() == "":
            log(stage, "表头为空，写入新表头")
            for col, header in enumerate(headers, start=1):
                ws.Cells(HEADER_ROW, col).Value = header
        else:
            log(stage, f"表头已存在，跳过表头写入")

        # 隐藏 M 列和 N 列
        ws.Columns("M").Hidden = True
        ws.Columns("N").Hidden = True

        # 写入数据
        for row_index, row_values in enumerate(rows, start=START_ROW):
            # 设置行高
            ws.Rows(row_index).RowHeight = ws.Rows(START_ROW).RowHeight
            
            # 写入值
            for col, value in enumerate(row_values, start=1):
                ws.Cells(row_index, col).Value = value
            
            # 设置字体（非粗体）
            for col in range(1, TOTAL_COLUMNS + 1):
                cell = ws.Cells(row_index, col)
                cell.Font.Bold = False
                cell.Font.Size = 11
                cell.Font.Name = "宋体"
            
            # 小区列特殊处理（黑色，无下划线）
            community_cell = ws.Cells(row_index, COMMUNITY_COLUMN)
            community_cell.Font.Color = 0  # 黑色
            community_cell.Font.Underline = False
            
            # 设置背景色（浅灰色）
            ws.Rows(row_index).Interior.Color = 0xF2F2F2

            written = row_index - START_ROW + 1
            if written % PROGRESS_STEP == 0 or written == count:
                log(stage, f"已写入 {written}/{count} 行")

        # 设置筛选范围
        last_row = START_ROW + count - 1
        filter_ref = f"A{HEADER_ROW}:N{last_row}"
        ws.AutoFilter.Range = ws.Range(f"A{HEADER_ROW}", f"N{last_row}")
        log(stage, f"设置筛选范围：{filter_ref}")

        # 保存并关闭
        log(stage, "保存工作簿")
        wb.Save()
        wb.Close()
        excel.Quit()
        pythoncom.CoUninitialize()
        
        log(stage, f"写入完成，共 {count} 套")
        log(stage, "已跳过宏：区域房龄刷新（该宏会截断房源行数）")
        return True, f"写入完成，共 {count} 套"

    except Exception as exc:
        if wb:
            try:
                wb.Close(False)
            except:
                pass
        if excel:
            try:
                excel.Quit()
            except:
                pass
        pythoncom.CoUninitialize()
        return False, f"写入失败：{exc}"


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
        print("ERROR: 请运行 D:\\Unique work form\\RUN_HOUSE_GRAB.cmd，不要单独运行 stage3_write.py")
        sys.exit(2)
    sys.exit(main())
