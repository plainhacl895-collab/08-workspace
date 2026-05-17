#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
房源抓取守护进程 - 自动监控、自动重试、自动汇报
"""

import subprocess
import sys
import time
import json
from datetime import datetime
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
RUNTIME_DIR = TOOLS_DIR / "_house_grab_runtime"
LOG_DIR = TOOLS_DIR / "_house_grab_logs"
LAST_RESULT = RUNTIME_DIR / "last_run_result.json"

MAX_RETRIES = 3
CHECK_INTERVAL = 60  # 每 60 秒检查一次


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def send_telegram(message):
    """发送 Telegram 消息"""
    try:
        import urllib.parse
        import urllib.request
        chat_id = "8724466632"
        bot_token = "8705450288:AAExGrG5ZIKt3wUnoAZ2Bll4W2StzDVCOYY"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=5)
        log("✅ Telegram 通知已发送")
    except Exception as e:
        log(f"⚠️ Telegram 发送失败：{e}")


def check_grab_status():
    """检查抓取状态"""
    if not LAST_RESULT.exists():
        return {"status": "no_result"}
    
    try:
        result = json.loads(LAST_RESULT.read_text(encoding="utf-8"))
        return result
    except:
        return {"status": "error"}


def run_grab():
    """执行抓取"""
    log("🚀 开始执行房源抓取...")
    
    try:
        proc = subprocess.run(
            ["cmd", "/c", "RUN_HOUSE_GRAB.cmd"],
            cwd=str(TOOLS_DIR),
            capture_output=False,
            timeout=3600  # 60 分钟超时
        )
        
        if proc.returncode == 0:
            log("✅ 抓取成功完成！")
            return True
        else:
            log(f"❌ 抓取失败，返回码：{proc.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        log("❌ 抓取超时（60 分钟）")
        return False
    except Exception as e:
        log(f"❌ 抓取异常：{e}")
        return False


def main():
    log("=" * 60)
    log("🏠 房源抓取守护进程启动")
    log("=" * 60)
    
    # 发送开始通知
    send_telegram("🏠 <b>房源抓取守护进程已启动</b>\n\n⏰ 时间：" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n📝 将自动监控抓取进度，失败自动重试")
    
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        log(f"\n📊 第 {retry_count + 1}/{MAX_RETRIES} 次尝试")
        
        # 执行抓取
        success = run_grab()
        
        if success:
            # 检查是否成功写入
            result = check_grab_status()
            if result.get("success") and result.get("data_count", 0) > 0:
                count = result["data_count"]
                log(f"\n✅ 抓取并写入完成！共 {count} 套房源")
                send_telegram(f"🎉 <b>房源抓取完成！</b>\n\n📊 总计：<b>{count}</b> 套\n✅ 已写入 Excel 表格\n⏰ 完成时间：" + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                return 0
            else:
                log("⚠️ 抓取完成但写入可能失败，准备重试")
        else:
            log("⚠️ 抓取失败，准备重试")
        
        retry_count += 1
        
        if retry_count < MAX_RETRIES:
            wait_minutes = 2
            log(f"⏱️  {wait_minutes} 分钟后重试...")
            send_telegram(f"⚠️ <b>抓取失败，{wait_minutes} 分钟后重试</b>\n\n尝试次数：{retry_count}/{MAX_RETRIES}")
            time.sleep(wait_minutes * 60)
    
    # 所有重试都失败
    log("\n❌ 所有重试都失败了")
    send_telegram("❌ <b>房源抓取失败</b>\n\n⚠️ 已重试 {MAX_RETRIES} 次\n📝 请检查日志：{LOG_DIR}/house_grab.log")
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
