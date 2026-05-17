# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
import sys
import os
import time
import subprocess
import win32com.client

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 1. KILL EXCEL
print("1. Killing Excel to release lock...")
try:
    subprocess.run(["taskkill", "/F", "/IM", "EXCEL.EXE"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
except:
    pass

# 2. OPEN THE CORRECT FILE
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
file_path = os.path.join(parent_dir, "daily_followup.xlsm")

print(f"2. Opening: {file_path}")

try:
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    
    wb = excel.Workbooks.Open(file_path)
    ws = wb.Sheets("客户不要猜")
    
    print("3. Checking Row 12 (Liu) and Row 13 (Next person) for data...")
    
    # Check Row 12 (Liu)
    liu_empty = True
    for col in range(20, 100):
        val = ws.Cells(12, col).Value
        if val and len(str(val).strip()) > 2:
            liu_empty = False
            header = ws.Cells(11, col).Value
            print(f"   [Row 12 Liu] Col {col} (Header: {header}): {str(val)[:30]}")
    
    if liu_empty:
        print("   [Row 12 Liu] EMPTY after Col 20!")

    # Check Row 13 (Next person) to see if anyone has data
    next_empty = True
    for col in range(20, 100):
        val = ws.Cells(13, col).Value
        if val and len(str(val).strip()) > 2:
            next_empty = False
            header = ws.Cells(11, col).Value
            print(f"   [Row 13 Next] Col {col} (Header: {header}): {str(val)[:30]}")

    if next_empty:
        print("   [Row 13 Next] EMPTY after Col 20!")
        
    # Check the last used column of the sheet to see max usage
    last_col = ws.Cells(12, ws.Columns.Count).End(-4159).Column
    print(f"\n   Max used column in Row 12 is: {last_col}")
    
    wb.Close(False)
    excel.Quit()
    print("\nDone.")
    
except Exception as e:
    print(f"Error: {e}")
