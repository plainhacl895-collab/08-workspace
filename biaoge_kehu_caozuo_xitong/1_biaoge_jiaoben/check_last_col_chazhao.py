# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
import sys
import os
import time
import subprocess
import win32com.client

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 1. KILL EXCEL
print("1. Killing Excel...")
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
    
    print("3. Checking the VERY LAST used column in the whole sheet...")
    
    # Get the last cell in the used range
    last_row = ws.Cells(ws.Rows.Count, 1).End(-4162).Row # xlUp
    last_col = ws.Cells(12, ws.Columns.Count).End(-4159).Column # xlToLeft
    
    print(f"   Last Row with data (Col 1): {last_row}")
    print(f"   Last Column with data (Row 12): {last_col}")
    
    # Check the value at the very last used column in Row 12
    val = ws.Cells(12, last_col).Value
    header = ws.Cells(11, last_col).Value
    
    print(f"\n--> LATEST ENTRY in Row 12:")
    print(f"    Col: {last_col}")
    print(f"    Date Header (Row 11): {header}")
    print(f"    Content: {str(val)[:100]}...")
    
    # Check if there are any dates in 2026
    found_2026 = False
    # Scan a wide range around the end just in case
    for c in range(max(20, last_col - 10), last_col + 5):
        h = ws.Cells(11, c).Value
        if h and "2026" in str(h):
            print(f"    -> Found 2026 Date at Col {c}: {h}")
            found_2026 = True
            
    if not found_2026:
        print(f"    -> WARNING: No 2026 dates found near the end. Last header was: {header}")

    wb.Close(False)
    excel.Quit()
    print("\nDone.")
    
except Exception as e:
    print(f"Error: {e}")
