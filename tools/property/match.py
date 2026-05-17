# -*- coding: utf-8 -*-
"""房源匹配功能"""

import argparse
import re
from typing import Any

import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from utils.cache import ensure_cache
from utils.helpers import clean_text


# 区域 → 板块 映射（完整版）
DISTRICT_PLATE_MAP = {
    '长宁': ['天山', '中山公园', '古北', '虹桥', '西郊', '新华路', '仙霞', '北新泾', '镇宁路'],
    '普陀': ['长风', '长寿路', '武宁', '长征', '真如', '光新', '真光', '中远两湾城', '万里', '桃浦', '曹杨', '甘泉宜川'],
    '闵行': ['金虹桥', '金汇', '古美', '静安新城', '龙柏', '七宝', '华漕', '莘闵别墅', '马桥', '春申', '颛桥', '老闵行', '闵浦', '梅陇', '浦江', '航华', '吴泾', '莘庄南广场', '莘庄北广场'],
    '静安': ['南京西路', '江宁路', '曹家渡', '西藏北路', '静安寺', '大宁', '不夜城', '苏河湾', '闸北公园', '永和', '阳城', '彭浦'],
    '徐汇': ['徐家汇', '田林', '徐汇滨江', '漕河泾', '斜土路', '龙华', '长桥', '建国西路', '康健', '上海南站', '华泾', '华东理工', '衡山路', '万体馆', '植物园'],
    '虹口': ['临平路', '北外滩', '江湾镇', '鲁迅公园', '凉城', '曲阳', '四川北路'],
    '杨浦': ['东外滩', '周家嘴路', '五角场', '新江湾城', '黄兴公园', '控江路', '鞍山', '中原'],
    '浦东': ['陆家嘴', '联洋', '碧云', '花木', '梅园', '南码头', '杨思前滩', '源深', '潍坊', '洋泾', '张江', '北蔡', '唐镇', '杨东', '三林', '世博', '金桥', '金杨', '塘桥', '御桥', '高行', '外高桥', '宣桥'],
    '嘉定': ['南翔', '嘉定新城', '丰庄', '江桥', '马陆', '嘉定老城', '华亭', '菊园新区', '安亭', '太仓', '外冈', '新成路', '徐行'],
    '青浦': ['徐泾', '赵巷', '白鹤', '重固', '华新', '金泽', '昆山', '练塘', '夏阳', '香花桥', '盈浦', '朱家角'],
    '黄浦': ['打浦桥', '董家渡', '黄浦滨江', '淮海中路', '老西门', '南京东路', '蓬莱公园', '人民广场', '世博滨江', '五里桥', '新天地', '豫园'],
}

ALL_PLATES = set()
for plates in DISTRICT_PLATE_MAP.values():
    ALL_PLATES.update(plates)

