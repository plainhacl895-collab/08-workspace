# -*- coding: utf-8 -*-
"""客户更新功能"""

import argparse
import re
from typing import Any, Optional

import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from utils.cache import ensure_cache
from utils.helpers import clean_text
from utils.excel import update_client_fields_via_excel


def client_brief(client: dict[str, Any]) -> dict[str, Any]:
    """返回客户简要信息"""
    return {
        "row": client.get("row"),
        "name": client.get("name"),
        "phone": client.get("phone"),
        "grade": client.get("grade"),
        "budget": client.get("budget"),
        "district": client.get("district"),
    }


def resolve_single_client(clients: list[dict[str, Any]], query: str) -> dict[str, Any]:
    """解析单个客户"""
    from utils.helpers import search_clients
    matches = search_clients(clients, query)
    if not matches:
        return {"status": "not_found", "query": query, "message": f"未找到客户：{query}"}
    if len(matches) > 1:
        return {
            "status": "ambiguous", "query": query, "match_count": len(matches),
            "candidates": [{"row": m["record"]["row"], "name": m["record"]["name"]} for m in matches[:5]],
        }
    return {"status": "success", "query": query, "client": matches[0]["record"]}


def parse_client_updates(set_args: list[str], client: dict[str, Any]) -> dict[str, Any]:
    """解析客户更新参数"""
    updates = {}
    for item in set_args:
        if '=' not in item:
            continue
        key, value = item.split('=', 1)
        key = key.strip()
        value = value.strip()
        if key in ['grade', 'budget', 'district', 'rooms', 'phone', 'notes']:
            updates[key] = value
    return updates


def parse_client_update_instruction(client: dict[str, Any], instruction: str) -> dict[str, Any]:
    """从自然语言指令解析更新"""
    instruction = clean_text(instruction)
    updates = {}
    ignored_fields = []
    unparsed_clauses = []
    
    # 简单解析逻辑
    if '预算' in instruction:
        match = re.search(r'预算 (\d+) 万', instruction)
        if match:
            updates['budget'] = match.group(1)
    
    if '等级' in instruction:
        match = re.search(r'等级 ([ABCD])', instruction)
        if match:
            updates['grade'] = match.group(1)
    
    return {
        "updates": updates,
        "ignored_fields": ignored_fields,
        "unparsed_clauses": unparsed_clauses,
    }


def cmd_client_update(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """客户更新"""
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1
    
    client = resolved["client"]
    updates = parse_client_updates(args.set, client)
    
    if args.dry_run:
        return {
            "status": "success", "command": "client-update", "dry_run": True,
            "query": args.query, "client": client_brief(client), "updates": updates,
        }, 0
    
    try:
        write_result = update_client_fields_via_excel(client["row"], updates)
    except Exception as exc:
        return {
            "status": "error", "message": f"更新客户基础信息失败：{exc}",
            "query": args.query, "client": client_brief(client), "updates": updates,
        }, 1
    
    return {
        "status": "success", "command": "client-update",
        "query": args.query, "client": client_brief(client), "updates": write_result,
    }, 0


def cmd_client_update_from_text(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """客户更新从文本"""
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1
    
    client = resolved["client"]
    plan = parse_client_update_instruction(client, args.instruction)
    
    if not plan["updates"] and not plan["ignored_fields"]:
        return {
            "status": "no_update", "command": "client-update-from-text",
            "query": args.query, "client": client_brief(client),
            "instruction": clean_text(args.instruction),
            "message": "没有从这句话里解析出可执行的字段修改。",
        }, 1
    
    if args.dry_run:
        return {
            "status": "success", "command": "client-update-from-text", "dry_run": True,
            "query": args.query, "client": client_brief(client),
            "instruction": clean_text(args.instruction), "updates": plan["updates"],
            "ignored_fields": plan["ignored_fields"], "unparsed_clauses": plan["unparsed_clauses"],
        }, 0
    
    try:
        write_result = update_client_fields_via_excel(client["row"], plan["updates"])
    except Exception as exc:
        return {
            "status": "error", "message": f"按自然语言更新客户失败：{exc}",
            "query": args.query, "client": client_brief(client),
            "instruction": clean_text(args.instruction), "updates": plan["updates"],
        }, 1
    
    return {
        "status": "success", "command": "client-update-from-text",
        "query": args.query, "client": client_brief(client),
        "instruction": clean_text(args.instruction), "updates": write_result,
    }, 0
