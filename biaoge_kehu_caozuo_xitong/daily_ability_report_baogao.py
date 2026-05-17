# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
"""
生成每日能力日报
用法：python daily_ability_report.py
输出：发送到 Telegram（通过 OpenClaw）
"""
import sys
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

LOG_FILE = r'D:\OpenClaw\Workspaces\keduoduo\memory\ability-changes.md'

def parse_today_section(content):
    """解析今天的内容"""
    today = datetime.now().strftime("%Y-%m-%d")
    today_section = f"## {today}"
    
    # 找到今天的部分
    start = content.find(today_section)
    if start == -1:
        return None, None, None
    
    # 找到下一个 ## 或文件末尾
    next_section = content.find('\n## ', start + 1)
    if next_section == -1:
        today_content = content[start:]
    else:
        today_content = content[start:next_section]
    
    # 解析三个部分
    adds = []
    updates = []
    suggestions = []
    
    in_section = None
    for line in today_content.split('\n'):
        if '### 新增能力' in line:
            in_section = 'adds'
        elif '### 更新能力' in line:
            in_section = 'updates'
        elif '### 待办/建议' in line:
            in_section = 'suggestions'
        elif line.startswith('- ') and in_section:
            item = line[2:].strip()
            if item:  # 跳过空行
                if in_section == 'adds':
                    adds.append(item)
                elif in_section == 'updates':
                    updates.append(item)
                elif in_section == 'suggestions':
                    suggestions.append(item)
    
    return adds, updates, suggestions

def generate_report():
    """生成日报"""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ 日志文件不存在")
        return
    
    adds, updates, suggestions = parse_today_section(content)
    
    if not adds and not updates and not suggestions:
        print("📭 今天没有变更记录")
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = datetime.now().strftime("%A")
    
    # 生成报告
    report = f"📊【客多多日报】{today} {weekday}\n\n"
    
    if adds:
        report += "✅ 今天新增：\n"
        for item in adds:
            report += f"  • {item}\n"
        report += "\n"
    
    if updates:
        report += "🔄 今天更新：\n"
        for item in updates:
            report += f"  • {item}\n"
        report += "\n"
    
    if suggestions:
        report += "💡 建议开发：\n"
        for item in suggestions:
            report += f"  • {item}\n"
        report += "\n"
    
    report += "---\n✨ 明天继续努力！"
    
    print(report)
    print("\n---")
    print("📤 准备发送...")
    
    # 通过 OpenClaw 发送（使用 sessions_send）
    # 注意：这里只是输出，实际发送由 OpenClaw 处理
    return report

if __name__ == "__main__":
    report = generate_report()
    if report:
        print(f"\n✅ 日报已生成，共 {len(report)} 字符")