# 板块 → 地铁线路 映射（用于过滤地铁线路需求）
# 上海地铁 2 号线沿线主要板块：徐泾东、虹桥火车站、虹桥2航站楼、虹桥1航站楼、龙溪路、龙柏新村、紫藤路、航中路、北新泾、淞虹路、福泉路、中山公园、江苏路、静安寺、南京西路、人民广场、陆家嘴、世纪大道、上海科技馆、世纪公园、龙阳路、张江高科
PLATE_SUBWAY_MAP = {
    '天山': [2],
    '中山公园': [2, 3, 4],
    '江苏路': [2, 11],
    '静安寺': [2, 7, 14],
    '南京西路': [2, 12, 13],
    '人民广场': [1, 2, 8],
    '陆家嘴': [2],
    '世纪大道': [2, 4, 6, 9],
    '世纪公园': [2],
    '龙阳路': [2, 7, 16],
    '张江高科': [2],
    '北新泾': [2],
    '淞虹路': [2],
    '虹桥火车站': [2, 10, 17],
    '虹桥2航站楼': [2, 10],
    '徐泾东': [2, 17],
    '镇宁路': [2, 7, 14],
    '新华路': [3, 4],
    '古北': [10, 15],
    '仙霞': [10],
    '虹桥': [10, 15],
    '西郊': [],
    '长寿路': [7, 13],
    '武宁': [3, 4, 7, 11, 13, 14],
    '长风': [13, 15],
    '曹家渡': [7, 11, 13, 14],
    '江宁路': [7, 12, 13],
    '淮海中路': [1, 10, 12, 13, 14],
    '新天地': [10, 13],
    '打浦桥': [4, 9, 12, 13],
    '嘉善路': [9, 12],
    '陕西南路': [1, 10, 12],
    '常熟路': [1, 7, 10],
    '交通大学': [10, 11],
    '隆德路': [11, 13],
    '曹杨路': [3, 4, 11],
    '枫桥路': [11],
    '真如': [11, 14, 15],
    '上海西站': [11, 15],
    '李子园': [15],
    '上海南站': [1, 3, 15],
    '石龙路': [3],
    '上海体育馆': [1, 4],
    '漕溪路': [1, 3, 4],
    '宜山路': [3, 4, 9, 15],
    '虹桥路': [3, 4, 10, 15],
    '桂林路': [9, 15],
    '漕宝路': [1, 12],
    '田林': [12, 15],
    '虹漓路': [12],
    '虹梅路': [9, 12],
    '顾戴路': [12],
    '东兰路': [12],
    '漕河泾开发区': [9, 12],
    '桂平路': [9, 12],
    '星中路': [9],
    '合川路': [9],
    '漕河泾': [9],
    '七宝': [9],
    '中春路': [9],
    '松江大学城': [9],
    '徐家汇': [1, 9, 11],
    '临平路': [4],
    '北外滩': [4, 12],
    '江湾镇': [3, 10],
    '鲁迅公园': [3, 8],
    '凉城': [3],
    '曲阳': [8, 10],
    '四川北路': [10],
    '东外滩': [12],
    '周家嘴路': [8, 12],
    '五角场': [10],
    '新江湾城': [10],
    '黄兴公园': [8],
    '控江路': [8, 10],
    '鞍山': [8, 10],
    '中原': [8],
    '联洋': [9],
    '碧云': [9],
    '花木': [2, 7],
    '梅园': [4, 6, 9],
    '南码头': [6, 7],
    '杨思前滩': [6, 8],
    '源深': [6],
    '潍坊': [4, 6, 9],
    '洋泾': [6],
    '张江': [2],
    '北蔡': [7, 13],
    '唐镇': [2],
    '杨东': [4],
    '三林': [6, 8, 11],
    '世博': [7, 8, 13],
    '金桥': [6],
    '金杨': [6],
    '塘桥': [4, 6],
    '御桥': [11],
    '高行': [6],
    '外高桥': [6],
    '宣桥': [16],
    '南翔': [11],
    '嘉定新城': [11],
    '丰庄': [13],
    '江桥': [13],
    '马陆': [11],
    '嘉定老城': [11],
    '华亭': [],
    '菊园新区': [11],
    '安亭': [11],
    '太仓': [],
    '外冈': [],
    '新成路': [],
    '徐行': [],
    '徐泾': [2, 17],
    '赵巷': [17],
    '白鹤': [],
    '重固': [],
    '华新': [],
    '金泽': [],
    '昆山': [],
    '练塘': [],
    '夏阳': [],
    '香花桥': [],
    '盈浦': [],
    '朱家角': [17],
    '徐家汇': [1, 9, 11],
    '田林': [12, 15],
    '徐汇滨江': [11, 12],
    '漕河泾': [9, 12],
    '斜土路': [4, 7, 9, 12],
    '龙华': [11, 12],
    '长桥': [15],
    '建国西路': [7, 10],
    '康健': [1, 3],
    '上海南站': [1, 3, 15],
    '华泾': [15],
    '华东理工': [1, 15],
    '衡山路': [1, 7, 10],
    '万体馆': [1, 3, 4, 9, 11, 12],
    '植物园': [],
    '临平路': [4],
    '北外滩': [4, 12],
    '江湾镇': [3, 10],
    '鲁迅公园': [3, 8],
    '凉城': [3],
    '曲阳': [8, 10],
    '四川北路': [10],
    '东外滩': [12],
    '周家嘴路': [8, 12],
    '五角场': [10],
    '新江湾城': [10],
    '黄兴公园': [8],
    '控江路': [8, 10],
    '鞍山': [8, 10],
    '中原': [8],
    '打浦桥': [4, 9, 12, 13],
    '董家渡': [9],
    '黄浦滨江': [9],
    '淮海中路': [1, 10, 12, 13, 14],
    '老西门': [8, 10],
    '南京东路': [2, 10],
    '蓬莱公园': [4, 6, 8],
    '人民广场': [1, 2, 8],
    '世博滨江': [7, 8, 13],
    '五里桥': [4, 8, 9, 13],
    '新天地': [10, 13],
    '豫园': [10],
}


