# -*- coding: utf-8 -*-
"""跟进写入功能"""

import argparse
import json
from typing import Any

import sys
sys.path.insert(0, str(__file__).rsplit('\\', 2)[0])  # 添加父目录到路径

from utils.cache import ensure_cache
from utils.helpers import clean_text, analyze_followup_content
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
    from client.search import resolve_single_client as _resolve
    return _resolve(clients, query)


def cmd_write_followup(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """
    写入跟进记录
    
    【自动添加跟进标签规则】
    执行写入跟进时，根据内容自动添加标签：
    - 如果内容描述的是"已完成的带看/看房" → 添加【有带看】
    - 如果内容描述的是"已通的电话" → 添加【通电话】
    - 如果内容描述的是"客户的回复/回应" → 添加【有回复】
    - 如果内容描述的是"分析/判断/想法" → 添加【解读】
    
    示例：
    - "带看了天山星城" → 【有带看】
    - "电话沟通 10 分钟" → 【通电话】
    - "客户回复说再看看" → 【有回复】
    - "客户纠结价格" → 【解读】
    - "约下次看房" → 【解读】（因为不是已完成的行为）
    """
    # AI 注意：请根据上述规则，在写入跟进前自动添加对应标签
    # 理解整个跟进内容的语义，不要只看关键词
    # 例如："电话约看房" 是通电话，不是有带看
    
    # 自动添加标签逻辑
    content = args.content
    if "带看" in content or "看房" in content or "实地" in content or "见面" in content:
        content = "【有带看】" + content
    elif "电话" in content or "通话" in content or "致电" in content:
        content = "【通电话】" + content
    elif "回复" in content or "回微信" in content or "回消息" in content or "客户说" in content:
        content = "【有回复】" + content
    else:
        content = "【解读】" + content
    
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1
    
    client = resolved["client"]
    followup_insights = analyze_followup_content(client, clean_text(content), cache.get("properties", []))
    
    if args.dry_run:
        from utils.cache import load_cache
        cache_data = load_cache() or {}
        preview = {
            "row": client["row"],
            "date": args.date,
            "column": 0,
            "created_new_date_column": False,
            "content": clean_text(content),
        }
        return {
            "status": "success",
            "command": "write-followup",
            "dry_run": True,
            "query": args.query,
            "client": client_brief(client),
            "preview": preview,
            "followup_insights": followup_insights,
        }, 0
    
    try:
        write_result = write_followup_via_excel(
            row_number=client["row"],
            content=content,
            date_str=args.date,
        )
    except Exception as exc:
        return {
            "status": "error",
            "message": f"写入跟进失败：{exc}",
            "query": args.query,
            "client": client_brief(client),
        }, 1
    
    payload = {
        "status": "success",
        "command": "write-followup",
        "query": args.query,
        "client": client_brief(client),
        "write_result": write_result,
        "followup_insights": followup_insights,
    }
    
    return payload, 0
