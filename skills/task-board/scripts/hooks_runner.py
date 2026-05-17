#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hooks_runner.py - Hooks 执行器（借鉴 Claw Code hooks.rs）

核心机制：
- PreToolUse: 执行前调用 Shell 命令，exit code 0=allow, 2=deny, 其他=warn
- PostToolUse: 执行后调用 Shell 命令，收集反馈信息

配置来源：
~/.openclaw/workspace/.task-board-config.json

用法：
    python hooks_runner.py pre <工具名> <输入JSON>
    python hooks_runner.py post <工具名> <输入JSON> <输出> <是否错误>
    python hooks_runner.py check-config

Exit Code 含义（与 Claw Code 一致）：
    0 = Allow (允许继续)
    2 = Deny (拒绝执行)
    其他 = Warn (警告但允许继续)
"""

import json
import os
import subprocess
import sys
import re
from pathlib import Path

CONFIG_FILE = Path.home() / ".openclaw" / "workspace" / ".task-board-config.json"

# stdout wrapper 移到 main() 内部，避免 import 时关闭

class HookRunResult:
    """Hook 执行结果（借鉴 Claw Code HookRunResult）"""
    def __init__(self, denied: bool, messages: list):
        self.denied = denied
        self.messages = messages
    
    def is_denied(self) -> bool:
        return self.denied
    
    def get_messages(self) -> list:
        return self.messages
    
    def format_output(self) -> str:
        if not self.messages:
            return ""
        return "\n".join(self.messages)

def load_config() -> dict:
    """加载配置文件"""
    if not CONFIG_FILE.exists():
        return {
            "hooks": {
                "PreToolUse": [],
                "PostToolUse": []
            },
            "permissionMode": "workspace-write"
        }
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 配置文件读取失败: {e}")
        return {
            "hooks": {
                "PreToolUse": [],
                "PostToolUse": []
            }
        }

def run_shell_command(command: str, payload: dict) -> tuple:
    """
    执行 Shell 命令（借鉴 Claw Code run_command）
    
    返回: (exit_code, stdout, stderr)
    """
    # Windows 适配
    if sys.platform == "win32":
        shell_cmd = ["cmd", "/C", command]
    else:
        shell_cmd = ["sh", "-lc", command]
    
    # 设置环境变量（与 Claw Code 一致）
    env = os.environ.copy()
    env["HOOK_EVENT"] = str(payload.get("hook_event_name", ""))
    env["HOOK_TOOL_NAME"] = str(payload.get("tool_name", ""))
    env["HOOK_TOOL_INPUT"] = str(payload.get("tool_input", ""))
    env["HOOK_TOOL_OUTPUT"] = str(payload.get("tool_output", "") or "")
    env["HOOK_TOOL_IS_ERROR"] = "1" if payload.get("tool_result_is_error", False) else "0"
    
    try:
        # 通过 stdin 传递 JSON payload
        result = subprocess.run(
            shell_cmd,
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=30  # 30秒超时
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Hook 命令超时"
    except Exception as e:
        return -1, "", f"Hook 命令执行失败: {e}"

def run_pre_tool_use(tool_name: str, tool_input: str) -> HookRunResult:
    """
    执行 PreToolUse Hooks（借鉴 Claw Code run_pre_tool_use）
    """
    config = load_config()
    commands = config.get("hooks", {}).get("PreToolUse", [])
    
    if not commands:
        return HookRunResult(False, [])
    
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": parse_tool_input(tool_input),
        "tool_input_json": tool_input,
        "tool_output": None,
        "tool_result_is_error": False
    }
    
    messages = []
    
    for command in commands:
        exit_code, stdout, stderr = run_shell_command(command, payload)
        
        # Exit code 逻辑（与 Claw Code 一致）
        if exit_code == 0:
            # Allow: 收集 stdout 作为反馈
            if stdout:
                messages.append(stdout)
        elif exit_code == 2:
            # Deny: 拒绝执行
            deny_message = stdout or stderr or f"PreToolUse hook denied tool `{tool_name}`"
            messages.append(deny_message)
            return HookRunResult(True, messages)
        else:
            # Warn: 警告但允许继续
            warn_message = f"Hook `{command}` exited with status {exit_code}; allowing tool execution to continue"
            if stdout:
                warn_message += f": {stdout}"
            elif stderr:
                warn_message += f": {stderr}"
            messages.append(warn_message)
    
    return HookRunResult(False, messages)

def run_post_tool_use(tool_name: str, tool_input: str, tool_output: str, is_error: bool) -> HookRunResult:
    """
    执行 PostToolUse Hooks（借鉴 Claw Code run_post_tool_use）
    """
    config = load_config()
    commands = config.get("hooks", {}).get("PostToolUse", [])
    
    if not commands:
        return HookRunResult(False, [])
    
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": tool_name,
        "tool_input": parse_tool_input(tool_input),
        "tool_input_json": tool_input,
        "tool_output": tool_output,
        "tool_result_is_error": is_error
    }
    
    messages = []
    
    for command in commands:
        exit_code, stdout, stderr = run_shell_command(command, payload)
        
        if exit_code == 0:
            if stdout:
                messages.append(stdout)
        elif exit_code == 2:
            # PostToolUse deny: 标记为错误
            deny_message = stdout or stderr or f"PostToolUse hook denied tool `{tool_name}`"
            messages.append(deny_message)
            return HookRunResult(True, messages)
        else:
            warn_message = f"PostToolUse hook `{command}` exited with status {exit_code}"
            if stdout:
                warn_message += f": {stdout}"
            messages.append(warn_message)
    
    return HookRunResult(False, messages)

def parse_tool_input(tool_input: str) -> dict:
    """解析工具输入（借鉴 Claw Code parse_tool_input）"""
    try:
        return json.loads(tool_input)
    except:
        return {"raw": tool_input}

def normalize_permission_mode(mode: str) -> str:
    """标准化 PermissionMode 名称"""
    mapping = {
        "workspace-write": "WorkspaceWrite",
        "readonly": "ReadOnly",
        "danger-full-access": "DangerFullAccess"
    }
    return mapping.get(mode.lower(), mode)

# PermissionMode 分级（本地实现）
PERMISSION_MODES = {
    "ReadOnly": {
        "patterns": [r"读取", r"查询", r"搜索", r"查看", r"获取", r"read", r"query", r"search", r"get", r"fetch"]
    },
    "WorkspaceWrite": {
        "patterns": [r"写入", r"编辑", r"修改", r"更新", r"添加", r"跟进", r"write", r"edit", r"update", r"add", r"append"]
    },
    "DangerFullAccess": {
        "patterns": [r"删除", r"移除", r"覆盖", r"批量", r"发.*客户", r"发送.*微信", r"delete", r"remove", r"overwrite", r"batch"]
    }
}

# 破坏性操作关键词
DESTRUCTIVE_PATTERNS = [
    r"删除", r"移除", r"去掉", r"清空", r"erase", r"delete", r"remove",
    r"覆盖", r"替换.*文件", r"重写", r"overwrite",
    r"批量", r"全部.*修改", r"所有.*更改", r"多条.*记录",
    r"发.*客户", r"发送.*微信", r"发.*短信", r"打电话.*客户", r"通知.*客户", r"回复.*客户",
    r"修改.*等级", r"更改.*等级", r"调整.*等级", r"修改.*意向", r"更改.*意向", r"修改.*预算", r"更改.*预算"
]

def infer_permission_mode_local(action: str) -> str:
    """推断操作所需的 PermissionMode"""
    action_lower = action.lower()
    for pattern in PERMISSION_MODES["DangerFullAccess"]["patterns"]:
        if re.search(pattern, action_lower, re.IGNORECASE):
            return "DangerFullAccess"
    for pattern in PERMISSION_MODES["WorkspaceWrite"]["patterns"]:
        if re.search(pattern, action_lower, re.IGNORECASE):
            return "WorkspaceWrite"
    return "ReadOnly"

def check_destructive_local(action: str) -> dict:
    """检查操作是否破坏性"""
    is_destructive = False
    matched_pattern = None
    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, action, re.IGNORECASE):
            is_destructive = True
            matched_pattern = pattern
            break
    
    risk = infer_risk_type(action) if is_destructive else ""
    return {
        "is_destructive": is_destructive,
        "matched_pattern": matched_pattern,
        "risk": risk
    }

def infer_risk_type(action: str) -> str:
    """推断风险类型"""
    action_lower = action.lower()
    if any(kw in action_lower for kw in ["删除", "delete", "remove", "移除", "清空"]):
        return "数据/文件将被删除，无法撤销"
    if any(kw in action_lower for kw in ["覆盖", "overwrite", "重写", "替换"]):
        return "原有数据将被覆盖，无法恢复"
    if any(kw in action_lower for kw in ["批量", "全部", "所有", "多条"]):
        return "涉及多条记录，影响范围大"
    if any(kw in action_lower for kw in ["发", "发送", "通知", "回复", "打电话"]):
        return "消息将外发给客户，发送后无法撤回"
    if any(kw in action_lower for kw in ["等级", "意向", "预算", "关键"]):
        return "关键字段被修改，影响客户分类和匹配"
    return "操作不可逆或影响范围较大"

def check_permission_mode(operation: str) -> dict:
    """
    检查 PermissionMode（整合 pre_action_check.py 逻辑）
    
    返回: {
        "operation": str,
        "required_mode": str,
        "current_mode": str,
        "allowed": bool,
        "reason": str
    }
    """
    config = load_config()
    current_mode_raw = config.get("permissionMode", "workspace-write")
    current_mode = normalize_permission_mode(current_mode_raw)
    
    # 直接实现判断逻辑（不依赖 import）
    required_mode = infer_permission_mode_local(operation)
    destructive_result = check_destructive_local(operation)
    
    # 权限检查逻辑
    mode_hierarchy = ["ReadOnly", "WorkspaceWrite", "DangerFullAccess"]
    current_level = mode_hierarchy.index(current_mode)
    required_level = mode_hierarchy.index(required_mode)
    
    allowed = current_level >= required_level
    
    reason = ""
    if not allowed:
        reason = f"当前权限模式 {current_mode} 不允许 {required_mode} 级别操作"
    elif destructive_result["is_destructive"]:
        reason = f"破坏性操作：{destructive_result['risk']}"
    
    return {
        "operation": operation,
        "required_mode": required_mode,
        "current_mode": current_mode,
        "allowed": allowed,
        "is_destructive": destructive_result["is_destructive"],
        "reason": reason
    }

def main():
    # 设置 stdout 编码
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("用法：hooks_runner.py <pre|post|check-config|check-permission> [参数...]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "pre":
        if len(sys.argv) < 4:
            print("用法：hooks_runner.py pre <工具名> <输入JSON>")
            sys.exit(1)
        
        tool_name = sys.argv[2]
        tool_input = sys.argv[3]
        
        result = run_pre_tool_use(tool_name, tool_input)
        
        if result.is_denied():
            print(f"❌ DENY: {result.format_output()}")
            sys.exit(2)  # Exit code 2 = Deny
        else:
            feedback = result.format_output()
            if feedback:
                print(f"⚠️ WARN: {feedback}")
            else:
                print("✅ ALLOW")
            sys.exit(0)
    
    elif command == "post":
        if len(sys.argv) < 6:
            print("用法：hooks_runner.py post <工具名> <输入JSON> <输出> <是否错误>")
            sys.exit(1)
        
        tool_name = sys.argv[2]
        tool_input = sys.argv[3]
        tool_output = sys.argv[4]
        is_error = sys.argv[5].lower() in ["true", "1", "yes"]
        
        result = run_post_tool_use(tool_name, tool_input, tool_output, is_error)
        
        feedback = result.format_output()
        if feedback:
            print(f"[反馈] {feedback}")
        sys.exit(0 if not result.is_denied() else 2)
    
    elif command == "check-config":
        config = load_config()
        print(json.dumps(config, ensure_ascii=False, indent=2))
    
    elif command == "check-permission":
        if len(sys.argv) < 3:
            print("用法：hooks_runner.py check-permission <操作描述>")
            sys.exit(1)
        
        operation = sys.argv[2]
        result = check_permission_mode(operation)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if not result["allowed"]:
            sys.exit(2)
        elif result["is_destructive"]:
            print(f"\n⚠️ 破坏性操作检测\n操作：{operation}\n风险：{result['reason']}\n→ 请回复\"确认\"继续")
            sys.exit(2)
        else:
            sys.exit(0)
    
    else:
        print(f"未知命令：{command}")
        sys.exit(1)

if __name__ == "__main__":
    main()