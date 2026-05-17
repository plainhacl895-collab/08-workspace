# -*- coding: utf-8 -*-
"""客户分诊功能"""

import argparse
from datetime import datetime, timedelta
from typing import Any

import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from utils.cache import ensure_cache
from utils.helpers import clean_text


def analyze_client_triage(client: dict[str, Any]) -> dict[str, Any]:
    """分析客户分诊"""
    grade = clean_text(client.get("grade", "")).upper()
    last_followup = client.get("last_followup_date", "")
    followup_count = client.get("followup_count", 0)
    
    score = 0
    bucket = "low_signal"
    
    # A 级客户
    if grade == "A":
        score = 90
        bucket = "follow_now"
    # B 级客户
    elif grade == "B":
        score = 70
        bucket = "can_wait"
    # C 级客户
    elif grade == "C":
        score = 50
        bucket = "can_wait"
    # D 级客户
    elif grade == "D":
        score = 30
        bucket = "low_signal"
    
    # 根据跟进时间调整
    if last_followup:
        try:
            last_date = datetime.strptime(last_followup, "%Y-%m-%d")
            days_since = (datetime.now() - last_date).days
            
            if days_since > 7:
                score += 20  # 超过 7 天没跟进，加分
                if bucket == "can_wait":
                    bucket = "follow_now"
            elif days_since > 3:
                score += 10
        except:
            pass
    
    return {
        "bucket": bucket,
        "score": score,
        "grade": grade,
        "last_followup": last_followup,
        "followup_count": followup_count,
    }


def triage_brief(item: dict[str, Any]) -> dict[str, Any]:
    """返回分诊简要信息"""
    client = item["client"]
    triage = item["triage"]
    return {
        "row": client.get("row"),
        "name": client.get("name"),
        "phone": client.get("phone"),
        "grade": client.get("grade"),
        "budget": client.get("budget"),
        "district": client.get("district"),
        "bucket": triage.get("bucket"),
        "score": triage.get("score"),
    }


def cmd_client_triage(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """客户分诊"""
    cache = ensure_cache()
    scored = []
    for client in cache["clients"]:
        triage = analyze_client_triage(client)
        scored.append({"client": client, "triage": triage})
    
    follow_now = [item for item in scored if item["triage"]["bucket"] == "follow_now"]
    can_wait = [item for item in scored if item["triage"]["bucket"] == "can_wait"]
    low_signal = [item for item in scored if item["triage"]["bucket"] == "low_signal"]
    
    follow_now.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"]))
    can_wait.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"]))
    low_signal.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"]))
    
    return {
        "status": "success",
        "command": "client-triage",
        "generated_at": cache.get("generated_at"),
        "follow_now": [triage_brief(item) for item in follow_now[:args.limit]],
        "can_wait": [triage_brief(item) for item in can_wait[:args.limit]],
        "low_signal": [triage_brief(item) for item in low_signal[:args.limit]],
    }, 0
