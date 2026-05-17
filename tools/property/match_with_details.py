# -*- coding: utf-8 -*-
"""房源精准匹配（集成详情页+加权特殊要求）"""

import argparse
import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from property.match import match_properties_for_client
from property.fetch_property_detail import fetch_property_detail

# 特殊要求等级对应的惩罚系数
LEVEL_PENALTY = {
    'hard': 0.5,    # 硬性要求：权重×0.5
    'medium': 0.3, # 中等要求：权重×0.3
    'soft': 0.1,   # 软性要求：权重×0.1
}


def _normalize_special_requirement(req) -> dict:
    """将特殊要求标准化为 {req, weight, level} 格式
    
    支持两种输入格式：
    - 字符串：'不要临街' -> {'req': '不要临街', 'weight': 1.0, 'level': 'hard'}
    - 字典：{'req': '不要临街', 'weight': 0.8, 'level': 'medium'}
    """
    if isinstance(req, dict):
        return {
            'req': req.get('req', ''),
            'weight': float(req.get('weight', 0.5)),
            'level': req.get('level', 'medium'),
        }
    else:
        req_str = str(req)
        level = 'medium'
        if any(kw in req_str for kw in ['不要', '不能', '必须', '绝对']):
            level = 'hard'
        elif any(kw in req_str for kw in ['最好', '希望', '有的话更好']):
            level = 'soft'
        return {'req': req_str, 'weight': 1.0, 'level': level}


def _evaluate_requirement(req_dict: dict, prop_detail: dict) -> tuple[float, str]:
    """评估单个特殊要求对房源的满足程度
    
    Returns:
        (discount_factor, note)
        discount_factor: 满足度折扣（0.0-1.0），1.0=完全满足，0.0=完全不满足
        note: 不满足时的说明
    """
    req = req_dict.get('req', '')
    weight = req_dict.get('weight', 1.0)
    level = req_dict.get('level', 'medium')
    penalty = LEVEL_PENALTY.get(level, 0.3)
    
    # 临街类
    if '临街' in req and '不' in req:
        if prop_detail.get('has_street_issue') or prop_detail.get('street_facing') == True:
            return 0.0, '嫌恶设施包含临街'
        return 1.0, ''
    
    # 车位类
    if '车位' in req and '无' not in req:
        has_parking = prop_detail.get('has_parking')
        if has_parking == False:
            return max(0.0, 1.0 - weight * penalty), '无车位'
        elif has_parking == True:
            return 1.0, ''
        else:
            return max(0.5, 1.0 - weight * penalty * 0.3), '车位未知'
    
    # 采光类
    if '采光' in req:
        facing = prop_detail.get('facing', '')
        floor_high = prop_detail.get('floor_high', False)
        if facing in ['南', '东南'] and floor_high:
            return 1.0, ''
        elif facing in ['南', '东南'] or floor_high:
            return max(0.6, 1.0 - weight * penalty * 0.5), f'朝向{facing}'
        else:
            return max(0.3, 1.0 - weight * penalty), f'朝向{facing}'
    
    # 精装修类
    if '精装' in req:
        decoration = prop_detail.get('decoration', '')
        if '精装' in decoration:
            return 1.0, ''
        elif decoration:
            return max(0.5, 1.0 - weight * penalty), f'装修:{decoration}'
        return 0.5, '装修未知'
    
    # 楼层高区类
    if '高区' in req or ('楼层' in req and '高' in req):
        if prop_detail.get('floor_high') == True:
            return 1.0, ''
        floor = prop_detail.get('floor_current', '')
        return max(0.4, 1.0 - weight * penalty), f'楼层:{floor}'
    
    # 户型/厅朝向类（南北通 > 厅朝南 > 厅朝北）
    if any(kw in req for kw in ['户型', '南北通', '厅朝', '厅的朝向']):
        hall_type = prop_detail.get('hall_type', '')
        hall_facing = prop_detail.get('hall_facing', '')
        
        if '南北通' in req or '厅的朝向' in req:
            # 南北通：最优
            if hall_type == '南北通':
                return 1.0, ''
            elif hall_type == '厅朝南':
                return max(0.8, 1.0 - weight * penalty * 0.2), f'厅类型:{hall_type}，非南北通但厅朝南'
            elif hall_type == '厅朝北':
                # 厅朝北是客户最不喜欢的，只有其他方面极度优秀才能勉强接受
                return max(0.2, 1.0 - weight * penalty * 1.5), f'厅朝北，最差选项'
            elif hall_type:
                return max(0.6, 1.0 - weight * penalty * 0.6), f'厅类型:{hall_type}'
            else:
                return max(0.5, 1.0 - weight * penalty * 0.5), '厅朝向未知'
        
        # "两房朝南厅朝北"或"厅朝北"作为关键词
        if '厅朝北' in req or ('厅朝' in req and '北' in req):
            if hall_type == '厅朝北':
                # 客户明确介意厅朝北
                return max(0.2, 1.0 - weight * penalty * 1.5), '厅朝北（客户介意）'
            elif hall_type == '南北通':
                return 1.0, ''
        
        # 朝南相关
        if '朝南' in req and hall_type == '厅朝南':
            return 1.0, ''
    
    # 默认：无法评估，返回中等折扣
    return 1.0, ''


