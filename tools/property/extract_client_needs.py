# -*- coding: utf-8 -*-
"""客户需求提取 - 简化修复版"""

import sys
import json
import os
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from utils.cache import ensure_cache
from utils.helpers import clean_text


def get_client_followups_from_cache(row: int, limit: int = 20) -> list[dict] | None:
    """从主缓存读取跟进记录"""
    main_cache_file = r'C:\Users\Huawei\.openclaw\workspace-tuantuan\runtime\tuantuan_cache.json'
    if not os.path.exists(main_cache_file):
        return None
    
    try:
        with open(main_cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查缓存是否在1小时内
        ts_str = data.get('generated_at', '')
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age_seconds = (datetime.now(timezone.utc) - ts).total_seconds()
                if age_seconds > 3600:
                    return None
            except:
                pass
        
        # 从主缓存中找到对应客户
        clients = data.get('clients', [])
        for client in clients:
            if client.get('row') == row:
                followups = client.get('followups', [])[-limit:]
                return followups
        return None
    except:
        return None


def extract_needs_from_followups(followups: list[dict]) -> dict:
    """从跟进记录提取需求（简化版）"""
    # 合并跟进记录文本
    text = "\n".join([
        f"[{f.get('date', '')}] {f.get('content', '')}"
        for f in followups if f.get('content')
    ])
    
    # 提取板块关键词
    plates = []
    excluded_plates = []
    preferred_communities = []
    
    # 板块关键词
    plate_keywords = ["天山", "中山公园", "新华路", "长寿路", "静安寺", "古北", "北新泾", "仙霞", "虹桥", "西郊", "镇宁路", "威宁路", "江宁路", "武宁路"]
    
    # 排除关键词
    exclude_keywords = ["太远", "不要", "不考虑", "不喜欢"]
    
    # 小区关键词
    community_keywords = ["仁恒", "天山河畔", "虹桥万博", "苏堤春晓", "河滨花园"]
    
    for kw in plate_keywords:
        if kw in text:
            # 检查是否被排除
            context = text[max(0, text.find(kw)-20):text.find(kw)+20]
            if any(ex in context for ex in exclude_keywords):
                excluded_plates.append(kw)
            else:
                plates.append(kw)
    
    for kw in community_keywords:
        if kw in text:
            preferred_communities.append(kw)
    
    # 提取预算
    import re
    budget_match = re.search(r'(\d{3,4})万', text)
    budget_max = int(budget_match.group(1)) if budget_match else None
    
    # 提取面积
    area_min, area_max = None, None
    area_matches = re.findall(r'(\d{2,3})\s*平', text)
    if area_matches:
        areas = [int(a) for a in area_matches]
        area_min = min(areas)
        area_max = max(areas)
    
    # 提取楼层偏好
    floor_pref = None
    if "中高楼层" in text or "高层" in text:
        floor_pref = "中高楼层"
    elif "低楼层" in text or "底层" in text:
        floor_pref = "低楼层"
    
    # 提取车位需求
    needs_parking = "车位" in text
    
    # 提取朝向
    orientation = None
    if "南北通" in text:
        orientation = "南北通"
    elif "朝南" in text:
        orientation = "朝南"
    
    # 提取地铁线路需求
    subway_lines = []
    subway_pattern = re.findall(r'(\d+)号线', text)
    for line in subway_pattern:
        try:
            subway_lines.append(int(line))
        except:
            pass
    
    return {
        "plates": plates,
        "excluded_plates": excluded_plates,
        "preferred_communities": preferred_communities,
        "budget_max": budget_max,
        "area_min": area_min,
        "area_max": area_max,
        "floor_preference": floor_pref,
        "needs_parking": needs_parking,
        "orientation": orientation,
        "subway_lines": subway_lines,
        "confidence": 0.8 if plates else 0.5,
        "extraction_mode": "keyword",
    }


def extract_client_needs(client_row: int, client_name: str = None) -> dict:
    """主入口：提取客户需求"""
    followups = get_client_followups_from_cache(client_row, limit=20)
    
    # 缓存不存在或已过期，自动触发刷新
    if followups is None:
        import subprocess
        try:
            subprocess.run(
                ['cmd', '/c', r'C:\Users\Huawei\.openclaw\workspace-tuantuan\tools\RUN_TUANTUAN_qidong.cmd', 'refresh'],
                capture_output=True, timeout=120
            )
        except:
            pass
        followups = get_client_followups_from_cache(client_row, limit=20)
    
    if not followups:
        return {
            "status": "no_followups",
            "message": f"行{client_row}没有找到跟进记录",
            "client_row": client_row,
        }
    
    # 获取客户表里的基础信息
    cache = ensure_cache()
    default_budget = None
    client_rooms = None
    client_district = None
    for cl in cache.get('clients', []):
        if cl.get('row') == client_row:
            default_budget = cl.get('budget')
            client_rooms = cl.get('rooms')
            client_district = cl.get('district')
            if not client_name:
                client_name = cl.get('name', client_name)
            break
    
    needs = extract_needs_from_followups(followups)
    
    # 合并客户表基础信息
    needs['client_row'] = client_row
    needs['client_name'] = client_name
    needs['district'] = client_district
    needs['rooms'] = client_rooms
    if not needs.get('budget_max') and default_budget:
        needs['budget_max'] = float(default_budget) if default_budget else None
    needs['followup_count'] = len(followups)
    needs['status'] = 'success'
    
    return needs


def pretty_print_needs(needs: dict) -> str:
    """格式化输出需求摘要"""
    lines = [
        f"客户：{needs.get('client_name')}（行{needs.get('client_row')}）",
        f"提取模式：{needs.get('extraction_mode', 'unknown')}",
        f"置信度：{needs.get('confidence', 0):.0%}",
        "",
        f"行政区：{needs.get('district', '未明确')}",
        f"意向板块：{', '.join(needs.get('plates', []) or ['未明确'])}",
        f"排除板块：{', '.join(needs.get('excluded_plates', []) or ['无'])}",
        f"意向小区：{', '.join(needs.get('preferred_communities', []) or ['无'])}",
        f"预算：{needs.get('budget_max') or '未明确'}万",
        f"面积：{needs.get('area_min') or '未明确'} ~ {needs.get('area_max') or '未明确'}平",
        f"楼层：{needs.get('floor_preference') or '无要求'}",
        f"车位：{'需要' if needs.get('needs_parking') else '未明确'}",
        f"朝向：{needs.get('orientation') or '无要求'}",
    ]
    return '\n'.join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--row", type=int, required=True)
    args = parser.parse_args()
    
    result = extract_client_needs(args.row)
    print(pretty_print_needs(result))
    print()
    print("原始数据：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
