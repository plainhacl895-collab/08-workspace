# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
"""
链家房源抓取 - 直接执行版
通过 CDP 执行 JS，数据保存到 window.LOBSTER_DATA
"""

import requests
import json
import time
import sys

DEBUG_PORT = 9222
SCRIPT_PATH = "D:\\OpenClaw\\Workspaces\\main\\tools\\house_scraper.js"

def get_ws_url():
    try:
        tabs = requests.get(f"http://localhost:{DEBUG_PORT}/json", timeout=3).json()
        for tab in tabs:
            if "house.link.lianjia.com" in tab.get("url", ""):
                return tab['webSocketDebuggerUrl']
    except:
        pass
    return None

def main():
    ws_url = get_ws_url()
    if not ws_url:
        print("[ERROR] 未找到链家页面")
        return 1
    
    print(f"[OK] WebSocket: {ws_url[:50]}...")
    
    # 读取 JS
    with open(SCRIPT_PATH, 'r', encoding='utf-8') as f:
        js_code = f.read()
    
    print(f"[OK] JS 脚本长度：{len(js_code)} 字节")
    print("[INFO] 请在浏览器控制台查看进度...")
    print("[INFO] 执行时间约 10-15 分钟")
    
    import websocket
    ws = websocket.create_connection(ws_url, timeout=120)
    ws.settimeout(300)
    
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
    
    # 监控
    start = time.time()
    while time.time() - start < 1200:
        try:
            msg = ws.recv()
            data = json.loads(msg)
            if data.get("method") == "Console.messageAdded":
                text = data.get("params", {}).get("message", {}).get("text", "")
                if "龙虾" in text:
                    print(f"  {text}")
                if "抓取完成" in text:
                    print("\n[OK] 抓取完成！")
                    # 验证数据
                    time.sleep(2)
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
                    print(f"[OK] 数据长度：{length} 字符")
                    ws.close()
                    return 0
        except Exception as e:
            if "timed out" in str(e):
                print(f"[...] 等待中... ({int(time.time()-start)}秒)")
            time.sleep(1)
    
    ws.close()
    print("[ERROR] 超时")
    return 1

if __name__ == '__main__':
    sys.exit(main())
