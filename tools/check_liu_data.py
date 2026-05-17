# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！

# -*- coding: utf-8 -*-
import sys
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

# 2. OPEN FILE
FILE_PATH = r"C:\Users\Huawei\.openclaw\workspace-tuantuan\biaoge_kehu_caozuo_xitong\biaoge_kehu_caozuo_xitong\biaoge_kehu_caozuo_xitong\daily_followup.xlsm"
print(f"2. Opening: {FILE_PATH}")

try:
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = excel.Workbooks.Open(FILE_PATH)
    ws = wb.Sheets("客户不要猜")
    
    print("3. Checking Liu's Row (Row 12) for recent entries...")
    
    # Scan from Col 20 to 60 to find where the data ends
    last_entry_col = None
    last_entry_val = None
    
    for col in range(20, 61):
        val = ws.Cells(12, col).Value
        if val and len(str(val).strip()) > 0:
            last_entry_col = col
            last_entry_val = str(val)
            # Also check the date header in Row 11 for this col
            header = ws.Cells(11, col).Value
            print(f"   Col {col} (Header: {header}): {last_entry_val[:50]}...")

    if last_entry_col:
        print(f"\n-> Found latest entry at Col {last_entry_col}: {last_entry_val[:100]}")
        if ws.Cells(11, last_entry_col).Value:
            print(f"   -> Date Header: {ws.Cells(11, last_entry_col).Value}")
    else:
        print("-> No entries found after Col 20.")
            
    wb.Close(False)
    excel.Quit()
    print("\nDone.")
    
except Exception as e:
    print(f"Error: {e}")
