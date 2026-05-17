# -*- coding: utf-8 -*-
"""房源详情页关键信息提取（全面提取+主观过滤）"""
import os
import subprocess
import time
import re
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

CHROME_PATH = r'C:\Users\Huawei\AppData\Local\Google\Chrome\Application\chrome.exe'
USER_PROFILE = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
DEBUG_PORT = 9222


def is_port_active(port: int) -> bool:
    try:
        req = urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=2)
        return len(req.read()) > 0
    except:
        return False


def ensure_automation_chrome() -> str:
    """启动自动化Chrome（使用用户Profile），确保有登录Cookie"""
    if is_port_active(DEBUG_PORT):
        print(f"[INFO] 已有Chrome运行在调试端口{DEBUG_PORT}，复用")
        return str(DEBUG_PORT)
    
    print(f"[INFO] 关闭所有Chrome进程...")
    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
    time.sleep(3)
    
    print(f"[INFO] 启动Chrome自动化浏览器（使用你的日常Profile）...")
    
    cmd = [
        CHROME_PATH,
        f'--remote-debugging-port={DEBUG_PORT}',
        f'--user-data-dir={USER_PROFILE}',
        '--no-first-run',
        '--no-default-browser-check',
        '--no-sandbox',
        '--restore-last-session',
    ]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(10)
    
    if is_port_active(DEBUG_PORT):
        print(f"[INFO] Chrome已启动在调试端口{DEBUG_PORT}")
        return str(DEBUG_PORT)
    else:
        print(f"[WARN] Chrome启动后端口{DEBUG_PORT}未响应")
        return str(DEBUG_PORT)


def close_automation_chrome():
    """自动化完成后不关闭Chrome（保持登录态，供下次复用）"""
    print("[INFO] 保持Chrome运行（下次可复用，无需重新登录）")
    pass


