# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！

# -*- coding: utf-8 -*-
"""
经验库管理 - 主表格 Experience Sheet
"""
import win32com.client
import sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

EXCEL_PATH = r'D:\ExcelData\daily_followup.xlsm'
PASSWORD = "000"

def get_ws():
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = excel.Workbooks.Open(EXCEL_PATH, Password=PASSWORD)
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
    print(f"=== 经验库查询 ===\n条件：S={filterS or '任意'} | C={filterC or '任意'} | B={filterB or '任意'} | 关键词={keyword or '无'}\n")
    found = 0
    for row in range(2, ws.UsedRange.Rows.Count + 1):
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
    if found == 0:
        print("❌ 没有找到匹配的经验")
    else:
        print(f"✅ 找到 {found} 条经验")
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