def match_with_details(client: dict, properties: list, needs_profile: dict = None, limit: int = 5) -> tuple[list[dict], list[dict], list[dict]]:
    """精准匹配+详情页+加权特殊要求
    
    流程：
    1. 粗筛匹配：区域+预算+房型+面积 → Top N候选
    2. 详情页抓取：逐个获取嫌恶设施/朝向/车位等
    3. 加权特殊要求评估：计算折扣乘数，不硬排除
    4. 输出最终推荐
    
    Returns:
        (final_matches, excluded_hard_fail, all_candidates)
    """
    CANDIDATE_LIMIT = 10
    candidates, excluded = match_properties_for_client(
        client=client,
        properties=properties,
        limit=CANDIDATE_LIMIT,
        needs_profile=needs_profile,
    )
    
    if not candidates:
        return []
    
    # 标准化特殊要求
    raw_special = needs_profile.get('special_requirements', []) if needs_profile else []
    special_reqs = [_normalize_special_requirement(r) for r in raw_special]
    
    final_matches = []
    excluded_hard_fail = []
    detail_cache = {}
    
    for cand in candidates:
        house_id = str(cand.get('house_id', '')).replace('.0', '').strip()
        if not house_id or house_id == 'None':
            continue
        
        # 抓详情
        if house_id not in detail_cache:
            detail_cache[house_id] = fetch_property_detail(house_id)
        
        prop_detail = detail_cache[house_id]
        base_score = float(cand.get('match_score', 0))
        
        # 评估所有特殊要求
        total_discount = 1.0
        special_notes = []
        hard_fail = False
        
        for req_dict in special_reqs:
            discount, note = _evaluate_requirement(req_dict, prop_detail)
            if discount == 0.0:
                # 硬性要求不满足 → 该房源不适合此客户，但不排除（用于对比展示）
                hard_fail = True
                special_notes.append(f"⚠️{req_dict['req']}:{note}")
            elif discount < 1.0:
                total_discount *= discount
                if note:
                    special_notes.append(f"{req_dict['req']}:{note}")
        
        # 最终得分 = 基础分 × 总折扣
        final_score = base_score * total_discount
        
        # 硬性要求不满足 → 直接排除，不进入推荐列表
        if hard_fail:
            cand['match_score'] = final_score
            cand['special_notes'] = special_notes
            cand['hard_fail'] = hard_fail
            cand['excluded_reason'] = '硬性要求不满足'
            excluded_hard_fail.append(cand)
            continue
        
        cand['match_score'] = final_score
        cand['special_notes'] = special_notes
        cand['hard_fail'] = hard_fail
        
        # 补充详情页信息
        cand['detail'] = {
            'facing': prop_detail.get('facing', ''),
            'hall_facing': prop_detail.get('hall_facing', ''),
            'hall_type': prop_detail.get('hall_type', ''),
            'floor': prop_detail.get('floor_current', ''),
            'floor_total': prop_detail.get('floor_total', 0),
            'floor_high': prop_detail.get('floor_high', False),
            'has_parking': prop_detail.get('has_parking'),
            'decoration': prop_detail.get('decoration', ''),
            'building_year': prop_detail.get('building_year', ''),
            'street_facing': prop_detail.get('street_facing', False),
        }
        
        # 更新推荐理由（补充详情页信息）
        detail_parts = []
        if prop_detail.get('facing'):
            detail_parts.append(f"朝向{prop_detail['facing']}")
        if prop_detail.get('hall_type'):
            detail_parts.append(prop_detail['hall_type'])
        if prop_detail.get('floor_current') and prop_detail.get('floor_total'):
            detail_parts.append(f"{prop_detail['floor_current']}/{prop_detail['floor_total']}层")
        if prop_detail.get('decoration'):
            detail_parts.append(prop_detail['decoration'])
        if prop_detail.get('building_year'):
            detail_parts.append(f"{prop_detail['building_year']}年建成")
        if special_notes:
            detail_parts.append(' | '.join(special_notes))
        
        if detail_parts:
            cand['reason'] = cand.get('reason', '') + '；' + '，'.join(detail_parts)
        
        final_matches.append(cand)
    
    # 按最终得分排序（硬失败的排最后）
    final_matches.sort(key=lambda x: (x.get('hard_fail', False), -float(x.get('match_score', 0))))
    
    return final_matches[:limit], excluded_hard_fail, candidates


