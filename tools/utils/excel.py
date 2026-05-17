# -*- coding: utf-8 -*-
"""Excel 操作工具函数"""

import subprocess
import time
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional

try:
    import pythoncom
    from win32com.client import DispatchEx, GetObject
except ImportError:
    pythoncom = None
    DispatchEx = None
    GetObject = None

# 配置
WORKBOOK_PATH = Path(r"D:\Unique work form\daily_followup.xlsm")
WORKBOOK_PASSWORD = "000"
CLIENT_SHEET_INDEX = 2  # "客户不要猜" 工作表
FIRST_FOLLOWUP_COLUMN = 365  # 第一列跟进


def write_followup_via_excel(*, row_number: int, content: str, date_str: str) -> dict[str, Any]:
    """
    通过 Excel 写入跟进记录
    
    Args:
        row_number: 客户所在行号
        content: 跟进内容
        date_str: 日期字符串
    
    Returns:
        写入结果字典
    """
    if pythoncom is None or DispatchEx is None or GetObject is None:
        raise RuntimeError("win32com 不可用，无法进行安全写入。")
    
    # 写入前先保存 Excel，再清理进程，避免文件被占用导致只读
    print("写入前保存并关闭 Excel...", flush=True)
    try:
        existing_excel = None
        try:
            existing_excel = GetObject(Class="Excel.Application")
            saved_count = 0
            for wb in existing_excel.Workbooks:
                if not wb.Saved:
                    wb.Save()
                    saved_count += 1
            if saved_count > 0:
                print(f"已自动保存 {saved_count} 个 Excel 文件", flush=True)
            existing_excel.Quit()
            time.sleep(2)
        except:
            pass
        finally:
            if existing_excel:
                try:
                    existing_excel.Quit()
                except:
                    pass
    except:
        pass
    
    # 强制杀掉残留的 Excel 进程
    subprocess.run(["taskkill", "/F", "/IM", "excel.exe"], capture_output=True)
    time.sleep(2)
    print("OK: Excel 已关闭", flush=True)
    
    # 智能识别日期
    target_date = parse_followup_date_from_content(content, date_str)
    content = clean_text(content)
    if not content:
        raise ValueError("跟进内容为空。")
    
    pythoncom.CoInitialize()
    excel = None
    workbook = None
    
    try:
        excel = DispatchEx("Excel.Application")
        excel.DisplayAlerts = False
        
        workbook = excel.Workbooks.Open(
            Filename=str(WORKBOOK_PATH),
            UpdateLinks=0,
            ReadOnly=False,
            Password=WORKBOOK_PASSWORD,
        )
        
        ws = workbook.Worksheets(CLIENT_SHEET_INDEX)
        header_row = 11  # 日期标题行号
        date_target = find_or_create_date_column(ws, target_date)
        target_col = date_target["column"]
        
        # 检查是否覆盖组别标记
        existing = clean_text(ws.Cells(row_number, target_col).Value)
        if target_col == FIRST_FOLLOWUP_COLUMN and looks_like_group(existing):
            raise RuntimeError("首个跟进列仍占用组别标记，拒绝覆盖，请改用更晚日期。")
        
        # 合并内容
        if existing and existing != content:
            content = f"{existing}\n{content}"
            action = "appended"
        elif existing == content:
            action = "unchanged"
        else:
            action = "written"
        
        ws.Cells(row_number, target_col).Value = content
        
        # 应用格式：与历史跟进保持一致
        _apply_followup_format(ws, row_number, target_col, header_row)
        
        workbook.Save()
        
        # 打开 Excel 并定位到写入位置
        excel.Visible = True
        ws.Activate()
        workbook.Activate()
        cell = ws.Cells(row_number, target_col)
        cell.Select()
        excel.ActiveWindow.ScrollRow = row_number
        excel.ActiveWindow.ScrollColumn = target_col
        print(f"已打开 Excel 并定位到第 {row_number} 行，第 {target_col} 列", flush=True)
        
        # 不关闭 Excel，保持打开状态让用户查看
        workbook = None
        excel = None
        
        return {
            "row": row_number,
            "column": target_col,
            "date": target_date.isoformat(),
            "content": content,
            "action": action,
            "created_new_date_column": date_target.get("created", False),
        }
        
    finally:
        if workbook is not None:
            try:
                workbook.Close(SaveChanges=False)
            except:
                pass
        if excel is not None:
            try:
                excel.Quit()
            except:
                pass


def parse_followup_date_from_content(content: str, default_date_str: str) -> date:
    """从跟进内容中智能识别日期"""
    import re
    
    # 尝试从内容中提取日期
    date_patterns = [
        r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日号]?',
        r'(\d{4})(\d{2})(\d{2})',
        r'今天|今日',
        r'昨天|昨日',
        r'明天|明日',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, content)
        if match:
            if pattern == r'今天 | 今日':
                return date.today()
            elif pattern == r'昨天 | 昨日':
                from datetime import timedelta
                return date.today() - timedelta(days=1)
            elif pattern == r'明天 | 明日':
                from datetime import timedelta
                return date.today() + timedelta(days=1)
            else:
                try:
                    year, month, day = map(int, match.groups())
                    return date(year, month, day)
                except:
                    continue
    
    # 默认使用传入的日期
    try:
        return datetime.strptime(default_date_str, "%Y-%m-%d").date()
    except:
        return date.today()


