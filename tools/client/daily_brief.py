# -*- coding: utf-8 -*-
"""客户每日简报功能"""

import argparse
from datetime import datetime
from typing import Any

import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from utils.cache import ensure_cache
from utils.helpers import clean_text
from client.triage import analyze_client_triage


def daily_brief_item(item: dict[str, Any]) -> dict[str, Any]:
    """返回每日简报项目"""
    client = item["client"]
    triage = item["triage"]
    return {
        "row": client.get("row"),
        "name": client.get("name"),
        "phone": client.get("phone"),
        "grade": client.get("grade"),
        "budget": client.get("budget"),
        "district": client.get("district"),
        "score": triage.get("score"),
        "bucket": triage.get("bucket"),
        "last_followup": client.get("last_followup_date"),
    }


def cmd_client_daily_brief(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """客户每日简报"""
    cache = ensure_cache()
    scored = []
    for client in cache["clients"]:
        triage = analyze_client_triage(client)
        scored.append({"client": client, "triage": triage})
    
    # 分桶
    grade_a = [item for item in scored if clean_text(item["client"].get("grade")).upper() == "A"]
    is_re_hot = [item for item in scored if item["triage"].get("is_re_hot", False) and item not in grade_a]
    is_forget_protection = [
        item for item in scored
        if item["triage"].get("is_forget_protection", False) and item not in grade_a and item not in is_re_hot
    ]
    can_wait = [
        item for item in scored
        if item["triage"]["bucket"] == "can_wait" and item not in grade_a and item not in is_re_hot and item not in is_forget_protection
    ]
    low_signal_count = len([item for item in scored if item["triage"]["bucket"] == "low_signal"])
    
    # 排序
    is_forget_protection.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"]))
    can_wait.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"]))
    
    # 组装
    priority_list = grade_a + is_re_hot
    remaining = max(0, args.limit - len(priority_list))
    priority_list += is_forget_protection[:remaining]
    
    return {
        "status": "success",
        "command": "client-daily-brief",
        "generated_at": cache.get("generated_at"),
        "priority_clients": [daily_brief_item(item) for item in priority_list],
        "can_wait": [daily_brief_item(item) for item in can_wait[:args.wait_limit]],
        "summary": {
            "priority_count": len(priority_list),
            "can_wait_count": len(can_wait),
            "low_signal_count": low_signal_count,
            "grade_a_count": len(grade_a),
            "re_hot_count": len(is_re_hot),
            "forget_protection_count": min(len(is_forget_protection), remaining),
        },
    }, 0
