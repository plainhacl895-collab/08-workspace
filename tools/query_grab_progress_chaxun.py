# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询房源抓取进度
"""

import sys
import io
import json
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 脚本所在目录（工作区 tools）
SCRIPT_DIR = Path(__file__).resolve().parent
PROGRESS_FILE = SCRIPT_DIR / "_house_grab_runtime" / "grab_progress.json"
TASK_STATE_FILE = SCRIPT_DIR / "_house_grab_runtime" / "grab_task_state.json"
LOG_FILE = SCRIPT_DIR / "_house_grab_logs" / "house_grab.log"

def query_progress():
    if not PROGRESS_FILE.exists():
        print("❌ 未找到进度文件，可能没有正在运行的抓取任务")
        return
    
    progress = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    
    print("=" * 60)
    print("📊 房源抓取进度")
    print("=" * 60)
    print(f"任务 ID: {progress.get('task_id', 'N/A')}")
    print(f"状态：{progress.get('status', 'unknown')}")
    print(f"当前阶段：{progress.get('current_phase', 'N/A')}")
    print(f"进度：{progress.get('progress_percent', 0)}%")
    print(f"已抓取：{progress.get('total_collected', 0)} 套")
    print(f"已完成区域：{len(progress.get('districts_completed', []))} 个")
    print(f"抓取中区域：{len(progress.get('districts_running', []))} 个")
    
    if progress.get('districts_running'):
        for d in progress['districts_running']:
            print(f"  - {d}")
    
    started = progress.get('started_at', '')
    if started:
        elapsed = datetime.now() - datetime.fromisoformat(started)
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"已用时间：{hours}小时{minutes}分钟{seconds}秒")
    
    print(f"错误数：{progress.get('errors_count', 0)}")
    print("=" * 60)

if __name__ == "__main__":
    query_progress()
