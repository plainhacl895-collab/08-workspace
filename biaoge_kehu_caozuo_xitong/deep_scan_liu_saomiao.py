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
    
    print("3. Scanning Liu's Row (Row 12) for ANY data after Col 20...")
    
    # Scan from Col 20 all the way to 200 to find where the data is
    found_entries = []
    
    for col in range(20, 201):
        val = ws.Cells(12, col).Value
        if val and len(str(val).strip()) > 2: # Skip tiny chars
            header = ws.Cells(11, col).Value
            entry_preview = str(val)[:50]
            print(f"   Col {col} (Header: {header}): {entry_preview}")
            found_entries.append((col, header, val))

    if found_entries:
        last_col, last_header, last_val = found_entries[-1]
        print(f"\n--> FOUND LATEST ENTRY at Col {last_col}:")
        print(f"    Date Header: {last_header}")
        print(f"    Content: {str(last_val)[:100]}...")
        
        # Verify the date of the latest entry
        if last_header:
            if "2026-04-10" in str(last_header) or "2026/4/10" in str(last_header):
                print("    -> MATCHES YESTERDAY!")
            elif "2026-04-11" in str(last_header) or "2026/4/11" in str(last_header):
                print("    -> MATCHES TODAY!")
    else:
        print("   No entries found after Col 20.")
            
    wb.Close(False)
    excel.Quit()
    print("\nDone.")
    
except Exception as e:
    print(f"Error: {e}")
