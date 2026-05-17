# -*- coding: utf-8 -*-
"""跟进更新功能"""

import argparse
from typing import Any

import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from utils.cache import ensure_cache, load_cache
from utils.helpers import clean_text
from utils.excel import write_followup_via_excel


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
        return {
            "status": "not_found",
            "query": query,
            "message": f"未找到客户：{query}",
        }
    
    if len(matches) > 1:
        return {
            "status": "ambiguous",
            "query": query,
            "match_count": len(matches),
            "candidates": [
                {
                    "row": m["record"]["row"],
                    "name": m["record"]["name"],
                    "phone": m["record"]["phone"],
                }
                for m in matches[:5]
            ],
        }
    
    return {
        "status": "success",
        "query": query,
        "client": matches[0]["record"],
    }


def cmd_update_followup(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """智能更新跟进记录"""
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1
    
    client = resolved["client"]
    
    # 这里简化处理，实际应该读取原内容并合并
    # 由于是拆分，暂时使用简单实现
    content = "【解读】" + args.instruction
    
    try:
        write_result = write_followup_via_excel(
            row_number=client["row"],
            content=content,
            date_str=args.date,
        )
    except Exception as exc:
        return {
            "status": "error",
            "message": f"更新跟进失败：{exc}",
            "query": args.query,
            "client": client_brief(client),
        }, 1
    
    payload = {
        "status": "success",
        "command": "update-followup",
        "query": args.query,
        "client": client_brief(client),
        "update_result": write_result,
    }
    
    return payload, 0
