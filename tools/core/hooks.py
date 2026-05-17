#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hooks.py - 团团助手 PreToolUse/PostToolUse 拦截机制

功能：
1. run_pre_hook：命令执行前检查，破坏性操作需要确认
2. run_post_hook：命令执行后验证，记录执行结果

破坏性命令清单（需要用户确认）：
- write-followup（写入跟进）
- update-followup（更新跟进）
- client-update（更新客户信息）
- client-update-from-text（从文本更新客户）
- client-grade-adjust（调整客户等级）
- experience-approve（批准经验）

非破坏性命令（直接执行）：
- client-search, client-context, client-triage, client-daily-brief
- property-search, property-detail, property-match, property-recommend
- experience-draft, experience-draft-list, experience-query
- doctor, refresh, core-guard-status
"""

import os
import sys
import json
import io
from datetime import datetime
from pathlib import Path
from typing import Any

# 破坏性命令清单
DESTRUCTIVE_COMMANDS = [
    "write-followup",
    "update-followup",
    "client-update",
    "client-update-from-text",
    "client-grade-adjust",
    "experience-approve",
]

# 日志文件路径
HOOK_LOG_PATH = Path.home() / ".openclaw" / "workspace" / "runtime" / "hook_logs.jsonl"


def run_pre_hook(command: str, args: Any) -> dict:
    """
    命令执行前拦截检查
    
    返回：
    - {"denied": False} → 允许执行
    - {"denied": True, "message": "..."} → 需要确认，返回提示信息
    
    如果用户已确认（--confirmed 参数），则允许执行破坏性命令。
    """
    # 检查是否有 --confirmed 参数
    confirmed = getattr(args, 'confirmed', False)
    if confirmed:
        return {"denied": False, "was_destructive": command in DESTRUCTIVE_COMMANDS}
    
    if command not in DESTRUCTIVE_COMMANDS:
        return {"denied": False}
    
    # 构建确认提示
    operation_desc = _build_operation_desc(command, args)
    risk_desc = _infer_risk(command)
    
    message = f"""⚠️ 破坏性操作检测
命令：{command}
操作：{operation_desc}
风险：{risk_desc}
→ 需要用户确认才能继续执行

确认方法：再次执行命令时添加 --confirmed 参数"""
    
    return {"denied": True, "message": message, "command": command, "args": args}


def run_post_hook(command: str, args: Any, result: dict) -> dict:
    """
    命令执行后验证记录
    
    功能：
    1. 记录执行结果到日志
    2. 如果是破坏性命令，标记已执行
    """
    # 记录日志
    _log_execution(command, args, result)
    
    # 如果执行失败，标记
    if result.get("status") == "error":
        result["hook_warning"] = "命令执行失败，请检查"
    
    return result


def _build_operation_desc(command: str, args: Any) -> str:
    """构建操作描述"""
    if command == "write-followup":
        query = getattr(args, 'query', '未知客户')
        date = getattr(args, 'date', '未知日期')
        return f"写入 {query} 的跟进记录，日期 {date}"
    
    if command == "update-followup":
        query = getattr(args, 'query', '未知客户')
        instruction = getattr(args, 'instruction', '未知修改')
        return f"修改 {query} 的跟进记录：{instruction}"
    
    if command == "client-update":
        query = getattr(args, 'query', '未知客户')
        sets = getattr(args, 'set', [])
        return f"更新客户 {query} 的字段：{sets}"
    
    if command == "client-update-from-text":
        query = getattr(args, 'query', '未知客户')
        instruction = getattr(args, 'instruction', '未知修改')
        return f"从文本更新客户 {query}：{instruction}"
    
    if command == "client-grade-adjust":
        query = getattr(args, 'query', '未知客户')
        new_grade = getattr(args, 'new_grade', '未知等级')
        return f"调整客户 {query} 的等级为 {new_grade}"
    
    if command == "experience-approve":
        draft_id = getattr(args, 'draft_id', '未知ID')
        return f"批准经验草稿 {draft_id}"
    
    return f"执行命令 {command}"


def _infer_risk(command: str) -> str:
    """推断风险类型"""
    if command in ["write-followup", "update-followup"]:
        return "跟进记录将被修改/新增，写入 Excel 后无法撤销"
    
    if command in ["client-update", "client-update-from-text"]:
        return "客户信息将被修改，可能影响后续匹配和跟进"
    
    if command == "client-grade-adjust":
        return "客户等级调整会影响跟进优先级和分类"
    
    if command == "experience-approve":
        return "经验草稿将被批准入库，无法撤回"
    
    return "操作不可逆或影响范围较大"


def _log_execution(command: str, args: Any, result: dict) -> None:
    """记录执行日志"""
    try:
        HOOK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "args": {k: v for k, v in vars(args).items() if not k.startswith('_')},
            "status": result.get("status", "unknown"),
            "is_destructive": command in DESTRUCTIVE_COMMANDS,
        }
        
        with open(HOOK_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        # 日志记录失败不影响主流程
        pass


# 测试入口
if __name__ == "__main__":
    import argparse
    import io
    
    # 设置 stdout 编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=== hooks.py 测试 ===")
    
    # 测试1：破坏性命令检测
    test_args = argparse.Namespace(query="张三", date="2026-04-28", content="测试跟进")
    result = run_pre_hook("write-followup", test_args)
    print("\n测试 write-followup:")
    print(result.get("message") if result.get("denied") else "OK (允许执行)")
    
    # 测试2：非破坏性命令
    test_args2 = argparse.Namespace(query="李四")
    result2 = run_pre_hook("client-search", test_args2)
    print("\n测试 client-search:")
    print("OK (允许执行)" if not result2.get("denied") else result2.get("message"))
    
    # 测试3：post hook
    test_result = {"status": "success", "message": "写入成功"}
    result3 = run_post_hook("write-followup", test_args, test_result)
    print("\n测试 post_hook:")
    print(f"状态: {result3.get('status')}")
    
    # 测试4：日志记录
    print("\n测试日志路径:")
    print(str(HOOK_LOG_PATH))
    
    print("\n=== 测试完成 ===")