def extract_all_info(text: str) -> dict:
    """从链家内网页面文本中提取所有关键信息"""
    result = {
        'price': '', 'unit_price': '', 'layout': '', 'area': '', 'facing': '',
        'floor_current': '', 'floor_total': 0, 'floor_high': False,
        'street_facing': None, 'has_street_issue': False,
        'decoration': '', 'has_parking': None, 'parking_price': '',
        'building_year': '', 'is_manwu': False, 'is_weiyi': False,
        'has_school_quota': False, 'is_vacant': False, 'has_key': False,
        'no_leakage': None, 'has_grant_area': '',
        'rooms': [], 'hall_area': '', 'hall_facing': '', 'hall_type': '',
        'district': '', 'plate': '', 'property_fee': '', 'building_structure': '',
        'property_years': '', 'ladder_ratio': '', 'building_type': '',
        'heating_type': '', 'elevator': None, 'gas': None,
        'water_type': '', 'electricity_type': '',
        'nearby_school': '', 'school_distance': '',
        'property_score': '', 'maintenance_completeness': '',
        'view_count_7d': '', 'view_count_total': '',
        'broker_followers': '', 'client_followers': '',
        'owner_bottom_price': '', 'owner_expected_price': '',
        'original_price': '', 'transfer_guide_price': '',
        'sale_reason': '', 'household_status': '', 'mortgage_status': '',
        'can_sign_anytime': False, 'expected_cycle': '',
        'property_shared': False, 'contact_is_owner': False, 'marital_status': '',
        'property_tags': [], 'suitable_for': '',
        'broker_comment': {
            'subway_distance': '', 'surroundings': '', 'traffic': '',
            'subjective_claims': [],
        },
        'owner_description': '',
        'price_negotiation': '', 'latest_log': '', 'urgency': '',
    }
    
    # ============ 基础信息 ============
    price_match = re.search(r'(\d+)\s*万', text)
    if price_match:
        result['price'] = price_match.group(1)
    
    unit_match = re.search(r'单价[:\uff1a](\d+)元/平米', text)
    if unit_match:
        result['unit_price'] = unit_match.group(1)
    
    layout_match = re.search(r'户型\s*(\d+-\d+-\d+-\d+)', text)
    if layout_match:
        result['layout'] = layout_match.group(1)
    
    area_match = re.search(r'面积\s*(\d+\.?\d*)平', text)
    if area_match:
        result['area'] = area_match.group(1)
    
    facing_map = {'南': '南', '东南': '东南', '东': '东', '西': '西', '北': '北', '南北': '南北'}
    for kw, val in facing_map.items():
        if f'朝向\n{kw}' in text or f'朝向:\n{kw}' in text or f'朝向 {kw}' in text:
            result['facing'] = val
            break
    
    floor_idx = text.find('楼层\n')
    if floor_idx >= 0:
        segment = text[floor_idx:floor_idx+100]
        floor_match = re.search(r'([高低中一二三四五六七八九十百]+)/\s*(\d+)', segment)
        if floor_match:
            result['floor_current'] = floor_match.group(1)
            result['floor_total'] = int(floor_match.group(2))
            result['floor_high'] = '高' in result['floor_current']
    
    # ============ 嫌恶设施 ============
    if '嫌恶设施' in text:
        idx = text.find('嫌恶设施')
        segment = text[idx:idx+100]
        if '无' in segment:
            result['street_facing'] = False
        elif any(kw in segment for kw in ['临街', '路冲', '加油站', '垃圾站', '庙', '墓']):
            result['has_street_issue'] = True
    
    # ============ 特色信息 ============
    if '装修情况' in text:
        idx = text.find('装修情况')
        segment = text[idx:idx+50]
        if '精装' in segment:
            result['decoration'] = '精装'
        elif '简装' in segment:
            result['decoration'] = '简装'
        elif '毛坯' in segment:
            result['decoration'] = '毛坯'
    
    if '有无车位' in text:
        idx = text.find('有无车位')
        segment = text[idx:idx+100]
        # 注意：'无车位'是'有无车位'的子串，需要特殊处理
        # 先检查是否有'有车位'（排除'无车位'的情况）
        lines = segment.split('\n')
        has_parking_line = False
        for line in lines[1:3]:  # 检查后面2行
            if '有车位' in line and '无车位' not in line:
                has_parking_line = True
                # 提取价格
                pk_match = re.search(r'(\d+)\s*万', line)
                if pk_match:
                    result['parking_price'] = pk_match.group(1)
                break
        result['has_parking'] = has_parking_line
    
    year_match = re.search(r'建成年代[：:]\s*(\d{4})', text)
    if year_match:
        result['building_year'] = year_match.group(1)
    
    if '满五' in text or '满N' in text:
        result['is_manwu'] = True
    if '唯一' in text:
        result['is_weiyi'] = True
    if '有学区名额' in text:
        result['has_school_quota'] = True
    if '空置' in text:
        result['is_vacant'] = True
    if '有钥匙' in text or '钥匙' in text:
        result['has_key'] = True
    if '无漏水表象' in text:
        result['no_leakage'] = True
    if '有赠送' in text:
        grant_match = re.search(r'有赠送[，,：:]\s*(.+)', text)
        if grant_match:
            result['has_grant_area'] = grant_match.group(1).strip()[:50]
    
    # ============ 实勘信息（房间详情） ============
    # 简化正则：匹配 "房间名 面积平米 朝向 窗户类型"
    room_pattern = r'([\u4e00-\u9fa5]+)\s+(\d+(?:\.\d+)?)\s*平米\s*([\u4e00-\u9fa5]+)\s+([\u4e00-\u9fa5]+)'
    for match in re.finditer(room_pattern, text):
        room_name = match.group(1)
        # 过滤掉非房间名称
        if any(kw in room_name for kw in ['单价', '产权', '建筑', '交易', '房屋', '结构', '用途', '类型', '年限', '比例', '权属']):
            continue
        # 只保留真正的房间（包含室/厅/厨/卫/阳台）
        if not any(kw in room_name for kw in ['室', '厅', '厨', '卫', '阳台']):
            continue
        room = {
            'name': room_name,
            'area': match.group(2),
            'facing': match.group(3),
            'window_type': match.group(4),
        }
        result['rooms'].append(room)
        if '客厅' in room['name']:
            result['hall_area'] = room['area']
            result['hall_facing'] = room['facing']
            hf = room['facing']
            if '南' in hf and '北' in hf:
                result['hall_type'] = '南北通'
            elif hf == '南':
                result['hall_type'] = '厅朝南'
            elif hf == '北':
                result['hall_type'] = '厅朝北'
            elif '东' in hf:
                result['hall_type'] = '厅朝东'
            elif '西' in hf:
                result['hall_type'] = '厅朝西'
    
    # ============ 小区信息 ============
    area_match = re.search(r'所在城区[：:]\s*([\u4e00-\u9fa5]+)\s*所属商圈[：:]\s*([\u4e00-\u9fa5]+)', text)
    if area_match:
        result['district'] = area_match.group(1)
        result['plate'] = area_match.group(2)
    
    fee_match = re.search(r'物业费[：:]\s*(\d+\.?\d*)', text)
    if fee_match:
        result['property_fee'] = fee_match.group(1)
    
    struct_match = re.search(r'建筑结构[：:]\s*(.+?)(?:\s|$)', text)
    if struct_match:
        result['building_structure'] = struct_match.group(1).strip()
    
    years_match = re.search(r'产权年限[：:]\s*(\d+)', text)
    if years_match:
        result['property_years'] = years_match.group(1)
    
    ladder_match = re.search(r'梯户比例[：:]\s*(.+?)(?:\s|$)', text)
    if ladder_match:
        result['ladder_ratio'] = ladder_match.group(1).strip()
    
    type_match = re.search(r'建筑类型[：:]\s*(.+?)(?:\s|$)', text)
    if type_match:
        result['building_type'] = type_match.group(1).strip()
    
    heat_match = re.search(r'供暖类型[：:]\s*(.+?)(?:\s|$)', text)
    if heat_match:
        result['heating_type'] = heat_match.group(1).strip()
    
    if '是否有电梯' in text:
        idx = text.find('是否有电梯')
        segment = text[idx:idx+20]
        result['elevator'] = '有' in segment
    
    if '是否有燃气' in text:
        idx = text.find('是否有燃气')
        segment = text[idx:idx+20]
        result['gas'] = '有' in segment
    
    water_match = re.search(r'用水类型[：:]\s*(.+?)(?:\s|$)', text)
    if water_match:
        result['water_type'] = water_match.group(1).strip()
    electricity_match = re.search(r'用电类型[：:]\s*(.+?)(?:\s|$)', text)
    if electricity_match:
        result['electricity_type'] = electricity_match.group(1).strip()
    
    # ============ 教育信息 ============
    school_match = re.search(r'附近小学\s*([\u4e00-\u9fa5\u5e02\u533a\u5c0f\u5b66\u516c\u7acb\u5b66\u6821]+)', text)
    if school_match:
        result['nearby_school'] = school_match.group(1).strip()
    
    dist_match = re.search(r'距离本小区步行距离\s*(\d+)米', text)
    if dist_match:
        result['school_distance'] = dist_match.group(1) + '米'
    
    # ============ 评分和热度 ============
    score_match = re.search(r'房源评分\s*(\d+\.\d+)分', text)
    if score_match:
        result['property_score'] = score_match.group(1)
    
    complete_match = re.search(r'房源维护完成度\s*(\d+)%', text)
    if complete_match:
        result['maintenance_completeness'] = complete_match.group(1) + '%'
    
    view7d_match = re.search(r'近7天带看(\d+)次', text)
    if view7d_match:
        result['view_count_7d'] = view7d_match.group(1)
    
    viewTotal_match = re.search(r'总带看(\d+)次', text)
    if viewTotal_match:
        result['view_count_total'] = viewTotal_match.group(1)
    
    broker_match = re.search(r'(\d+)位经纪人关注', text)
    if broker_match:
        result['broker_followers'] = broker_match.group(1)
    
    client_match = re.search(r'(\d+)位客户关注', text)
    if client_match:
        result['client_followers'] = client_match.group(1)
    
    # ============ 价格信息 ============
    bottom_match = re.search(r'业主最新底价(\d+\.?\d*)万', text)
    if bottom_match:
        result['owner_bottom_price'] = bottom_match.group(1)
    
    expected_match = re.search(r'业主预期价[：:]\s*(\d+\.?\d*)万', text)
    if expected_match:
        result['owner_expected_price'] = expected_match.group(1)
    
    original_match = re.search(r'原购价格[：:]\s*(\d+)万', text)
    if original_match:
        result['original_price'] = original_match.group(1)
    
    guide_match = re.search(r'过户指导价[：:]\s*(\d+\.?\d*)元/平', text)
    if guide_match:
        result['transfer_guide_price'] = guide_match.group(1)
    
    # ============ 业主信息 ============
    reason_match = re.search(r'售房原因[：:]\s*(.+?)(?:\n|$)', text)
    if reason_match:
        result['sale_reason'] = reason_match.group(1).strip()
    
    household_match = re.search(r'户口情况[：:]\s*(.+?)(?:\n|$)', text)
    if household_match:
        result['household_status'] = household_match.group(1).strip()
    
    mortgage_match = re.search(r'抵押情况[：:]\s*(.+?)(?:\n|$)', text)
    if mortgage_match:
        result['mortgage_status'] = mortgage_match.group(1).strip()
    
    if '随时可签' in text:
        result['can_sign_anytime'] = True
    
    cycle_match = re.search(r'期望出售周期[：:]\s*(.+?)(?:\n|$)', text)
    if cycle_match:
        result['expected_cycle'] = cycle_match.group(1).strip()
    
    if '产权是否共有' in text:
        idx = text.find('产权是否共有')
        segment = text[idx:idx+30]
        result['property_shared'] = '是' in segment and '非' not in segment
    
    if '联系人是否为业主' in text:
        idx = text.find('联系人是否为业主')
        segment = text[idx:idx+30]
        result['contact_is_owner'] = '是业主' in segment
    
    marital_match = re.search(r'婚姻状况[：:]\s*(.+?)(?:\n|$)', text)
    if marital_match:
        result['marital_status'] = marital_match.group(1).strip()
    
    # ============ 特色标签 ============
    tags_match = re.search(r'房源特色[：:]\s*(.+)', text)
    if tags_match:
        result['property_tags'] = [t.strip() for t in tags_match.group(1).split() if t.strip()]
    
    suitable_match = re.search(r'适合客户群体[：:]\s*(.+)', text)
    if suitable_match:
        result['suitable_for'] = suitable_match.group(1).strip()[:100]
    
    # ============ 经纪人点评（只提取客观信息） ============
    comment_idx = text.find('经纪人点评')
    if comment_idx >= 0:
        comment_section = text[comment_idx:comment_idx+2000]
        
        subway_match = re.search(r'(\d+)号线.*?(\d+)米', comment_section)
        if subway_match:
            result['broker_comment']['subway_distance'] = f"{subway_match.group(1)}号线{subway_match.group(2)}米"
        
        if '周边配套' in comment_section:
            surround_idx = comment_section.find('周边配套')
            surround_section = comment_section[surround_idx:surround_idx+500]
            next_title = re.search(r'\n(交通出行|户型介绍|小区介绍|核心卖点)', surround_section)
            if next_title:
                surround_section = surround_section[:next_title.start()]
            result['broker_comment']['surroundings'] = surround_section.strip()[:200]
        
        if '交通出行' in comment_section:
            traffic_idx = comment_section.find('交通出行')
            traffic_section = comment_section[traffic_idx:traffic_idx+300]
            next_title = re.search(r'\n(户型介绍|小区介绍|核心卖点|周边配套)', traffic_section)
            if next_title:
                traffic_section = traffic_section[:next_title.start()]
            result['broker_comment']['traffic'] = traffic_section.strip()[:200]
        
        subjective_keywords = ['高档', '品质', '豪华', '尊贵', '顶级', '稀缺', '绝版', '经典']
        for kw in subjective_keywords:
            if kw in comment_section:
                result['broker_comment']['subjective_claims'].append(kw)
    
    # ============ 房主自荐 ============
    owner_idx = text.find('房主自荐')
    if owner_idx >= 0:
        owner_section = text[owner_idx:owner_idx+1000]
        next_title = re.search(r'\n(证件信息|常见问题|实勘信息)', owner_section)
        if next_title:
            owner_section = owner_section[:next_title.start()]
        owner_text = owner_section.replace('房主自荐', '').replace('业主对房源的描述', '').strip()
        result['owner_description'] = owner_text[:300]
    
    # ============ 跟进日志（价格空间） ============
    log_idx = text.find('近30天日志')
    if log_idx >= 0:
        log_section = text[log_idx:log_idx+3000]
        log_entries = log_section.split('链家-')
        if len(log_entries) > 1:
            latest = log_entries[1][:500]
            result['latest_log'] = latest.strip()
            
            if '可以谈' in latest or '可以小谈' in latest or '好谈' in latest:
                result['price_negotiation'] = '价格可谈'
            elif '价格空间不大' in latest:
                result['price_negotiation'] = '价格空间不大'
            
            if '越快越好' in latest or '急售' in latest:
                result['urgency'] = '急售'
            elif '诚意出售' in latest:
                result['urgency'] = '诚意出售'
            elif '心态较高' in latest:
                result['urgency'] = '心态较高'
    
    return result


