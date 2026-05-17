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
    
    print("3. Writing Mr. Liu's Followup & Tags...")
    
    # Mr. Liu is at Row 12
    row_liu = 12
    
    # A. Update Tags in Column Q (17)
    print("   - Updating Column Q (Tags)...")
    tag_content = "[S5:对比犹豫][C5:家人决策][B14:问底价][B6:看多不决] | 【动态洞察】曾看 179 平嫌贵，后看中 163 平（品质妥协底线），123 平绝对不行。对低价房敏感，怀疑有硬伤。谈判锚点在 1600 万。"
    ws.Cells(row_liu, 17).Value = tag_content
    print("     Done.")

    # B. Write Followup for Today (2026-04-11)
    # We know Yesterday (4/10) was Col 366. So Today should be Col 367.
    # Let's verify or find it.
    
    target_col = 367 # Based on yesterday being 366
    header_val = ws.Cells(11, target_col).Value
    
    # Just in case, search for today's date nearby
    found_col = None
    for c in range(360, 380):
        h = ws.Cells(11, c).Value
        if h and ("2026-04-11" in str(h) or "2026/4/11" in str(h)):
            found_col = c
            break
            
    if found_col:
        target_col = found_col
        print(f"   - Found Today's Column: {target_col}")
    else:
        # If not found, maybe we need to create it? 
        # But usually TuanTuan creates it. Let's assume 367 is correct or the next empty one.
        # Check if 367 is empty
        if ws.Cells(row_liu, 367).Value is None:
            target_col = 367
            # Set header if empty?
            if ws.Cells(11, 367).Value is None:
                ws.Cells(11, 367).Value = "2026-04-11"
            print(f"   - Using Col 367 (Assuming Today)")
        else:
            # Find next empty
            for c in range(367, 400):
                if ws.Cells(row_liu, c).Value is None:
                    target_col = c
                    if ws.Cells(11, c).Value is None:
                        ws.Cells(11, c).Value = "2026-04-11"
                    break
            print(f"   - Using next available Col {target_col}")

    # Write Content
    followup_content = "解读：曾看 179 平嫌贵，后看中 163 平（品质妥协底线），123 平绝对不行。对低价房敏感，怀疑有硬伤。谈判锚点在 1600 万。"
    ws.Cells(row_liu, target_col).Value = followup_content
    print(f"   - Wrote Followup to Col {target_col}")
    print(f"   - Content: {followup_content}")

    wb.Save()
    print("\n4. SUCCESS! Saved.")
    wb.Close(False)
    excel.Quit()
    print("Done.")
    
except Exception as e:
    print(f"Error: {e}")
