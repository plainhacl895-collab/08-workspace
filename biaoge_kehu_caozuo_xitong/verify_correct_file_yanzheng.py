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
    
    # 3. SCAN ROW 11 FOR DATES
    print("3. Scanning Row 11 for dates...")
    found_cols = {}
    
    # Check columns 20 to 40
    for col in range(20, 45):
        val = ws.Cells(11, col).Value
        if val:
            # Store for output
            found_cols[col] = str(val)
            
            # Check for Yesterday (2026-04-10)
            if "2026-04-10" in str(val) or "2026/4/10" in str(val) or "2026/04/10" in str(val):
                print(f"   *** FOUND YESTERDAY (2026-04-10) at Column {col}! Value: {val}")
            
            # Check for Today (2026-04-11)
            if "2026-04-11" in str(val) or "2026/4/11" in str(val) or "2026/04/11" in str(val):
                print(f"   *** FOUND TODAY (2026-04-11) at Column {col}! Value: {val}")

    # Print last few found dates to verify context
    print("\n4. Last few date columns found:")
    keys = sorted(found_cols.keys(), reverse=True)
    for k in keys[:5]: # Print last 5
        print(f"   Col {k}: {found_cols[k]}")
            
    wb.Close(False)
    excel.Quit()
    print("\nDone.")
    
except Exception as e:
    print(f"Error: {e}")
