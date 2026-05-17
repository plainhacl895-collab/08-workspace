# -*- coding: utf-8 -*-
"""客户查询功能"""

import argparse
from typing import Any

import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from utils.cache import ensure_cache
from utils.helpers import clean_text, normalize_text, digits_only, score_client_match


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


def search_clients(clients: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """搜索客户"""
    query = clean_text(query)
    if not query:
        return []
    
    q_digits = digits_only(query)
    q_norm = normalize_text(query)
    q_row = int(query) if query.isdigit() else None
    matches: list[dict[str, Any]] = []
    
    for client in clients:
        score = score_client_match(client, q_row, q_digits, q_norm)
        if score <= 0:
            continue
        matches.append({"score": score, "record": client})
    
    matches.sort(
        key=lambda item: (
            -item["score"],
            item["record"]["name"],
            item["record"]["row"],
        )
    )
    return matches


def resolve_single_client(clients: list[dict[str, Any]], query: str) -> dict[str, Any]:
    """解析单个客户"""
    # 如果是数字，直接按行号查找
    if query.isdigit():
        row_num = int(query)
        for client in clients:
            if client.get("row") == row_num:
                return {
                    "status": "success",
                    "query": query,
                    "client": client,
                }
        return {
            "status": "not_found",
            "query": query,
            "message": f"未找到行号为 {row_num} 的客户",
        }
    
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
                    "grade": m["record"]["grade"],
                    "budget": m["record"]["budget"],
                    "district": m["record"]["district"],
                    "followup_count": m["record"].get("followup_count", 0),
                    "last_followup_date": m["record"].get("last_followup_date"),
                }
                for m in matches[:5]
            ],
        }
    
    return {
        "status": "success",
        "query": query,
        "client": matches[0]["record"],
    }


def cmd_client_search(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """客户搜索"""
    cache = ensure_cache()
    matches = search_clients(cache["clients"], args.query)
    
    if not matches:
        return {
            "status": "not_found",
            "query": args.query,
            "message": f"未找到客户：{args.query}",
        }, 1
    
    result = {
        "status": "success" if len(matches) == 1 else "ambiguous",
        "query": args.query,
        "match_count": len(matches),
        "candidates": [
            {
                "row": m["record"]["row"],
                "name": m["record"]["name"],
                "phone": m["record"]["phone"],
                "grade": m["record"]["grade"],
                "budget": m["record"]["budget"],
                "district": m["record"]["district"],
                "followup_count": m["record"].get("followup_count", 0),
                "last_followup_date": m["record"].get("last_followup_date"),
            }
            for m in matches[:10]
        ],
    }
    
    return result, 0


def cmd_client_context(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """客户上下文（详情）"""
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    
    if resolved["status"] != "success":
        return resolved, 1
    
    client = resolved["client"]
    
    # 获取跟进记录（从缓存读取）
    followups = {
        "total": client.get("followup_count", 0),
        "latest_date": client.get("last_followup_date"),
        "recent": client.get("followups", []),
    }
    
    result = {
        "status": "success",
        "query": args.query,
        "client": {
            "row": client.get("row"),
            "name": client.get("name"),
            "phone": client.get("phone"),
            "grade": client.get("grade"),
            "rooms": client.get("rooms"),
            "budget": client.get("budget"),
            "district": client.get("district"),
            "decode": client.get("decode"),
            "decision_speed": client.get("decision_speed"),
            "info_style": client.get("info_style"),
            "interaction_style": client.get("interaction_style"),
            "need": client.get("need"),
            "ideal_phrase": client.get("ideal_phrase"),
            "pain": client.get("pain"),
            "notes": client.get("notes"),
            "followup_count": client.get("followup_count", 0),
            "last_followup_date": client.get("last_followup_date"),
        },
        "followups": followups,
    }
    
    return result, 0
