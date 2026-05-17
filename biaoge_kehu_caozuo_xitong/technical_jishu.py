# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
"""
技术操作经验库管理 - Technical Sheet
"""
import win32com.client
import sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

EXCEL_PATH = r'D:\Unique work form\daily_followup.xlsm'
PASSWORD = "000"

def get_ws():
    """获取 Technical Sheet"""
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = excel.Workbooks.Open(EXCEL_PATH, Password=PASSWORD)
    ws = None
    for i in range(1, wb.Worksheets.Count + 1):
        if wb.Worksheets(i).Name == "Technical":
            ws = wb.Worksheets(i)
            break
    return excel, wb, ws

def add(scene, t_label, command, notes="", success=""):
    """添加技术操作经验"""
    excel, wb, ws = get_ws()
    if ws is None:
        print("❌ Technical Sheet 不存在，请先在 Excel 中创建 'Technical' 工作表")
        wb.Close(False)
        excel.Quit()
        return
    
    newRow = ws.UsedRange.Rows.Count + 1
    
    # A 列：序号
    ws.Cells(newRow, 1).Value = newRow - 1
    # B 列：日期
    ws.Cells(newRow, 2).Value = datetime.now().strftime("%Y-%m-%d")
    # C 列：场景
    ws.Cells(newRow, 3).Value = scene
    # D 列：T 标签
    ws.Cells(newRow, 4).Value = t_label
    # E 列：命令
    ws.Cells(newRow, 5).Value = command
    # F 列：注意事项
    ws.Cells(newRow, 6).Value = notes
    # G 列：成功标志
    ws.Cells(newRow, 7).Value = success
    
    wb.Save()
    wb.Close(True)
    excel.Quit()
    
    print(f"✅ 已写入第{newRow}行")
    print(f"场景：{scene}")
    print(f"标签：{t_label}")
    print(f"命令：{command[:50]}..." if len(command) > 50 else f"命令：{command}")
    print(f"注意事项：{notes}")
    print(f"成功标志：{success}")

def query(filterT="", keyword=""):
    """查询技术操作经验"""
    excel, wb, ws = get_ws()
    if ws is None:
        print("❌ Technical Sheet 不存在")
        wb.Close(False)
        excel.Quit()
        return
    
    print(f"=== 技术操作经验库查询 ===")
    print(f"条件：T 标签={filterT or '任意'} | 关键词={keyword or '无'}\n")
    
    found = 0
    for row in range(2, ws.UsedRange.Rows.Count + 1):
        t = str(ws.Cells(row, 4).Value or "")
        scene = str(ws.Cells(row, 3).Value or "")
        command = str(ws.Cells(row, 5).Value or "")
        notes = str(ws.Cells(row, 6).Value or "")
        success = str(ws.Cells(row, 7).Value or "")
        date = str(ws.Cells(row, 2).Value or "")
        
        match = True
        if filterT and t != filterT: match = False
        if keyword:
            search_text = f"{scene} {command} {notes}".lower()
            if keyword.lower() not in search_text: match = False
        
        if match:
            found += 1
            print(f"[{date}] T={t}")
            print(f"  场景：{scene}")
            print(f"  命令：{command[:80]}..." if len(command) > 80 else f"  命令：{command}")
            print(f"  注意事项：{notes}")
            print(f"  成功标志：{success}\n")
    
    if found == 0:
        print("❌ 没有找到匹配的经验")
    else:
        print(f"✅ 找到 {found} 条经验")
    
    wb.Close(False)
    excel.Quit()

def init():
    """初始化 Technical Sheet（创建表头）"""
    excel, wb, ws = get_ws()
    if ws is None:
        print("❌ Technical Sheet 不存在，请先在 Excel 中创建 'Technical' 工作表")
        wb.Close(False)
        excel.Quit()
        return
    
    # 创建表头
    headers = ["序号", "日期", "场景", "T 标签", "命令", "注意事项", "成功标志"]
    for col, header in enumerate(headers, 1):
        ws.Cells(1, col).Value = header
    
    # 设置表头样式（加粗）
    ws.Range(ws.Cells(1, 1), ws.Cells(1, len(headers))).Font.Bold = True
    
    wb.Save()
    wb.Close(True)
    excel.Quit()
    print("✅ Technical Sheet 表头已初始化")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python technical.py add|query|init")
        print("  add: python technical.py add \"场景\" \"T1\" \"命令\" \"注意事项\" \"成功标志\"")
        print("  query: python technical.py query \"T1\" \"查询客户\"")
        print("  query: python technical.py query \"\" \"写入\"")
        print("  init: python technical.py init (初始化表头)")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "add":
        add(
            sys.argv[2] if len(sys.argv) > 2 else "",
            sys.argv[3] if len(sys.argv) > 3 else "",
            sys.argv[4] if len(sys.argv) > 4 else "",
            sys.argv[5] if len(sys.argv) > 5 else "",
            sys.argv[6] if len(sys.argv) > 6 else ""
        )
    elif cmd == "query":
        query(
            sys.argv[2] if len(sys.argv) > 2 else "",
            " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        )
    elif cmd == "init":
        init()
    else:
        print(f"❌ 未知命令：{cmd}")
        sys.exit(1)