def extract_plate_name(plate_field: str) -> str:
    """从板块字段提取板块名（去掉末尾的12位房源ID）
    格式如：'古北107115355685' -> '古北'
    """
    if not plate_field:
        return ''
    return re.sub(r'\d{12}$', '', str(plate_field)).strip()


def is_district_match(client_district: str, prop_plate: str) -> bool:
    """判断房源是否在客户的目标区域内（仅基于板块名匹配）
    
    支持区级和板块级匹配：
    - 客户说"长宁" -> 匹配任意板块属于长宁区9个板块的房源
    - 客户说"古北" -> 匹配板块名为古北的房源
    """
    cd = clean_text(client_district)
    pp = extract_plate_name(prop_plate) if prop_plate else ''
    
    if not cd:
        return True
    
    # 情况1：客户输入的是区名
    if cd in DISTRICT_PLATE_MAP:
        if pp in DISTRICT_PLATE_MAP.get(cd, []):
            return True
        return False
    
    # 情况2：客户输入的是板块名
    if pp == cd:
        return True
    
    return False


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
    from client.search import search_clients
    matches = search_clients(clients, query)
    if not matches:
        return {"status": "not_found", "query": query, "message": f"未找到客户：{query}"}
    if len(matches) > 1:
        return {
            "status": "ambiguous", "query": query, "match_count": len(matches),
            "candidates": [{"row": m["record"]["row"], "name": m["record"]["name"]} for m in matches[:5]],
        }
    return {"status": "success", "query": query, "client": matches[0]["record"]}


