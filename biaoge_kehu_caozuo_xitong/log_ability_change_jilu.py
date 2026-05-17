# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
"""
记录能力变更
用法：
  python log_ability_change.py "新增" "能力名称" "详细描述"
  python log_ability_change.py "更新" "能力名称" "更新内容"
  python log_ability_change.py "建议" "能力名称" "建议理由"
"""
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

LOG_FILE = r'D:\OpenClaw\Workspaces\keduoduo\memory\ability-changes.md'

def log_change(change_type, ability, description):
    """记录能力变更"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 读取现有内容
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = f"# 客多多能力变更日志\n\n**创建日期：** {today}\n\n---\n\n"
    
    # 检查今天的内容是否存在
    today_section = f"## {today}"
    
    if today_section not in content:
        # 添加今天的部分
        today_content = f"""
## {today}

### 新增能力
- 

### 更新能力
- 

### 待办/建议
- 

---
"""
        # 插入到文件末尾（在最后一个 --- 之前）
        last_sep = content.rfind('---')
        if last_sep != -1:
            content = content[:last_sep] + today_content
        else:
            content += today_content
    
    # 根据类型添加到对应部分
    type_map = {
        "新增": "### 新增能力",
        "更新": "### 更新能力",
        "建议": "### 待办/建议"
    }
    
    target_section = type_map.get(change_type)
    if not target_section:
        print(f"❌ 未知类型：{change_type}，可用：新增，更新，建议")
        return
    
    # 找到对应部分，添加到第一行（- 后面）
    section_start = content.find(target_section)
    if section_start == -1:
        print(f"❌ 未找到部分：{target_section}")
        return
    
    # 找到下一行（- 开头）
    next_line = content.find('\n- ', section_start) + 3
    if next_line == 2:  # 没找到
        print(f"❌ 格式错误")
        return
    
    # 检查是否已有内容（跳过"- "占位符）
    line_content = content[next_line:content.find('\n', next_line)].strip()
    if not line_content or line_content == '':
        # 空行，直接替换
        end_line = content.find('\n', next_line)
        if end_line == -1:
            end_line = len(content)
        content = content[:next_line-2] + f"- {ability}：{description}\n" + content[end_line:]
    else:
        # 已有内容，插入新行
        new_line = f"- {ability}：{description}\n"
        content = content[:next_line] + new_line + content[next_line:]
    
    # 写回文件
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已记录：{change_type} - {ability}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法：python log_ability_change.py \"新增\" \"能力名称\" \"详细描述\"")
        print("  类型：新增，更新，建议")
        sys.exit(1)
    
    change_type = sys.argv[1]
    ability = sys.argv[2]
    description = sys.argv[3]
    
    log_change(change_type, ability, description)