def find_or_create_date_column(ws, target_date: date) -> dict[str, Any]:
    """查找或创建日期列"""
    header_row = 11
    
    # 查找现有日期列
    for col in range(FIRST_FOLLOWUP_COLUMN, FIRST_FOLLOWUP_COLUMN + 1000):
        cell_val = ws.Cells(header_row, col).Value
        if cell_val:
            try:
                if isinstance(cell_val, (datetime, date)):
                    cell_date = cell_val.date() if isinstance(cell_val, datetime) else cell_val
                    if cell_date == target_date:
                        return {"column": col, "created": False}
            except:
                continue
    
    # 创建新日期列
    for col in range(FIRST_FOLLOWUP_COLUMN, FIRST_FOLLOWUP_COLUMN + 1000):
        cell_val = ws.Cells(header_row, col).Value
        if not cell_val or str(cell_val).strip() == "":
            # Use 12:00:00 to avoid UTC timezone shifting date backwards
            safe_dt = datetime(target_date.year, target_date.month, target_date.day, 12, 0, 0)
            ws.Cells(header_row, col).Value = safe_dt
            # Set custom format with weekday
            ws.Cells(header_row, col).NumberFormat = 'yyyy-mm-dd aaaa'
            return {"column": col, "created": True}
    
    raise RuntimeError("无法找到或创建日期列")


def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ""
    return str(text).strip()


def looks_like_group(text: str) -> bool:
    """判断是否像组别标记"""
    if not text:
        return False
    text = clean_text(text)
    return text.startswith("组") or text.startswith("分组") or len(text) < 10


def _apply_followup_format(ws, row_number: int, target_col: int, header_row: int):
    """
    应用跟进单元格格式：与历史保持一致
    
    - 自动检测历史跟进内容的格式（字体大小、对齐方式）
    - 应用到新写入的单元格
    - 日期标题格式统一
    """
    try:
        # 1. 检测历史格式：查找同一行前面的跟进单元格
        ref_font_size = 10  # 默认值
        ref_font_name = "微软雅黑"
        ref_h_align = -4108  # xlCenter
        ref_v_align = -4108  # xlCenter
        ref_wrap = True
        
        # 从目标列往前找，找到第一个有内容的跟进单元格作为参考
        for ref_col in range(target_col - 1, FIRST_FOLLOWUP_COLUMN - 1, -1):
            ref_cell = ws.Cells(row_number, ref_col)
            if ref_cell.Value and clean_text(ref_cell.Value):
                try:
                    ref_font_size = ref_cell.Font.Size
                    ref_font_name = ref_cell.Font.Name
                    ref_h_align = ref_cell.HorizontalAlignment
                    ref_v_align = ref_cell.VerticalAlignment
                    ref_wrap = ref_cell.WrapText
                except:
                    pass
                break
        
        # 2. 应用格式到跟进内容单元格
        content_cell = ws.Cells(row_number, target_col)
        
        font = content_cell.Font
        font.Name = ref_font_name
        font.Size = ref_font_size
        
        content_cell.HorizontalAlignment = ref_h_align
        content_cell.VerticalAlignment = ref_v_align
        content_cell.WrapText = ref_wrap
        
        # 3. 设置日期标题单元格格式
        header_cell = ws.Cells(header_row, target_col)
        header_font = header_cell.Font
        header_font.Name = "微软雅黑"
        header_font.Size = 10
        header_font.Bold = True
        
        header_cell.HorizontalAlignment = -4108  # xlCenter
        header_cell.VerticalAlignment = -4108    # xlCenter
        
    except Exception as e:
        print(f"格式设置警告：{e}", flush=True)


def update_client_fields_via_excel(row_number: int, updates: dict[str, Any]) -> dict[str, Any]:
    """
    通过 Excel 更新客户字段
    
    Args:
        row_number: 客户所在行号
        updates: 更新字典 {字段名：新值}
    
    Returns:
        更新结果字典
    """
    if pythoncom is None or DispatchEx is None or GetObject is None:
        raise RuntimeError("win32com 不可用。")
    
    # 先保存并关闭 Excel
    print("更新前保存并关闭 Excel...", flush=True)
    try:
        existing_excel = GetObject(Class="Excel.Application")
        for wb in existing_excel.Workbooks:
            if not wb.Saved:
                wb.Save()
        existing_excel.Quit()
        time.sleep(2)
    except:
        pass
    
    subprocess.run(["taskkill", "/F", "/IM", "excel.exe"], capture_output=True)
    time.sleep(2)
    print("OK: Excel 已关闭", flush=True)
    
    pythoncom.CoInitialize()
    excel = None
    workbook = None
    
    try:
        excel = DispatchEx("Excel.Application")
        excel.DisplayAlerts = False
        workbook = excel.Workbooks.Open(
            Filename=str(WORKBOOK_PATH),
            UpdateLinks=0,
            ReadOnly=False,
            Password=WORKBOOK_PASSWORD,
        )
        
        ws = workbook.Worksheets(CLIENT_SHEET_INDEX)
        
        # 字段映射：字段名 -> 列号
        field_columns = {
            "grade": 3,
            "budget": 5,
            "district": 6,
            "rooms": 4,
            "phone": 2,
            "notes": 10,
        }
        
        updated_fields = []
        for field, value in updates.items():
            if field in field_columns:
                col = field_columns[field]
                ws.Cells(row_number, col).Value = value
                updated_fields.append(field)
        
        workbook.Save()
        
        return {
            "row": row_number,
            "updated_fields": updated_fields,
            "updates": updates,
        }
        
    finally:
        if workbook is not None:
            try:
                workbook.Close(SaveChanges=False)
            except:
                pass
        if excel is not None:
            try:
                excel.Quit()
            except:
                pass