def match_properties_for_client(client: dict[str, Any], properties: list[dict[str, Any]], limit: int = 10, needs_profile: dict = None, weights: dict = None, **kwargs) -> tuple[list[dict[str, Any]], list[str]]:
    """为客戶匹配房源
    
    预算浮动逻辑：
    - 核心区 ±10%：最佳匹配
    - 弹性区 -20%~+20%：可接受
    - 极限下浮 -20% 以下：仅高房源分才推荐
    - 超限 +20% 以上：不推荐
    - 挂牌价可能谈下 5%，计算时按 *0.95 估算
    
    Args:
        weights: 自定义权重 {"price": 0.7, "room": 0.3}
    """
    matches = []
    excluded = []
    
    client_district = clean_text(client.get("district", ""))
    client_budget = client.get("budget", "") or 0
    try:
        client_budget = float(client_budget)
    except:
        client_budget = 0
    
    # 预算浮动阈值（用户确认版）
    CORE_LOW = 0.90    # 核心下浮 10%
    CORE_HIGH = 1.20   # 核心上浮 20%
    CORE_LOW_BELOW = 0.80  # 极限下浮 20%（低于此值仅高分房保留）
    OVER_LIMIT = 1.20 # 超限上浮 20%（超出直接排除）
    NEGOTIATION_FACTOR = 0.95  # 挂牌价可谈估算系数
    
    # 从 needs_profile 获取精准需求（由LLM提取）
    min_rooms = int(needs_profile.get('min_rooms', 0)) if needs_profile else 0
    max_rooms = int(needs_profile.get('max_rooms', 99)) if needs_profile else 99
    area_min = float(needs_profile.get('area_min', 0)) if needs_profile else 0
    area_max = float(needs_profile.get('area_max', 9999)) if needs_profile else 9999
    
    # 新增：意向板块、排除板块、意向小区
    preferred_plates = needs_profile.get('plates', []) if needs_profile else []
    excluded_plates = needs_profile.get('excluded_plates', []) if needs_profile else []
    preferred_communities = needs_profile.get('preferred_communities', []) if needs_profile else []
    
    # 新增：楼层偏好、车位需求、朝向
    floor_preference = needs_profile.get('floor_preference') if needs_profile else None
    needs_parking = needs_profile.get('needs_parking', False) if needs_profile else False
    orientation = needs_profile.get('orientation') if needs_profile else None
    
    # 新增：地铁线路需求
    required_subway_lines = needs_profile.get('subway_lines', []) if needs_profile else []
    
    # 解析已推送房源（降分避免重复推荐）
    pushed_houses_raw = client.get('pushed_houses', '') or ''
    pushed_house_ids = set()
    if pushed_houses_raw:
        for hid in pushed_houses_raw.split('#'):
            hid = hid.strip()
            if hid:
                if hid.endswith('.0'):
                    hid = hid[:-2]
                pushed_house_ids.add(hid)
    
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
        
        # 新增：楼层偏好过滤
        prop_floor = prop.get("floor", "")
        if floor_preference and not _is_floor_match(prop_floor, floor_preference):
            continue  # 楼层不符合偏好，直接排除
        
        # 新增：地铁线路过滤
        if required_subway_lines:
            prop_plates = [prop_plate_name] if prop_plate_name else []
            # 如果板块在映射中，检查是否有匹配的地铁线路
            has_required_line = False
            for plate in prop_plates:
                plate_lines = PLATE_SUBWAY_MAP.get(plate, [])
                for req_line in required_subway_lines:
                    if req_line in plate_lines:
                        has_required_line = True
                        break
                if has_required_line:
                    break
            if not has_required_line:
                continue  # 不满足地铁线路需求，直接排除
        
        try:
            raw_price = float(prop_price)
        except:
            continue
        
        est_price = raw_price * NEGOTIATION_FACTOR
        
        # 超限排除：估算成交价 > 预算 * 120%
        if client_budget > 0 and est_price > client_budget * OVER_LIMIT:
            excluded.append(prop.get("house_id", ""))
            continue
        
        # 价格偏离度
        if client_budget > 0:
            price_deviation = (raw_price - client_budget) / client_budget
        else:
            price_deviation = 0
        
        # 极限下浮（比预算低20%以上）：只有高房源分才保留
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
            # 有精准房型需求时（从跟进提取），得分按偏离程度
            room_diff = abs(rooms - (min_rooms + max_rooms) / 2)
            room_score = max(0, 1.0 - room_diff * 0.3)
            room_priority = None  # 精准需求不使用优先级逻辑
        elif client_primary > 0:
            # 使用户型优先级逻辑
            if rooms == client_primary:
                # 主力房型：高分
                room_score = 1.0
                room_priority = "primary"
            elif client_secondary and rooms == client_secondary:
                # 备选房型：降分，说明面积大但品质可能不如主力
                room_score = 0.6
                room_priority = "secondary"
            else:
                # 其他房型：按偏离程度计分
                room_diff = abs(rooms - client_primary)
                room_score = max(0, 0.5 - room_diff * 0.2)
                room_priority = None
        elif client_rooms_raw > 0:
            room_diff = abs(rooms - client_rooms_raw)
            room_score = max(0, 1.0 - room_diff * 0.3)
            room_priority = None
        else:
            room_score = 0.5
            room_priority = None
        
        # 可配置权重（默认价格70% + 房型30%）
        price_w = weights.get('price', 0.7) if weights else 0.7
        room_w = weights.get('room', 0.3) if weights else 0.3
        total_score = price_score * price_w + room_score * room_w
        
        # 意向小区加分（客户明确关注的小区）
        community_bonus = 0.0
        prop_community = prop.get('community', '') or ''
        if preferred_communities:
            for comm in preferred_communities:
                if comm in prop_community:
                    community_bonus = 0.3  # 意向小区加分30%
                    break
        total_score += community_bonus
        
        # 已推送房源降分（避免重复推荐无反馈房源）
        prop_house_id = prop.get('house_id', '') or ''
        if prop_house_id.endswith('.0'):
            prop_house_id = prop_house_id[:-2]
        if prop_house_id in pushed_house_ids:
            total_score -= 0.3  # 已推送降分
        
        # 生成推荐理由
        reason = _generate_reason(
            prop=prop,
            client=client,
            price_deviation=price_deviation,
            rooms=rooms,
            price_zone=_get_price_zone(price_deviation),
            needs_profile=needs_profile,
            room_priority=room_priority,
        )
        
        matches.append({
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
            "room_priority": room_priority,  # 新增字段
            "reason": reason,
        })
    
    matches.sort(key=lambda x: float(x.get("match_score", 0)), reverse=True)
    return matches[:limit], excluded[:limit * 2]


