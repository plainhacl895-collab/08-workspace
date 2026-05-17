# -*- coding: utf-8 -*-
"""房源搜索功能"""

import argparse
from typing import Any

import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from utils.cache import ensure_cache


def cmd_property_search(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """房源搜索"""
    cache = ensure_cache()
    properties = cache.get("properties", [])
    
    query = args.query.lower() if args.query else ""
    
    # 智能筛选：按小区、区域、标题、板块匹配
    results = []
    for prop in properties:
        title = str(prop.get("title", "")).lower()
        district = str(prop.get("district", "")).lower()
        house_id = str(prop.get("house_id", "")).lower()
        community = str(prop.get("community", "")).lower()  # 小区名
        plate = str(prop.get("plate", "")).lower()  # 板块
        
        # 匹配关键词
        if query and (query in title or query in district or query in house_id or query in community or query in plate):
            results.append(prop)
        elif not query:
            results.append(prop)
        
        # 最多返回 50 套，避免过载
        if len(results) >= 50:
            break
    
    return {
        "status": "success",
        "match_count": len(results),
        "properties": results,
        "total_properties": len(properties),
    }, 0


def cmd_property_detail(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """房源详情"""
    cache = ensure_cache()
    properties = cache.get("properties", [])
    
    house_id = args.house_id
    for prop in properties:
        if prop.get("house_id") == house_id:
            return {
                "status": "success",
                "property": prop,
            }, 0
    
    return {
        "status": "not_found",
        "house_id": house_id,
        "message": f"未找到房源：{house_id}",
    }, 1
