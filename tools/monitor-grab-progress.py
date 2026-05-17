# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
"""
房源抓取进度监控 - 每 30 秒读取状态并显示
"""
import time
from pathlib import Path
from datetime import datetime

# 脚本所在目录（工作区 tools）
SCRIPT_DIR = Path(__file__).resolve().parent
STATUS_FILE = SCRIPT_DIR / "_house_grab_runtime" / "grab_status.txt"
LOG_FILE = SCRIPT_DIR / "_house_grab_logs" / "house_grab.log"

def get_status():
    if not STATUS_FILE.exists():
        return "未开始"
    return STATUS_FILE.read_text(encoding='utf-8', errors='replace').strip()

def get_progress():
    if not LOG_FILE.exists():
        return []
    
    lines = LOG_FILE.read_text(encoding='utf-8', errors='replace').splitlines()
    progress = []
    
    for line in lines[-30:]:
        if '进度' in line or '完成' in line:
            # 提取时间戳和内容
            if ' [' in line:
                parts = line.split(' [', 1)
                if len(parts) == 2:
                    ts = parts[0]
                    content = '[' + parts[1]
                    progress.append(f"{ts[-8:]} {content[:100]}")
    
    return progress

print("=" * 70)
print("房源抓取进度监控（每 30 秒刷新）")
print("=" * 70)

last_status = ""
while True:
    status = get_status()
    progress = get_progress()
    
    if status != last_status:
        print(f"\n{datetime.now().strftime('%H:%M:%S')} 状态：{status}")
        last_status = status
    
    if progress:
        print(f"  最新进度：{progress[-1]}")
    
    time.sleep(30)
