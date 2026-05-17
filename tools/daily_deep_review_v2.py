#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日跟进深度复盘脚本 v3 (修复 API Key 和列索引)
"""
import win32com.client
import pythoncom
import requests
import json
import re
import time
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', write_through=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', write_through=True)

# 导入主脚本的配置（获取真实的 API Key）
sys.path.insert(0, r"C:\Users\Huawei\.openclaw\workspace-tuantuan\tools")
from daily_follow_plan_v2_jihua import BAILIAN_API_KEY, BAILIAN_API_URL, TELEGRAM_BOT_TOKEN as TG_TOKEN, TELEGRAM_CHAT_ID as TG_CHAT_ID, CLIENT_SHEET_INDEX, COL_NAME, COL_GRADE, COL_NEED

BAILIAN_MODEL = "qwen3.6-plus"
EXCEL_PATH = r"D:\Unique work form\daily_followup.xlsm"
PASSWORD="000"

from datetime import datetime

pythoncom.CoInitialize()

def send_tg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text})
    except:
        pass

def log(msg):
    print(msg)
    if any(kw in msg for kw in ["启动", "完成", "生成", "失败", "发现"]):
        send_tg(msg)

def read_excel():
    log("📂 正在打开 Excel...")
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.DisplayAlerts = False
        wb = excel.Workbooks.Open(EXCEL_PATH, UpdateLinks=0, ReadOnly=True, Password=PASSWORD)
        ws = wb.Sheets(CLIENT_SHEET_INDEX)
        log("✅ Excel 打开成功")
    except Exception as e:
        log(f"❌ 打开 Excel 失败: {e}")
        return []

    today_str = datetime.now().strftime("%Y-%m-%d")
    clients_with_followup = []

    log("🔍 正在扫描今日跟进记录...")
    for row in range(12, 2000):
        try:
            # 查找今天的跟进列
            date_col = None
            content_col = None
            
            # 扫描表头
            for c in range(1, 1000):
                val = ws.Cells(11, c).Value
                if val and today_str in str(val):
                    date_col = c
                    content_col = c
                    break
            
            if date_col:
                name = ws.Cells(row, COL_NAME).Value
                if not name: continue
                
                content = ws.Cells(row, content_col).Value
                if content:
                     grade = ws.Cells(row, COL_GRADE).Value
                     demand = ws.Cells(row, COL_NEED).Value
                     
                     clients_with_followup.append({
                         "name": str(name),
                         "grade": str(grade) if grade else "",
                         "demand": str(demand) if demand else "",
                         "content": str(content)
                     })
        except:
            continue

    wb.Close(False)
    excel.Quit()
    return clients_with_followup

def call_ai(client):
    prompt = f"""
你是一名上海二手房销售总监。请点评以下客户的跟进。
客户：{client['name']} ({client['grade']}级)
需求：{client['demand']}
今日跟进：{client['content']}
请输出 JSON：{{"score": 0-100, "comment": "...", "insight": "...", "next_action": "..."}}
"""
    try:
        resp = requests.post(BAILIAN_API_URL, json={
            "model": BAILIAN_MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }, headers={"Authorization": f"Bearer {BAILIAN_API_KEY}", "Content-Type": "application/json"}, timeout=120)
        res = resp.json()
        content = res["choices"][0]["message"]["content"]
        return json.loads(re.sub(r'```json|```', '', content).strip())
    except Exception as e:
        return {"score": 0, "comment": f"Error: {e}", "insight": "", "next_action": ""}

def main():
    log("🚀 深度复盘脚本启动...")
    clients = read_excel()
    
    if not clients:
        log("⚠️ 未找到今日跟进记录。")
        return

    log(f"🔍 发现 {len(clients)} 个跟进记录，开始分析...")
    html = "<html><head><style>body{font-family:sans-serif;padding:20px} .card{border:1px solid #ddd; padding:15px; margin-bottom:15px; border-radius:8px}</style></head><body>"
    
    for i, c in enumerate(clients):
        log(f"⏳ 分析 {i+1}/{len(clients)}: {c['name']}")
        res = call_ai(c)
        score = res.get("score", 0)
        color = "#d4edda" if score >= 80 else "#fff3cd" if score >= 60 else "#f8d7da"
        
        html += f"""
        <div class="card" style="background:{color}">
            <h3>{c['name']} ({c['grade']}级) - 得分: {score}</h3>
            <p><b>今日动作：</b>{c['content']}</p>
            <p><b>AI 点评：</b>{res.get('comment')}</p>
            <p><b>洞察：</b>{res.get('insight')}</p>
            <p><b>建议：</b>{res.get('next_action')}</p>
        </div>
        """
        time.sleep(5) # Cooldown

    html += "</body></html>"
    
    report_path = os.path.expanduser("~/Desktop/daily_review_report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    log(f"📄 报告已生成：{report_path}")
    send_tg("📄 报告已生成，请查看桌面文件。")

if __name__ == "__main__":
    main()