def _parse_rooms(layout: Any) -> int:
    """从房型字符串解析室数，支持多种格式
    
    支持格式：
    - '3室2厅' → 3
    - '3-2-120' → 3
    - '三室两厅' → 3
    - '3室2厅-120平' → 3
    - '3室' → 3
    """
    if not layout:
        return 0
    
    layout_str = str(layout).strip()
    
    # 中文数字映射
    cn_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8}
    
    # 优先匹配 "X室" 或 "X室X厅" 格式
    import re
    match = re.search(r'([\d一二三四五六七八九])\s*室', layout_str)
    if match:
        first = match.group(1)
        if first in cn_map:
            return cn_map[first]
        return int(first)
    
    # 回退：按 '-' 分割取第一部分
    parts = layout_str.split("-")
    try:
        return int(parts[0].strip())
    except:
        return 0

def _parse_rooms_priority(rooms_str: str) -> tuple[int, int | None]:
    """解析客户户型优先级标注
    
    格式："主力.备选" 如 "2.3" 表示两房主力、三房备选
    
    返回：(primary_room, secondary_room)
    - primary_room: 主力房型（优先匹配，预算舒适）
    - secondary_room: 备选房型（次优，面积大但品质可能降）
    
    示例：
    - "2.3" → (2, 3)  两房主力，三房理想但预算紧
    - "3.4" → (3, 4)  三房主力，四房理想但预算紧
    - "4.3" → (4, 3)  四房目标但预算紧，三房更现实
    - "3.2" → (3, 2)  三房目标但预算紧，两房更现实
    - "3"  → (3, None) 单一房型需求
    """
    if not rooms_str:
        return (0, None)
    
    rooms_str = str(rooms_str).strip()
    
    # 尝试解析 "X.Y" 格式
    if '.' in rooms_str:
        parts = rooms_str.split('.')
        try:
            primary = int(parts[0].strip())
            secondary = int(parts[1].strip()) if len(parts) > 1 else None
            return (primary, secondary)
        except:
            pass
    
    # 单一房型
    try:
        return (int(rooms_str), None)
    except:
        return (0, None)


def _parse_floor_level(floor_str: str) -> tuple[str | None, bool]:
    """从楼层字符串解析楼层级别
    
    支持格式：
    - '高/18' → ('高', True)
    - '中/6' → ('中', True)
    - '低/4' → ('低', True)
    - '高/24 层' → ('高', True)
    - '高/4' → (None, False)  # 数据异常：总层数<=6 时不可能是高层
    
    返回：(楼层级别，数据是否可信)
    """
    if not floor_str:
        return (None, False)
    
    floor_str = str(floor_str).strip()
    
    # 匹配 "X/Y" 格式
    match = re.search(r'([低中高])/(\d+)', floor_str)
    if match:
        level = match.group(1)
        total_floors = int(match.group(2))
        
        # 数据验证：总层数 <= 6 时，不可能是"高"楼层
        if total_floors <= 6 and level == '高':
            return (None, False)  # 数据异常
        
        return (level, True)
    
    return (None, False)


def _is_floor_match(prop_floor: str, client_floor_pref: str | None) -> bool:
    """检查房源楼层是否符合客户偏好
    
    Args:
        prop_floor: 房源楼层字符串，如 '高/18'
        client_floor_pref: 客户楼层偏好，如 '中高楼层'
    
    Returns:
        True 表示匹配，False 表示不匹配
    """
    if not client_floor_pref:
        return True  # 无偏好则全部匹配
    
    prop_level, data_reliable = _parse_floor_level(prop_floor)
    
    # 数据不可靠时：如果客户有明确楼层偏好，则排除（避免推荐错误数据）
    if not data_reliable or not prop_level:
        return False  # 数据异常，排除
    
    # 解析客户偏好
    if '中高楼层' in client_floor_pref or '高层' in client_floor_pref:
        return prop_level in ['高', '中']
    elif '低楼层' in client_floor_pref or '底层' in client_floor_pref:
        return prop_level in ['低']
    
    return True  # 未知偏好则保留


