#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pre_action_check.py - 破坏性操作检测 + PermissionMode 分级

用法：
    python pre_action_check.py "操作描述"
    python pre_action_check.py "操作描述" --json

返回：
    - 如果是破坏性操作：输出确认提示格式
    - 如果是普通操作：输出 "OK"

PermissionMode 分级（借鉴 Claw Code）：
    - ReadOnly: 只读文件、查询数据、搜索
    - WorkspaceWrite: 写入文件、编辑、跟进记录
    - DangerFullAccess: 删除、覆盖、批量修改、外发消息

破坏性操作范围（与 SKILL.md 一致）：
    1. 删除文件、记录（含 Excel 行删除）
    2. 覆盖已有配置、数据、文件
    3. 批量操作（涉及2条以上记录）
    4. 外发消息（给客户发微信/短信/打电话）
    5. 修改客户等级、意向区域等关键字段
"""

import sys
import re
import json
from pathlib import Path

# stdout wrapper 移到 main() 内部

CONFIG_FILE = Path.home() / ".openclaw" / "workspace" / ".task-board-config.json"

# PermissionMode 分级
PERMISSION_MODES = {
    "ReadOnly": {
        "description": "只读文件、查询数据、搜索",
        "patterns": [
            r"读取", r"查询", r"搜索", r"查看", r"获取",
            r"read", r"query", r"search", r"get", r"fetch"
        ]
    },
    "WorkspaceWrite": {
        "description": "写入文件、编辑、跟进记录",
        "patterns": [
            r"写入", r"编辑", r"修改", r"更新", r"添加", r"跟进",
            r"write", r"edit", r"update", r"add", r"append"
        ]
    },
    "DangerFullAccess": {
        "description": "删除、覆盖、批量修改、外发消息",
        "patterns": [
            r"删除", r"移除", r"覆盖", r"批量", r"发.*客户", r"发送.*微信",
            r"delete", r"remove", r"overwrite", r"batch"
        ]
    }
}

# 破坏性操作关键词（正则匹配）
DESTRUCTIVE_PATTERNS = [
    # 删除类
    r"删除",
    r"移除",
    r"去掉",
    r"清空",
    r"erase",
    r"delete",
    r"remove",
    
    # 覆盖类
    r"覆盖",
    r"替换.*文件",
    r"重写",
    r"overwrite",
    
    # 批量操作类
    r"批量",
    r"全部.*修改",
    r"所有.*更改",
    r"多条.*记录",
    
    # 外发消息类
    r"发.*客户",
    r"发送.*微信",
    r"发.*短信",
    r"打电话.*客户",
    r"通知.*客户",
    r"回复.*客户",
    
    # 关键字段修改类
    r"修改.*等级",
    r"更改.*等级",
    r"调整.*等级",
    r"修改.*意向",
    r"更改.*意向",
    r"修改.*预算",
    r"更改.*预算",
]

def infer_permission_mode(action: str) -> str:
    """推断操作所需的 PermissionMode"""
    action_lower = action.lower()
    
    # 优先检查 DangerFullAccess
    for pattern in PERMISSION_MODES["DangerFullAccess"]["patterns"]:
        if re.search(pattern, action_lower, re.IGNORECASE):
            return "DangerFullAccess"
    
    # 检查 WorkspaceWrite
    for pattern in PERMISSION_MODES["WorkspaceWrite"]["patterns"]:
        if re.search(pattern, action_lower, re.IGNORECASE):
            return "WorkspaceWrite"
    
    # 默认 ReadOnly
    return "ReadOnly"

def check_destructive(action: str) -> dict:
    """检查操作是否破坏性，返回结构化结果"""
    is_destructive = False
    matched_pattern = None
    
    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, action, re.IGNORECASE):
            is_destructive = True
            matched_pattern = pattern
            break
    
    permission_mode = infer_permission_mode(action)
    risk = infer_risk_type(action) if is_destructive else ""
    
    return {
        "action": action,
        "is_destructive": is_destructive,
        "matched_pattern": matched_pattern,
        "permission_mode": permission_mode,
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

def format_warning(action: str, risk: str) -> str:
    """生成确认提示格式"""
    permission_mode = infer_permission_mode(action)
    
    warning = f"""⚠️ 破坏性操作检测
操作：{action}
风险：{risk}
PermissionMode：{permission_mode}
→ 请回复"确认"继续，或告诉我需要调整什么"""
    
    return warning

def format_json_result(result: dict) -> str:
    """生成 JSON 格式输出"""
    return json.dumps(result, ensure_ascii=False, indent=2)

def main():
    if len(sys.argv) < 2:
        print("用法：pre_action_check.py \"操作描述\" [--json]")
        sys.exit(1)
    
    action = sys.argv[1]
    output_json = "--json" in sys.argv
    
    result = check_destructive(action)
    
    if output_json:
        print(format_json_result(result))
    else:
        if result["is_destructive"]:
            print(format_warning(action, result["risk"]))
        else:
            print(f"OK (PermissionMode: {result['permission_mode']})")

if __name__ == "__main__":
    main()