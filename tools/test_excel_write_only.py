import win32com.client
import time
import os

EXCEL_PATH = r"D:\Unique work form\daily_followup.xlsm"
PASSWORD = "your_password" 
CLIENT_SHEET_INDEX = 2

def test_write():
    os.system('taskkill /F /IM EXCEL.EXE 2>nul')
    time.sleep(4)

    pythoncom = __import__('pythoncom')
    pythoncom.CoInitialize()
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = True
    excel.DisplayAlerts = False
    excel.Interactive = False

    try:
        wb = excel.Workbooks.Open(EXCEL_PATH, UpdateLinks=0, ReadOnly=False, Password=PASSWORD)
        ws = wb.Worksheets(CLIENT_SHEET_INDEX)
        
        header_row = 11
        suggestion_col = None
        
        for c in range(1, 50):
            val = ws.Cells(header_row, c).Value
            if val and "建议" in str(val):
                suggestion_col = c
                print(f"[OK] 找到建议列: 第 {c} 列 ({val})")
                break
        
        if not suggestion_col:
            print("[!] 未找到建议列，默认用第 20 列")
            suggestion_col = 20

        target_col = suggestion_col + 1
        ws.Cells(header_row, target_col).Value = "2026-04-25 检查"
        print(f"[OK] 表头已写入: 第 {target_col} 列")

        test_count = 0
        for row in range(12, 50):
            name = ws.Cells(row, 9).Value
            if name and str(name).strip():
                content = f"降级: 意向消失 (负面) | 点评: 话术生硬 | 建议: 发短信试探"
                ws.Cells(row, target_col).Value = content
                print(f"  -> 写入第 {row} 行 ({name.strip()})")
                test_count += 1
                if test_count >= 3: break
        
        wb.Save()
        print(f"\n[OK] 成功写入 {test_count} 行。请检查 Excel。")

    except Exception as e:
        print(f"[X] 失败: {e}")
        import traceback; traceback.print_exc()
    finally:
        try:
            wb.Close(SaveChanges=True)
            excel.Quit()
        except: pass
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    test_write()
