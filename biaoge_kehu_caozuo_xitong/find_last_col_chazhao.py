# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
import sys
import time
import subprocess
import win32com.client

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 1. SAVE ALL OPEN WORKBOOKS (don't kill Excel)
print("1. Saving all open Excel workbooks...")
try:
    excel = win32com.client.GetActiveObject("Excel.Application")
    for w in excel.Workbooks:
        if not w.Saved:
            print(f"   Saving: {w.Name}")
            w.Save()
    print("   All workbooks saved.")
except:
    pass  # Excel not running

# 2. OPEN THE CORRECT FILE
FILE_PATH = r"C:\Users\Huawei\.openclaw\workspace-tuantuan\biaoge_kehu_caozuo_xitong\daily_followup.xlsm"
print(f"2. Opening: {FILE_PATH}")

try:
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = excel.Workbooks.Open(FILE_PATH)
    ws = wb.Sheets("客户不要猜")
    
    print("3. Checking Liu's Row (Row 12) for the LAST used column...")
    
    # Check the very last used column in Row 12
    last_col_idx = ws.Cells(12, 256).End(-4159).Column  # -4159 is xlToLeft
    last_val = ws.Cells(12, last_col_idx).Value
    header_val = ws.Cells(11, last_col_idx).Value
    
    print(f"\n--> FOUND LAST ENTRY at Column {last_col_idx}")
    print(f"    Date Header: {header_val}")
    print(f"    Content: {str(last_val)[:50]}...")

    # Also check if there is a column for Today (2026-04-11)
    found_today = False
    for col in range(last_col_idx - 5, last_col_idx + 5): # Scan around the end
        h = ws.Cells(11, col).Value
        if h and ("2026-04-11" in str(h) or "2026/4/11" in str(h) or "2026/04/11" in str(h)):
            print(f"\n--> FOUND TODAY'S COLUMN at Col {col}!")
            found_today = True
            
    if not found_today:
        print(f"\n--> WARNING: Today's (2026-04-11) column not found near the end.")
        print(f"    Last date header was: {header_val}")

    wb.Close(False)
    excel.Quit()
    print("\nDone.")
    
except Exception as e:
    print(f"Error: {e}")
