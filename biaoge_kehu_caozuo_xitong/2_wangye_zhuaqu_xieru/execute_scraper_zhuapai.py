# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
"""
执行房源抓取 JS 脚本
"""
import requests
import json
import websocket
import time
import sys

DEBUG_PORT = 9222
SCRIPT_PATH = "D:\\OpenClaw\\Workspaces\\main\\tools\\house_scraper.js"

def get_ws_url():
    tabs = requests.get(f"http://localhost:{DEBUG_PORT}/json", timeout=3).json()
    for tab in tabs:
        if "house.link.lianjia.com" in tab.get("url", ""):
            return tab['webSocketDebuggerUrl']
    return None

def main():
    ws_url = get_ws_url()
    if not ws_url:
        print("[ERROR] 未找到链家页面")
        return 1
    
    print(f"[OK] 找到链家页面")
    
    # 读取 JS
    with open(SCRIPT_PATH, 'r', encoding='utf-8') as f:
        js_code = f.read()
    print(f"[OK] JS 脚本已加载 ({len(js_code)} 字节)")
    
    # 连接
    ws = websocket.create_connection(ws_url, timeout=120)
    ws.settimeout(60)
    print(f"[OK] WebSocket 已连接")
    
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
    print(f"[OK] 脚本已发送，开始抓取...")
    print(f"[INFO] 预计耗时 10-15 分钟，请在浏览器查看进度")
    
    start = time.time()
    while time.time() - start < 1200:  # 20 分钟超时
        try:
            msg = ws.recv()
            data = json.loads(msg)
            
            if data.get("method") == "Console.messageAdded":
                text = data.get("params", {}).get("message", {}).get("text", "")
                if "龙虾" in text:
                    print(f"  {text}")
                    sys.stdout.flush()
                
                if "抓取完成" in text or "🎉" in text:
                    print("\n[OK] 抓取完成！")
                    time.sleep(3)
                    
                    # 验证数据
                    cmd2 = {
                        "id": 2,
                        "method": "Runtime.evaluate",
                        "params": {
                            "expression": "window.LOBSTER_DATA ? window.LOBSTER_DATA.length : 0",
                            "returnByValue": True
                        }
                    }
                    ws.send(json.dumps(cmd2))
                    res = json.loads(ws.recv())
                    length = res.get('result', {}).get('value', 0)
                    print(f"[OK] 数据验证：{length} 字符")
                    ws.close()
                    
                    if length > 1000:
                        print("[✅] 成功！")
                        return 0
                    else:
                        print("[ERROR] 数据太短，可能失败")
                        return 1
            
        except websocket.WebSocketTimeoutException:
            elapsed = int(time.time() - start)
            if elapsed % 60 == 0:
                print(f"[...] 抓取中... ({elapsed//60} 分钟)")
            time.sleep(1)
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(1)
    
    ws.close()
    print("[ERROR] 超时")
    return 1

if __name__ == '__main__':
    sys.exit(main())
