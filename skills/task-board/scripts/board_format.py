#!/usr/bin/env python3
"""
board_format.py - 看板格式化

用法：
    python board_format.py <目标> <步骤> <已完成> <风险> <下一步>
    python board_format.py --simple <目标> <当前> <已完成> <风险> <下一步>

输出标准看板格式：
    [看板] 🎯目标 | 📍步骤3/7 | ✅已完成 | ⚠️风险 | 🔄下一步
"""

import sys

def format_board_with_steps(target: str, step: str, completed: str, risk: str, next_step: str) -> str:
    """带步骤的看板格式"""
    risk_display = risk if risk and risk.lower() not in ["无", "none", ""] else "无"
    return f"[看板] 🎯{target} | 📍{step} | ✅{completed} | ⚠️{risk_display} | 🔄{next_step}"

def format_board_simple(target: str, current: str, completed: str, risk: str, next_step: str) -> str:
    """无步骤的看板格式"""
    risk_display = risk if risk and risk.lower() not in ["无", "none", ""] else "无"
    return f"[看板] 🎯{target} | 📍{current} | ✅{completed} | ⚠️{risk_display} | 🔄{next_step}"

def main():
    # 设置 stdout 编码为 utf-8，避免 Windows GBK 编码问题
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("用法：board_format.py <目标> <步骤> <已完成> <风险> <下一步>")
        print("或：board_format.py --simple <目标> <当前> <已完成> <风险> <下一步>")
        sys.exit(1)
    
    mode = sys.argv[1]
    
    if mode == "--simple":
        if len(sys.argv) < 7:
            print("用法：board_format.py --simple <目标> <当前> <已完成> <风险> <下一步>")
            sys.exit(1)
        result = format_board_simple(
            sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
        )
        print(result)
    
    else:
        if len(sys.argv) < 6:
            print("用法：board_format.py <目标> <步骤> <已完成> <风险> <下一步>")
            sys.exit(1)
        result = format_board_with_steps(
            sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        )
        print(result)

if __name__ == "__main__":
    main()