def fetch_property_detail(house_id: str) -> dict:
    """抓取房源详情页并提取所有关键信息"""
    target_url = f'https://house.link.lianjia.com/housedel/view?housedelCode={house_id}'
    login_trigger_url = 'https://house.link.lianjia.com/search/sale/default/gdiv_mt'
    
    result = {
        'house_id': house_id,
        'url': target_url,
        'full_text': '',
        'error': None,
    }
    result.update(extract_all_info(''))
    
    try:
        port = ensure_automation_chrome()
        
        options = Options()
        options.add_experimental_option('debuggerAddress', f'127.0.0.1:{port}')
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        print(f"[INFO] 打开链家搜索页面（触发自动登录）...")
        driver.get(login_trigger_url)
        time.sleep(8)
        
        current_url = driver.current_url
        print(f"[INFO] 当前URL: {current_url}")
        
        if 'login' in current_url:
            print("\n" + "="*60)
            print("[WARNING] 需要登录链家！")
            print("请在打开的Chrome窗口中扫码登录...")
            print("登录完成后按回车继续...")
            print("="*60 + "\n")
            try:
                input()
            except:
                print("[INFO] 超时，继续尝试...")
        
        print(f"[INFO] 打开房源详情页: {target_url}")
        driver.get(target_url)
        time.sleep(10)
        
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            result['full_text'] = body.text
        except:
            pass
        
        text = result['full_text']
        
        if len(text) < 500:
            result['error'] = f'页面内容过短（{len(text)}字符），可能未登录或加载失败'
            print(f"[WARN] {result['error']}")
            return result
        
        extracted = extract_all_info(text)
        result.update(extracted)
        
        print(f"[INFO] 提取完成，共{len(text)}字符")
        
        driver.quit()
        close_automation_chrome()
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


