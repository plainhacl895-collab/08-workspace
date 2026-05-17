# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
"""
链家房源抓取 - 直接执行
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import json
import websocket
import time
import sys

DEBUG_PORT = 9222
SCRIPT_PATH = "D:\\OpenClaw\\Workspaces\\main\\tools\\house_scraper.js"

# 获取页面
tabs = requests.get(f"http://localhost:{DEBUG_PORT}/json", timeout=3).json()
ws_url = None
for tab in tabs:
    if "house.link.lianjia.com" in tab.get("url", ""):
        ws_url = tab['webSocketDebuggerUrl']
        break

if not ws_url:
    print("[ERROR] 未找到链家页面")
    sys.exit(1)

print("[OK] 找到链家页面")

# 读取 JS
with open(SCRIPT_PATH, 'r', encoding='utf-8') as f:
    js_code = f.read()

print(f"[OK] JS 已加载 ({len(js_code)//1024}KB)")

# 连接
ws = websocket.create_connection(ws_url, timeout=120)
ws.settimeout(60)

# 启用 Console API
ws.send(json.dumps({"id": 0, "method": "Console.enable"}))
ws.recv()

# 执行
cmd = {
    "id": 1,
    "method": "Runtime.evaluate",
    "params": {
        "expression": js_code,
        "awaitPromise": False
    }
}
ws.send(json.dumps(cmd))
print("[OK] 脚本已发送")
print("[INFO] 抓取中...（约 10-15 分钟）")

start = time.time()
last_progress = 0

while True:
    try:
        msg = ws.recv()
        data = json.loads(msg)
        
        if data.get("method") == "Console.messageAdded":
            text = data.get("params", {}).get("message", {}).get("text", "")
            
            if "龙虾" in text:
                print(f"  {text}")
                sys.stdout.flush()
            
            if "抓取完成" in text:
                print("\n[OK] 抓取完成！")
                time.sleep(2)
                
                # 获取数据
                cmd2 = {
                    "id": 2,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": "window.LOBSTER_DATA",
                        "returnByValue": True
                    }
                }
                ws.send(json.dumps(cmd2))
                res = json.loads(ws.recv())
                data_content = res.get('result', {}).get('value')
                
                if data_content and len(data_content) > 1000:
                    lines = data_content.split('\n')
                    print(f"[OK] 数据：{len(lines)} 行，{len(data_content)//1024}KB")
                    
                    # 保存到文件
                    with open("D:\\ExcelData\\properties_grabbed.txt", "w", encoding="utf-8") as f:
                        f.write(data_content)
                    print(f"[OK] 已保存到 D:\\ExcelData\\properties_grabbed.txt")
                    ws.close()
                    
                    # 写入 Excel
                    print("\n[Excel] 正在写入...")
                    import win32com.client
                    excel = win32com.client.DispatchEx('Excel.Application')
                    excel.Visible = False
                    excel.DisplayAlerts = False
                    
                    wb = excel.Workbooks.Open(r'D:\ExcelData\daily_followup.xlsm', Password="000")
                    sheet = wb.Worksheets('Sheet1')
                    
                    # 清空
                    sheet.Range("A4:K10000").ClearContents()
                    
                    # 写入
                    rows = data_content.split('\n')
                    count = 0
                    for i, row in enumerate(rows):
                        if i == 0:  # 跳过表头
                            continue
                        if not row.strip():
                            continue
                        cols = row.split('\t')
                        count += 1
                        for j, col in enumerate(cols, start=2):
                            if j <= 11:
                                if col.startswith('=HYPERLINK'):
                                    sheet.Cells(i + 3, j).Formula = col
                                else:
                                    sheet.Cells(i + 3, j).Value = col
                    
                    # 运行宏
                    try:
                        excel.Run("区域房龄刷新")
                        print("[Excel] 宏执行完成")
                    except Exception as e:
                        print(f"[警告] 宏失败：{e}")
                    
                    wb.Save()
                    wb.Close(True)
                    excel.Quit()
                    
                    print(f"\n[✅] 完成！写入 {count} 条数据到 Sheet1")
                    print(f"\n[[tts:房源抓取完成，共写入 Excel {count} 套房源]]")
                    sys.exit(0)
                else:
                    print("[ERROR] 数据异常")
                    ws.close()
                    sys.exit(1)
    
    except websocket.WebSocketTimeoutException:
        elapsed = int(time.time() - start)
        if elapsed % 60 == 0 and elapsed != last_progress:
            print(f"[...] {elapsed//60} 分钟")
            last_progress = elapsed
        time.sleep(1)
    except KeyboardInterrupt:
        print("\n[中断] 用户取消")
        ws.close()
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        time.sleep(1)
    
    if time.time() - start > 1800:  # 30 分钟超时
        print("[ERROR] 超时")
        ws.close()
        sys.exit(1)
