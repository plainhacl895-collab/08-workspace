# -*- coding: utf-8 -*-
"""房源推荐功能"""

import argparse
from typing import Any

import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from utils.cache import ensure_cache
from utils.helpers import clean_text
from property.match import (
    client_brief, resolve_single_client, build_client_preferences_summary,
    is_district_match, DISTRICT_PLATE_MAP, extract_plate_name,
    _parse_rooms, _parse_rooms_priority, _get_price_zone, _generate_reason
)


def recommend_properties_for_client(client: dict[str, Any], properties: list[dict[str, Any]], candidate_limit: int = 5, final_limit: int = 3, needs_profile: dict = None, weights: dict = None, **kwargs) -> dict[str, Any]:
    """为客戶推荐房源
    
    预算浮动逻辑：
    - 下限 -10%：低于预算10%以内
    - 上限 +20%：超出预算20%以上不推荐
    - 极限下浮 -20% 以下：仅高房源分才推荐
    - 挂牌价可谈估算系数 0.95
    
    Args:
        weights: 自定义权重 {"price": 0.7, "room": 0.3}
    """
    rough_candidates = []
    excluded_recommended = []
    
    client_district = clean_text(client.get("district", ""))
    client_budget = client.get("budget", "") or 0
    try:
        client_budget = float(client_budget)
    except:
        client_budget = 0
    
    # 从 needs_profile 获取精准需求（由LLM提取）
    min_rooms = int(needs_profile.get('min_rooms', 0)) if needs_profile else 0
    max_rooms = int(needs_profile.get('max_rooms', 99)) if needs_profile else 99
    area_min = float(needs_profile.get('area_min', 0)) if needs_profile else 0
    area_max = float(needs_profile.get('area_max', 9999)) if needs_profile else 9999
    
    # 新增：意向板块、排除板块、意向小区
    preferred_plates = needs_profile.get('plates', []) if needs_profile else []
    excluded_plates = needs_profile.get('excluded_plates', []) if needs_profile else []
    preferred_communities = needs_profile.get('preferred_communities', []) if needs_profile else []
    
    # 解析已推送房源（排除已推无反馈）
    pushed_houses_raw = client.get('pushed_houses', '') or ''
    pushed_house_ids = set()
    if pushed_houses_raw:
        for hid in pushed_houses_raw.split('#'):
            hid = hid.strip()
            if hid:
                # 统一格式：去掉 .0 后缀
                if hid.endswith('.0'):
                    hid = hid[:-2]
                pushed_house_ids.add(hid)
    
    CORE_LOW = 0.90
    CORE_HIGH = 1.20
    CORE_LOW_BELOW = 0.80
    OVER_LIMIT = 1.20
    NEGOTIATION_FACTOR = 0.95
    
    for prop in properties:
        prop_plate = prop.get("plate", "")
        prop_price = prop.get("price", "")
        
        # 区域匹配
        prop_plate_name = extract_plate_name(prop_plate) if prop_plate else ''
        
        # 优先：排除板块
        if excluded_plates and prop_plate_name in excluded_plates:
            continue
        
        # 其次：意向板块（如果有，则只匹配这些板块）
        if preferred_plates:
            if prop_plate_name not in preferred_plates:
                continue
        # 再次：行政区匹配（兼容旧逻辑）
        elif not is_district_match(client_district, prop_plate):
            continue
        
        if not prop_price:
            continue
        
        # 房型过滤（精准需求）
        rooms = _parse_rooms(prop.get("layout", ""))
        if min_rooms > 0 and (rooms < min_rooms or rooms > max_rooms):
            continue
        
        # 面积过滤（精准需求）
        prop_area = float(prop.get("area", 0) or 0)
        if area_min > 0 and prop_area < area_min:
            continue
        if area_max < 9999 and prop_area > area_max:
            continue
        
        try:
            raw_price = float(prop_price)
        except:
            continue
        
        est_price = raw_price * NEGOTIATION_FACTOR
        
        # 超限排除
        if client_budget > 0 and est_price > client_budget * OVER_LIMIT:
            excluded_recommended.append(prop.get("house_id", ""))
            continue
        
        if client_budget > 0:
            price_deviation = (raw_price - client_budget) / client_budget
        else:
            price_deviation = 0
        
        # 极限下浮过滤
        if price_deviation < CORE_LOW_BELOW - 1:
            prop_score = float(prop.get("score", 0) or 0)
            if prop_score < 9.0:
                continue
        
        # 价格得分
        if price_deviation <= 0:
            price_score = max(0, 1.0 - abs(price_deviation) * 2)
        else:
            price_score = max(0, 1.0 - price_deviation * 3)
        
        # 房型得分（基于户型优先级）
        # 解析客户户型优先级（主力.备选）
        client_primary, client_secondary = _parse_rooms_priority(client.get("rooms", ""))
        
        if min_rooms > 0:
            room_diff = abs(rooms - (min_rooms + max_rooms) / 2)
            room_score = max(0, 1.0 - room_diff * 0.3)
            room_priority = None
        elif client_primary > 0:
            if rooms == client_primary:
                room_score = 1.0
                room_priority = "primary"
            elif client_secondary and rooms == client_secondary:
                room_score = 0.6
                room_priority = "secondary"
            else:
                room_diff = abs(rooms - client_primary)
                room_score = max(0, 0.5 - room_diff * 0.2)
                room_priority = None
        else:
            client_rooms_raw = _parse_rooms(client.get("rooms", ""))
            if client_rooms_raw > 0:
                room_diff = abs(rooms - client_rooms_raw)
                room_score = max(0, 1.0 - room_diff * 0.3)
                room_priority = None
            else:
                room_score = 0.5
                room_priority = None
        
        total_score = price_score * 0.7 + room_score * 0.3
        
        # 意向小区加分
        community_bonus = 0.0
        prop_community = prop.get('community', '') or ''
        if preferred_communities:
            for comm in preferred_communities:
                if comm in prop_community:
                    community_bonus = 0.3
                    break
        total_score += community_bonus
        
        # 已推送房源降分（避免重复推荐无反馈房源）
        prop_house_id = prop.get('house_id', '') or ''
        if prop_house_id.endswith('.0'):
            prop_house_id = prop_house_id[:-2]
        if prop_house_id in pushed_house_ids:
            total_score -= 0.3  # 已推送降分
        
        reason = _generate_reason(
            prop=prop,
            client=client,
            price_deviation=price_deviation,
            rooms=rooms,
            price_zone=_get_price_zone(price_deviation),
            needs_profile=needs_profile,
            room_priority=room_priority,
        )
        
        rough_candidates.append({
            "house_id": prop.get("house_id"),
            "title": prop.get("title"),
            "price": prop.get("price"),
            "est_price": round(est_price, 1),
            "area": prop.get("area"),
            "district": prop.get("district"),
            "plate": extract_plate_name(prop_plate),
            "layout": prop.get("layout"),
            "floor": prop.get("floor"),
            "community": prop.get("community"),
            "score": prop.get("score"),
            "url": prop.get("url"),
            "match_score": round(total_score, 3),
            "price_zone": _get_price_zone(price_deviation),
            "room_priority": room_priority,
            "reason": reason,
        })
    
    # 排序取候选
    rough_candidates.sort(key=lambda x: float(x.get("match_score", 0)), reverse=True)
    
    # 精选推荐：综合房源分和匹配分
    def recommendation_score(x):
        ms = float(x.get("match_score", 0))
        ps = float(x.get("score", 0))
        return ms * 0.5 + ps * 0.5
    
    reviewed = sorted(rough_candidates, key=recommendation_score, reverse=True)
    final = reviewed[:final_limit]
    
    return {
        "rough_candidates": rough_candidates[:candidate_limit],
        "reviewed_candidates": reviewed,
        "final_recommendations": final,
        "excluded_recommended": excluded_recommended,
        "summary": {
            "rough_count": len(rough_candidates),
            "reviewed_count": len(reviewed),
            "final_count": len(final),
        },
    }


