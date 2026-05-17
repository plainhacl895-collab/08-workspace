# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
import sys
import time
import subprocess
import win32com.client

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Save all open Excel workbooks first (don't kill other workbooks)
print("Saving all open Excel workbooks...")
try:
    excel = win32com.client.GetActiveObject("Excel.Application")
    for w in excel.Workbooks:
        if not w.Saved:
            print(f"  Saving: {w.Name}")
            w.Save()
    # Don't quit Excel, just save
    print("  All workbooks saved.")
except:
    pass  # Excel not running

def check_file(path):
    try:
        print(f"Checking: {path}")
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        try:
            wb = excel.Workbooks.Open(path)
        except Exception as e:
            print(f"Failed to open: {e}")
            excel.Quit()
            return

        ws = wb.Sheets("客户不要猜")
        
        print("Dates in Row 11 (Cols 20-30):")
        for col in range(20, 30):
            val = ws.Cells(11, col).Value
            if val:
                print(f"Col {col}: {val}")
            else:
                print(f"Col {col}: Empty")
        
        # Also check the user provided path if different
        # user_path = r"C:\Users\huawei\.openclaw\workspace\biaoge_kehu_caozuo_xitong\daily_followup.xlsm"
        # ...
        
        wb.Close(False)
        excel.Quit()
    except Exception as e:
        print(f"Error: {e}")

check_file(r"C:\Users\Huawei\.openclaw\workspace-tuantuan\biaoge_kehu_caozuo_xitong\daily_followup.xlsm")
