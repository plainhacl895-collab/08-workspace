# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
房源抓取进度汇报脚本
每隔 30 秒读取日志，向用户汇报进度
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# 脚本所在目录（工作区 tools）
SCRIPT_DIR = Path(__file__).resolve().parent
LOG_FILE = SCRIPT_DIR / "_house_grab_logs" / "house_grab.log"
STATUS_FILE = SCRIPT_DIR / "_house_grab_runtime" / "grab_status.txt"

def parse_latest_progress(log_lines):
    """解析最新进度"""
    districts = {}
    total_collected = 0
    
    for line in log_lines[-100:]:
        if "区完成：" in line:
            # 提取已完成的区域
            try:
                district = line.split("区完成：")[0].split(" ")[-1]
                count_str = line.split("区完成：")[1].split("套")[0]
                count = int(count_str)
                districts[district] = {"status": "done", "count": count}
            except:
                pass
        elif "区进度：" in line and "status=running" in line:
            # 提取进行中的区域
            try:
                district = line.split("区进度：")[0].split(" ")[-1]
                count = int(line.split("collected=")[1].split(",")[0])
                page = int(line.split("page=")[1].split(",")[0])
                if district not in districts or districts[district].get("status") != "done":
                    districts[district] = {"status": "running", "count": count, "page": page}
            except:
                pass
    
    # 计算总数
    for info in districts.values():
        if info.get("status") == "done":
            total_collected += info.get("count", 0)
        else:
            total_collected = max(total_collected, info.get("count", 0))
    
    return districts, total_collected

def report_progress():
    """生成进度报告"""
    if not LOG_FILE.exists():
        return "❌ 日志文件不存在"
    
    log_lines = LOG_FILE.read_text(encoding='gbk', errors='ignore').splitlines()
    
    if not log_lines:
        return "❌ 日志文件为空"
    
    districts, total = parse_latest_progress(log_lines)
    
    # 生成报告
    report = []
    report.append(f"[房源抓取进度] {datetime.now().strftime('%H:%M:%S')}")
    report.append("=" * 50)
    
    done = [d for d, info in districts.items() if info.get("status") == "done"]
    running = [d for d, info in districts.items() if info.get("status") == "running"]
    
    if done:
        report.append("[已完成区域]")
        for d in done:
            report.append(f"  - {d}: {districts[d]['count']} 套")
    
    if running:
        report.append("[抓取中区域]")
        for d in running:
            info = districts[d]
            report.append(f"  - {d}: {info.get('count', 0)} 套（第{info.get('page', 0)}页）")
    
    report.append("=" * 50)
    report.append(f"[总计] {total} 套房源")
    
    if STATUS_FILE.exists():
        status = STATUS_FILE.read_text(encoding='utf-8', errors='ignore')
        report.append(f"[状态] {status.strip()}")
    
    return "\n".join(report)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    print(report_progress())
