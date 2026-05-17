# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
"""
房源抓取监控器 - 每 2 分钟汇报进度，检测死循环
"""
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# 脚本所在目录（工作区 tools）
SCRIPT_DIR = Path(__file__).resolve().parent
LOG_FILE = SCRIPT_DIR / "_house_grab_logs" / "house_grab.log"
STATUS_FILE = SCRIPT_DIR / "_house_grab_runtime" / "grab_status.txt"

def get_last_district():
    """获取最后完成的区域"""
    if not LOG_FILE.exists():
        return None, 0
    
    lines = LOG_FILE.read_text(encoding='utf-8', errors='replace').splitlines()
    completed = []
    
    for line in reversed(lines[-200:]):
        if '区完成' in line and '保留' in line:
            # 提取区域名和套数
            try:
                parts = line.split('[')
                if len(parts) >= 2:
                    ts = parts[1].split(']')[0] if ']' in parts[1] else ''
                    if '完成' in line:
                        # 提取套数
                        import re
                        match = re.search(r'保留 (\d+) 套', line)
                        count = int(match.group(1)) if match else 0
                        # 提取区名
                        match2 = re.search(r'开始处理 (\S+) 区', line)
                        if not match2:
                            # 从上一行找
                            for prev in lines[-200:]:
                                if '开始处理' in prev and '区' in prev:
                                    match2 = re.search(r'开始处理 (\S+) 区', prev)
                                    break
                        
                        district = match2.group(1) if match2 else '未知'
                        completed.append((district, count, ts))
                        if len(completed) >= 10:
                            break
            except:
                pass
    
    return completed

def monitor():
    print("=" * 70)
    print("房源抓取监控器")
    print("=" * 70)
    print(f"启动时间：{datetime.now().strftime('%H:%M:%S')}")
    print()
    
    last_update = ""
    start_time = time.time()
    
    while True:
        elapsed = (time.time() - start_time) / 60
        
        # 每 2 分钟汇报一次
        completed = get_last_district()
        if completed:
            total = sum(c[1] for c in completed)
            districts = ", ".join([f"{c[0]}({c[1]}套)" for c in completed])
            current = f"{len(completed)}区/{total}套：{districts}"
            
            if current != last_update:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 进度：{current}")
                last_update = current
        
        # 检测超时（超过 40 分钟）
        if elapsed > 40:
            print(f"\n⚠️ 警告：已运行 {elapsed:.0f} 分钟，可能卡死")
        
        time.sleep(120)

if __name__ == '__main__':
    monitor()
