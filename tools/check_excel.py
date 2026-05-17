# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！

# -*- coding: utf-8 -*-
import sys
import win32com.client

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("Starting Excel check...")
try:
    # Try to get running instance first
    try:
        excel = win32com.client.GetActiveObject("Excel.Application")
        print("Found running Excel.")
    except:
        print("No running Excel. Creating new one.")
        excel = win32com.client.Dispatch("Excel.Application")
    
    excel.Visible = False
    excel.DisplayAlerts = False
    
    # Open Workbook
    FILE_PATH = r"C:\Users\huawei\OneDrive\daily_followup.xlsm"
    print(f"Opening {FILE_PATH}...")
    wb = excel.Workbooks.Open(FILE_PATH)
    print(f"Opened {wb.Name}")
    
    # Read Row 11, Col 20 (T)
    ws = wb.Sheets("客户不要猜")
    val = ws.Cells(11, 20).Value
    print(f"Cell T11 value: {val}")
    
    wb.Close(False)
    # Don't quit if it was running? 
    # If we created it, we should quit. If we got it, maybe don't?
    # But `GetActiveObject` usually implies we should be careful.
    # Let's just quit for safety in this test.
    if wb: wb.Close(False)
    
    # Check how many workbooks are open
    if excel.Workbooks.Count == 0:
        excel.Quit()
        print("Excel closed.")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