def _get_price_zone(deviation: float) -> str:
    if deviation < -0.2:
        return "极限低价"
    elif deviation < -0.1:
        return "超值低价"
    elif deviation <= 0.2:
        return "核心区间"
    else:
        return "超出可谈范围"


def _generate_reason(prop: dict, client: dict, price_deviation: float, rooms: int, price_zone: str, needs_profile: dict = None, room_priority: str = None) -> str:
    """生成推荐理由"""
    reasons = []
    
    raw_price = float(prop.get('price', 0) or 0)
    est_price = raw_price * 0.95
    client_budget = float(client.get('budget', 0) or 0)
    if client_budget > 0:
        if price_deviation <= 0:
            reasons.append(f"总价{prop.get('price')}万（估算{est_price:.0f}万），在预算范围内")
        else:
            reasons.append(f"总价{prop.get('price')}万（估算{est_price:.0f}万），超出预算{abs(price_deviation)*100:.0f}%，但可谈")
    
    layout = prop.get('layout', '')
    if layout:
        # 户型优先级说明
        if room_priority == "primary":
            reasons.append(f"{layout}（{rooms}室），主力户型，预算内品质更优")
        elif room_priority == "secondary":
            reasons.append(f"{layout}（{rooms}室），备选户型，面积大但品质可能不及主力户型")
        else:
            reasons.append(f"{layout}（{rooms}室）")
    
    area = float(prop.get('area', 0) or 0)
    if area > 0:
        if needs_profile and needs_profile.get('area_min') and needs_profile.get('area_max'):
            reasons.append(f"面积{area}平，在需求{needs_profile['area_min']}-{needs_profile['area_max']}平范围内")
        else:
            reasons.append(f"面积{area}平")
    
    plate = extract_plate_name(prop.get('plate', ''))
    if plate:
        reasons.append(f"位于{plate}板块")
    
    score = float(prop.get('score', 0) or 0)
    if score >= 8.5:
        reasons.append(f"链家房源分{score}，优质")
    elif score >= 7.5:
        reasons.append(f"链家房源分{score}")
    
    return "；".join(reasons)


def build_client_preferences_summary(client: dict[str, Any]) -> dict[str, Any]:
    """构建客户偏好摘要"""
    return {
        "district": client.get("district"),
        "budget": client.get("budget"),
        "rooms": client.get("rooms"),
    }


def cmd_client_match_properties(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """客户房源匹配 — 自动提取需求后匹配"""
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
            # 将需求提取结果转换为匹配函数需要的格式
            needs_profile = {
                'min_rooms': needs_info.get('min_rooms', 0),
                'max_rooms': needs_info.get('max_rooms', 99),
                'area_min': needs_info.get('area_min', 0) or 0,
                'area_max': needs_info.get('area_max', 9999) or 9999,
                'special_requirements': needs_info.get('special_requirements', []),
                # 新增：楼层偏好、车位需求、朝向
                'floor_preference': needs_info.get('floor_preference'),
                'needs_parking': needs_info.get('needs_parking', False),
                'orientation': needs_info.get('orientation'),
                # 新增：地铁线路需求
                'subway_lines': needs_info.get('subway_lines', []),
            }
    except Exception as e:
        needs_info = {"status": "error", "message": str(e)}
    
    # 可配置权重（默认价格70% + 房型30%）
    weights = None
    if getattr(args, 'weights', None):
        try:
            import json as _json
            weights = _json.loads(args.weights)
        except:
            pass
    
    matches, excluded = match_properties_for_client(
        client=client,
        properties=cache.get("properties", []),
        limit=args.limit,
        needs_profile=needs_profile,
        weights=weights,
        include_recommended=getattr(args, 'include_recommended', False),
    )
    
    return {
        "status": "success",
        "command": "client-match-properties",
        "query": args.query,
        "client": client_brief(client),
        "client_preferences": build_client_preferences_summary(client),
        "needs_extraction": needs_info,
        "excluded_recommended_count": len(excluded),
        "excluded_recommended_ids": excluded[:20],
        "properties": matches,
    }, 0