def format_match_result(matches: list, client_name: str, excluded_hard_fail: list = None, needs_profile: dict = None) -> str:
    """格式化输出匹配结果"""
    raw_special = needs_profile.get('special_requirements', []) if needs_profile else []
    special_reqs = [_normalize_special_requirement(r) for r in raw_special]
    special_desc = '、'.join([r['req'] for r in special_reqs]) if special_reqs else '无'
    
    if not matches:
        return f"为 {client_name} 筛选后没有符合条件（特别是特殊要求）的房源"
    
    lines = [f"为 {client_name} 推荐 Top{len(matches)}："]
    lines.append(f"（特殊要求：{special_desc}）")
    lines.append("")
    
    for i, m in enumerate(matches, 1):
        reason = m.get('reason', '暂无理由')
        notes = m.get('special_notes', [])
        
        lines.append(f"[{i}] {m.get('community')}")
        lines.append(f"    板块:{m.get('plate')} | 房型:{m.get('layout')} | {m.get('area')}平")
        lines.append(f"    挂牌:{m.get('price')}万 | 估算:{m.get('est_price')}万 | [{m.get('price_zone')}]")
        lines.append(f"    理由: {reason}")
        if notes:
            lines.append(f"    提示: {' | '.join(notes)}")
        lines.append(f"    链接:{m.get('url')}")
        lines.append("")
    
    # 显示因硬性要求被排除的房源
    if excluded_hard_fail:
        lines.append(f"\n⚠️ 以下{len(excluded_hard_fail)}套因硬性要求未满足被排除：")
        for m in excluded_hard_fail[:5]:
            lines.append(f"  - {m.get('community')} ({m.get('plate')}) | {m.get('layout')} | {m.get('price')}万")
            lines.append(f"    原因: {' | '.join(m.get('special_notes', []))}")
    
    return '\n'.join(lines)


def cmd_client_recommend_with_details(args: argparse.Namespace) -> tuple[dict, int]:
    """客户房源精准推荐 — 自动提取需求 + 详情页 + 硬性要求排除"""
    import argparse
    from utils.cache import ensure_cache
    from property.match import resolve_single_client, client_brief, build_client_preferences_summary
    
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
    
    # 精准匹配（含详情页 + 硬性要求排除）
    final_matches, excluded_hard_fail, all_candidates = match_with_details(
        client=client,
        properties=cache.get("properties", []),
        needs_profile=needs_profile,
        limit=getattr(args, 'final_limit', 5),
    )
    
    status = "success" if final_matches else "no_recommendation"
    message = (
        f"已为 {client.get('name')} 完成精准匹配（含详情页分析 + 硬性要求排除）。"
        if final_matches
        else f"已完成精准匹配，但暂时没有足够把握直接推荐给 {client.get('name')} 的房源。"
    )
    
    return {
        "status": status,
        "command": "client-recommend-with-details",
        "query": args.query,
        "client": client_brief(client),
        "client_preferences": build_client_preferences_summary(client),
        "needs_extraction": needs_info,
        "message": message,
        "summary": {
            "candidate_count": len(all_candidates),
            "recommended_count": len(final_matches),
            "hard_fail_count": len(excluded_hard_fail),
        },
        "excluded_hard_fail": [{
            "house_id": m.get("house_id"),
            "community": m.get("community"),
            "plate": m.get("plate"),
            "layout": m.get("layout"),
            "price": m.get("price"),
            "excluded_reason": m.get("excluded_reason"),
            "special_notes": m.get("special_notes", []),
        } for m in excluded_hard_fail[:10]],
        "final_recommendations": final_matches,
    }, 0


if __name__ == "__main__":
    from utils.cache import ensure_cache
    
    c = ensure_cache()
    clients = c.get('clients', [])
    props = c.get('properties', [])
    
    # 找刘先生微信
    client = None
    for cl in clients:
        if cl.get('row') == 12:
            client = cl
            break
    
    # 新格式：加权特殊要求
    needs_profile = {
        'min_rooms': 3,
        'max_rooms': 4,
        'area_min': 120,
        'area_max': 180,
        'special_requirements': [
            {'req': '不要临街', 'weight': 1.0, 'level': 'hard'},
            {'req': '含车位', 'weight': 0.6, 'level': 'medium'},
            {'req': '采光好', 'weight': 0.3, 'level': 'soft'},
        ],
    }
    
    client['district'] = '长宁'
    client['budget'] = 1500.0
    
    print(f"匹配中（客户:{client.get('name')} | 区域:{client.get('district')} | 预算:{client.get('budget')}万）")
    print(f"需求：{needs_profile}")
    print()
    
    matches, all_candidates = match_with_details(client, props, needs_profile=needs_profile, limit=5)
    
    print(f"匹配结果：{len(matches)}套（从{len(all_candidates)}套候选中）")
    print()
    
    output = format_match_result(matches, client.get('name'), needs_profile)
    print(output)
