# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！

# -*- coding: utf-8 -*-
import sys
import win32com.client
from datetime import date

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("Scanning Row 11 for dates...")
try:
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    
    FILE_PATH = r"C:\Users\huawei\OneDrive\daily_followup.xlsm"
    wb = excel.Workbooks.Open(FILE_PATH)
    ws = wb.Sheets("客户不要猜")
    
    TODAY = date(2026, 4, 11)
    
    # Scan Cols 20 (T) to 40
    found_today = False
    for col in range(20, 41):
        val = ws.Cells(11, col).Value
        if val:
            print(f"Col {col}: {val}")
            # Check date
            if isinstance(val, date):
                if val == TODAY:
                    print(f"  -> FOUND TODAY at Col {col}!")
                    found_today = True
            elif "2026-04-11" in str(val):
                print(f"  -> FOUND TODAY (string match) at Col {col}!")
                found_today = True

    if not found_today:
        print(f"Did not find column for {TODAY} in range 20-40.")
        
    wb.Close(False)
    excel.Quit()
    
except Exception as e:
    print(f"Error: {e}")
