# -*- coding: utf-8 -*-
"""客户分级调整功能"""

import argparse
from typing import Any

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


def cmd_client_grade_adjust(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """客户分级调整"""
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1
    
    client = resolved["client"]
    
    updates = {
        "grade": args.new_grade,
    }
    
    try:
        write_result = update_client_fields_via_excel(client["row"], updates)
    except Exception as exc:
        return {
            "status": "error",
            "message": f"调整客户等级失败：{exc}",
            "query": args.query,
            "client": client_brief(client),
        }, 1
    
    return {
        "status": "success",
        "command": "client-grade-adjust",
        "query": args.query,
        "client": client_brief(client),
        "old_grade": client.get("grade"),
        "new_grade": args.new_grade,
        "updates": write_result,
    }, 0
