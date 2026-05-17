# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
"""
经验库管理 - 主表格 Experience Sheet
带进度汇报，避免卡死错觉
"""
import win32com.client
import sys
import time
import subprocess
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

def kill_excel_processes():
    """先保存所有打开的 Excel 文件，再清理进程，避免 COM 连接失败"""
    import pythoncom
    try:
        # 先尝试保存所有打开的 Excel 文件
        excel = None
        pythoncom.CoInitialize()
        try:
            excel = win32com.client.Dispatch("Excel.Application")
            saved_count = 0
            for wb in excel.Workbooks:
                if not wb.Saved:
                    wb.Save()
                    saved_count += 1
            if saved_count > 0:
                print(f"已自动保存 {saved_count} 个 Excel 文件")
            excel.Quit()
            time.sleep(2)  # 等待 Excel 完全退出
        except:
            pass  # 如果 Excel 未运行，忽略
        finally:
            if excel:
                try:
                    excel.Quit()
                except:
                    pass
    finally:
        pythoncom.CoUninitialize()
    
    # 强制杀掉残留的 Excel 进程
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'excel.exe'], 
                      capture_output=True, timeout=5)
        subprocess.run(['taskkill', '/F', '/IM', 'dllhost.exe'], 
                      capture_output=True, timeout=5)
        time.sleep(1)  # 等待进程完全释放
    except:
        pass  # 如果没有进程可杀，忽略错误

EXCEL_PATH = r'D:\ExcelData\daily_followup.xlsm'
PASSWORD = "000"

def get_ws():
    # 先清理卡住的 Excel 进程
    kill_excel_processes()
    
    print(f"[0:00] 📊 正在连接 Excel...")
    sys.stdout.flush()
    start = time.time()
    
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = excel.Workbooks.Open(EXCEL_PATH, Password=PASSWORD)
    
    elapsed = int(time.time() - start)
    print(f"[0:{elapsed:02d}] ✅ Excel 已打开")
    sys.stdout.flush()
    
    ws = None
    for i in range(1, wb.Worksheets.Count + 1):
        if wb.Worksheets(i).Name == "Experience":
            ws = wb.Worksheets(i)
            break
    return excel, wb, ws

def add(content, stateS="", cardianC="", signalB=""):
    excel, wb, ws = get_ws()
    if ws is None:
        print("ERROR: Experience sheet not found")
        wb.Close(False)
        excel.Quit()
        return
    newRow = ws.UsedRange.Rows.Count + 1
    ws.Cells(newRow, 1).Value = newRow - 1
    ws.Cells(newRow, 2).Value = datetime.now().strftime("%Y-%m-%d")
    ws.Cells(newRow, 3).Value = content
    ws.Cells(newRow, 4).Value = stateS
    ws.Cells(newRow, 5).Value = cardianC
    ws.Cells(newRow, 6).Value = signalB
    wb.Save()
    wb.Close(True)
    excel.Quit()
    print(f"✅ 已写入第{newRow}行")
    print(f"内容：{content}")
    print(f"标签：S={stateS} | C={cardianC} | B={signalB}")

def query(filterS="", filterC="", filterB="", keyword=""):
    excel, wb, ws = get_ws()
    if ws is None:
        print("ERROR: Experience sheet not found")
        wb.Close(False)
        excel.Quit()
        return
    
    print(f"=== 经验库查询 ===")
    print(f"条件：S={filterS or '任意'} | C={filterC or '任意'} | B={filterB or '任意'} | 关键词={keyword or '无'}")
    print(f"[0:00] 🔍 开始扫描经验库...")
    sys.stdout.flush()
    
    start = time.time()
    found = 0
    total_rows = ws.UsedRange.Rows.Count
    last_report = 0
    
    for row in range(2, total_rows + 1):
        # 每 30 秒汇报进度
        elapsed = int(time.time() - start)
        if elapsed - last_report >= 30:
            percent = int((row / total_rows) * 100)
            print(f"[{elapsed//60}:{elapsed%60:02d}] ⏳ 已扫描 {row}/{total_rows} 行 ({percent}%)...")
            sys.stdout.flush()
            last_report = elapsed
        
        s = str(ws.Cells(row, 4).Value or "")
        c = str(ws.Cells(row, 5).Value or "")
        b = str(ws.Cells(row, 6).Value or "")
        content = str(ws.Cells(row, 3).Value or "")
        date = str(ws.Cells(row, 2).Value or "")
        match = True
        if filterS and s != filterS: match = False
        if filterC and c != filterC: match = False
        if filterB and b != filterB: match = False
        if keyword and keyword.lower() not in content.lower(): match = False
        if match:
            found += 1
            print(f"[{date}] S={s} | C={c} | B={b}\n  {content}\n")
    
    elapsed = int(time.time() - start)
    if found == 0:
        print(f"[{elapsed//60}:{elapsed%60:02d}] ❌ 没有找到匹配的经验")
    else:
        print(f"[{elapsed//60}:{elapsed%60:02d}] ✅ 找到 {found} 条经验")
    
    wb.Close(False)
    excel.Quit()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python experience.py add|query ...")
        print("  add: python experience.py add \"经验内容\" \"S5\" \"C5\" \"B4\"")
        print("  query: python experience.py query \"S5\" \"\" \"\" \"周末\"")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "add":
        add(sys.argv[2] if len(sys.argv) > 2 else "", sys.argv[3] if len(sys.argv) > 3 else "", sys.argv[4] if len(sys.argv) > 4 else "", sys.argv[5] if len(sys.argv) > 5 else "")
    elif cmd == "query":
        query(sys.argv[2] if len(sys.argv) > 2 else "", sys.argv[3] if len(sys.argv) > 3 else "", sys.argv[4] if len(sys.argv) > 4 else "", " ".join(sys.argv[5:]) if len(sys.argv) > 5 else "")