def cmd_client_recommend_properties(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """客户房源推荐 — 自动提取需求后推荐"""
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1
    
    client = resolved["client"]
    
    # 自动提取客户需求（从跟进记录）
    needs_profile = None
    needs_info = None
    try:
        from property.extract_client_needs import extract_client_needs
        needs_info = extract_client_needs(client.get("row", 0), client.get("name"))
        if needs_info.get("status") == "success":
            needs_profile = {
                'min_rooms': needs_info.get('min_rooms', 0),
                'max_rooms': needs_info.get('max_rooms', 99),
                'area_min': needs_info.get('area_min', 0) or 0,
                'area_max': needs_info.get('area_max', 9999) or 9999,
                'special_requirements': needs_info.get('special_requirements', []),
                'plates': needs_info.get('plates', []),
                'excluded_plates': needs_info.get('excluded_plates', []),
                'preferred_communities': needs_info.get('preferred_communities', []),
                'floor_preference': needs_info.get('floor_preference'),
                'needs_parking': needs_info.get('needs_parking'),
                'orientation': needs_info.get('orientation'),
            }
    except Exception as e:
        needs_info = {"status": "error", "message": str(e)}
    
    # 可配置权重
    weights = None
    if getattr(args, 'weights', None):
        try:
            import json as _json
            weights = _json.loads(args.weights)
        except:
            pass
    
    recommendation = recommend_properties_for_client(
        client=client,
        properties=cache.get("properties", []),
        candidate_limit=max(1, int(getattr(args, 'candidate_limit', 5))),
        final_limit=max(1, int(getattr(args, 'final_limit', 3))),
        needs_profile=needs_profile,
        weights=weights,
        include_recommended=getattr(args, 'include_recommended', False),
    )
    
    status = "success" if recommendation["final_recommendations"] else "no_recommendation"
    message = (
        f"已为 {client.get('name')} 先粗筛房源，再抓详情精选推荐。"
        if recommendation["final_recommendations"]
        else f"已完成粗筛和详情复核，但暂时没有足够把握直接推荐给 {client.get('name')} 的房源。"
    )
    
    return {
        "status": status,
        "command": "client-recommend-properties",
        "query": args.query,
        "client": client_brief(client),
        "client_preferences": build_client_preferences_summary(client),
        "needs_extraction": needs_info,
        "message": message,
        "recommendation_summary": recommendation["summary"],
        "excluded_recommended_count": len(recommendation["excluded_recommended"]),
        "excluded_recommended_ids": recommendation["excluded_recommended"][:20],
        "rough_candidates": recommendation["rough_candidates"],
        "reviewed_candidates": recommendation["reviewed_candidates"],
        "final_recommendations": recommendation["final_recommendations"],
    }, 0
