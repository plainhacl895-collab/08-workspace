# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
import sys
import os
import time
import subprocess

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import win32com.client

FILE_PATH = r"C:\Users\Huawei\.openclaw\workspace-tuantuan\biaoge_kehu_caozuo_xitong\daily_followup.xlsm"

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

def update_excel():
    try:
        print("Creating new Excel instance...")
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        print(f"Opening: {FILE_PATH}")
        wb = excel.Workbooks.Open(FILE_PATH)
        
        if wb:
            print(f"Opened: {wb.Name}")
            # Get sheet
            ws = wb.Sheets("客户不要猜")
            
            # Find Mr. Liu
            target_row = 12 # Known location
            print(f"Updating Row {target_row}...")
            
            content = "[S5:对比犹豫][C5:家人决策][B14:问底价][B6:看多不决] | 【动态洞察】曾看 179 平嫌贵，后看中 163 平（品质妥协底线），123 平绝对不行。对低价房敏感，怀疑有硬伤。谈判锚点在 1600 万。"
            ws.Cells(target_row, 17).Value = content
            
            wb.Save()
            print("SUCCESS: Updated.")
        else:
            print("ERROR: Workbook is None")
            
        wb.Close(False)
        excel.Quit()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    save_all_workbooks()
    update_excel()