if __name__ == '__main__':
    import sys
    house_id = sys.argv[1] if len(sys.argv) > 1 else '107115306364'
    
    print(f'抓取详情: {house_id}')
    detail = fetch_property_detail(house_id)
    
    print(f'\n=== 提取结果 ===')
    print(f'总价: {detail.get("price")}万')
    print(f'单价: {detail.get("unit_price")}元/平米')
    print(f'户型: {detail.get("layout")}')
    print(f'面积: {detail.get("area")}平')
    print(f'朝向: {detail.get("facing")}')
    print(f'楼层: {detail.get("floor_current")}/{detail.get("floor_total")} -> 高区:{detail.get("floor_high")}')
    print(f'装修: {detail.get("decoration")}')
    print(f'车位: {detail.get("has_parking")} (价格:{detail.get("parking_price")}万)')
    print(f'建成年代: {detail.get("building_year")}')
    print(f'满五: {detail.get("is_manwu")} | 唯一: {detail.get("is_weiyi")}')
    print(f'学区: {detail.get("has_school_quota")} | 空置: {detail.get("is_vacant")} | 钥匙: {detail.get("has_key")}')
    print(f'嫌恶设施: {"有" if detail.get("has_street_issue") else "无"}')
    print(f'厅类型: {detail.get("hall_type")} | 厅面积: {detail.get("hall_area")}平 | 厅朝向: {detail.get("hall_facing")}')
    print(f'房间详情: {len(detail.get("rooms", []))}个')
    for r in detail.get('rooms', []):
        print(f'  - {r["name"]}: {r["area"]}平 {r["facing"]} {r["window_type"]}')
    print(f'城区: {detail.get("district")} | 商圈: {detail.get("plate")}')
    print(f'物业费: {detail.get("property_fee")} | 梯户比: {detail.get("ladder_ratio")}')
    print(f'电梯: {detail.get("elevator")} | 燃气: {detail.get("gas")}')
    print(f'学校: {detail.get("nearby_school")} (距离:{detail.get("school_distance")})')
    print(f'房源评分: {detail.get("property_score")} | 维护完成度: {detail.get("maintenance_completeness")}')
    print(f'7天带看: {detail.get("view_count_7d")} | 总带看: {detail.get("view_count_total")}')
    print(f'经纪人关注: {detail.get("broker_followers")} | 客户关注: {detail.get("client_followers")}')
    print(f'业主底价: {detail.get("owner_bottom_price")}万 | 预期价: {detail.get("owner_expected_price")}万')
    print(f'原购价格: {detail.get("original_price")}万')
    print(f'售房原因: {detail.get("sale_reason")}')
    print(f'户口: {detail.get("household_status")} | 抵押: {detail.get("mortgage_status")}')
    print(f'随时可签: {detail.get("can_sign_anytime")} | 期望周期: {detail.get("expected_cycle")}')
    print(f'产权共有: {detail.get("property_shared")} | 联系人业主: {detail.get("contact_is_owner")}')
    print(f'婚姻: {detail.get("marital_status")}')
    print(f'特色标签: {detail.get("property_tags")}')
    print(f'适合群体: {detail.get("suitable_for")}')
    bc = detail.get('broker_comment', {})
    print(f'地铁距离: {bc.get("subway_distance")}')
    print(f'周边配套: {bc.get("surroundings")[:50]}...')
    print(f'交通: {bc.get("traffic")[:50]}...')
    print(f'主观夸大: {bc.get("subjective_claims")}')
    print(f'业主描述: {detail.get("owner_description")[:50]}...')
    print(f'价格可谈: {detail.get("price_negotiation")}')
    print(f'急售程度: {detail.get("urgency")}')
    print(f'最新日志: {detail.get("latest_log")[:50]}...')
    
    if detail.get('error'):
        print(f'\n错误: {detail["error"]}')
    print(f'\n页面文本长度: {len(detail.get("full_text",""))}字符')
