# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
import sys
import os
import time
import subprocess
from datetime import date

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import win32com.client

FILE_PATH = r"C:\Users\Huawei\.openclaw\workspace-tuantuan\biaoge_kehu_caozuo_xitong\daily_followup.xlsm"
TODAY = date.today()

def save_all_workbooks():
    """Save all open Excel workbooks without closing Excel"""
    print("Saving all open Excel workbooks...")
    try:
        excel = win32com.client.GetActiveObject("Excel.Application")
        for w in excel.Workbooks:
            if not w.Saved:
                print(f"  Saving: {w.Name}")
                w.Save()
        print("  All workbooks saved.")
    except:
        pass  # Excel not running

def write_followup():
    try:
        print("Creating new Excel instance...")
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        print(f"Opening: {FILE_PATH}")
        wb = excel.Workbooks.Open(FILE_PATH)
        
        if wb:
            print(f"Opened: {wb.Name}")
            ws = wb.Sheets("客户不要猜")
            
            # 1. Find Mr. Liu (Row 12)
            target_row = 12
            print(f"Target: Mr. Liu at Row {target_row}")
            
            # 2. Find Today's Date Column
            # Start checking from Column 20 (T) to 30
            target_col = None
            found_cols = []
            
            for col in range(20, 31):
                val = ws.Cells(11, col).Value
                # Check for date string or object
                is_today = False
                if val:
                    if isinstance(val, date) and val == TODAY:
                        is_today = True
                    elif str(val) == str(TODAY):
                        is_today = True
                    elif str(TODAY) in str(val): # e.g. "2026-04-11" in "2026-04-11 12:00"
                        is_today = True
                
                if is_today:
                    target_col = col
                    print(f"Found Today ({TODAY}) at Column {col}")
                    break
                else:
                    found_cols.append(f"Col {col}: {val}")

            if target_col:
                # Content to write
                content = "解读：客户对品质要求极高，为保品质可妥协面积至 160 平，但 120 平为底线不可推。对低价房敏感（疑有硬伤），谈判锚点 1600 万（含车位）。"
                
                print(f"Writing to Cell({target_row}, {target_col})...")
                ws.Cells(target_row, target_col).Value = content
                
                # Also update the Insight in Q12 as requested previously (just in case)
                insight = "[S5:对比犹豫][C5:家人决策][B14:问底价][B6:看多不决] | 【动态洞察】曾看 179 平嫌贵，后看中 163 平（品质妥协底线），123 平绝对不行。对低价房敏感，怀疑有硬伤。谈判锚点在 1600 万。"
                ws.Cells(target_row, 17).Value = insight
                
                wb.Save()
                print("SUCCESS: Updated Followup & Insight.")
            else:
                print(f"ERROR: Did not find column for Today ({TODAY}).")
                print("Columns found:")
                for c in found_cols:
                    print(c)
        else:
            print("ERROR: Workbook is None")
            
        wb.Close(False)
        excel.Quit()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    save_all_workbooks()
    write_followup()
