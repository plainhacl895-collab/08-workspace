# -*- coding: utf-8 -*-
"""Browser Handover - One Port, Alternating Use"""
import os
import time
import subprocess
import sys
import re
import shutil
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

LOCK_FILE = r'C:\Users\Huawei\.openclaw\workspace-tuantuan\temp\Profile_lock.txt'
USER_PROFILE = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
CHROME_PATH = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe')
DEBUG_PORT = 9222
TARGET_URL = 'https://house.link.lianjia.com/search/sale/default/gdiv_mt'


def acquire_lock(max_wait_seconds: int = 0) -> bool:
    if not os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'w', encoding='utf-8') as f:
                f.write(f"locked at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            return True
        except:
            return False
    if max_wait_seconds == 0:
        return False
    waited = 0
    while waited < max_wait_seconds:
        time.sleep(1)
        waited += 1
        if not os.path.exists(LOCK_FILE):
            try:
                with open(LOCK_FILE, 'w', encoding='utf-8') as f:
                    f.write(f"locked at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                return True
            except:
                return False
    return False


def release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass


def wait_for_port(port: int, timeout: int = 15) -> bool:
    waited = 0
    while waited < timeout:
        try:
            req = urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=2)
            if len(req.read()) > 0:
                return True
        except:
            pass
        time.sleep(1)
        waited += 1
    return False


def launch_my_chrome() -> str:
    """Launch Chrome for automation - kills user Chrome first"""
    # Kill ALL Chrome (user's included)
    subprocess.run('taskkill /F /IM chrome.exe', shell=True, capture_output=True)
    time.sleep(2)

    cmd = [
        CHROME_PATH,
        f'--remote-debugging-port={DEBUG_PORT}',
        f'--user-data-dir={USER_PROFILE}',
        '--no-first-run',
        '--no-default-browser-check',
        '--no-sandbox',
        '--restore-last-session',
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if wait_for_port(DEBUG_PORT, timeout=15):
        return str(DEBUG_PORT)
    return None


def close_chrome_and_release():
    try:
        subprocess.run('taskkill /F /IM chrome.exe', shell=True, capture_output=True)
        time.sleep(1)
    except:
        pass
    finally:
        release_lock()


def fetch_property_detail_with_handover(house_id: str) -> dict:
    """
    Flow:
    1. Acquire lock
    2. Kill ALL Chrome (user's + any automation)
    3. Launch Chrome with user's profile + debug port
    4. Go to listing page (auto-select 佳佳 account)
    5. Fetch detail
    6. Close Chrome
    7. User opens Chrome normally (session restored)
    """
    result = {
        'house_id': house_id,
        'url': '',
        'street_facing': None,
        'has_street_issue': False,
        'facing': '',
        'hall_facing': '',
        'hall_type': '',
        'floor_high': False,
        'floor_total': 0,
        'floor_current': '',
        'has_parking': None,
        'decoration': '',
        'building_year': '',
        'full_text': '',
        'error': None,
    }

    driver = None

    try:
        if not acquire_lock():
            result['error'] = 'Chrome is busy. Please close Chrome and try again.'
            return result

        port = launch_my_chrome()
        if not port:
            release_lock()
            result['error'] = 'Failed to launch Chrome. Please try again.'
            return result

        options = Options()
        options.add_experimental_option('debuggerAddress', f'127.0.0.1:{port}')
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)

        # Go to listing page - this triggers auto-login with 佳佳 account
        driver.get(TARGET_URL)
        time.sleep(5)

        # Now go to detail page
        detail_url = f'https://house.link.lianjia.com/housedel/view?housedelCode={house_id}'
        result['url'] = detail_url

        target_tab = None
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if '/housedel/view' in driver.current_url:
                target_tab = handle
                break

        if target_tab:
            driver.switch_to.window(target_tab)
            driver.get(detail_url)
        else:
            driver.execute_script('window.open("", "_blank")')
            time.sleep(1)
            handles = driver.window_handles
            driver.switch_to.window(handles[-1])
            driver.get(detail_url)

        time.sleep(8)

        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            result['full_text'] = body.text
        except:
            pass

        text = result['full_text']

        if len(text) < 500:
            result['error'] = f'Page too short ({len(text)} chars). Lianjia login may have expired.'

        # Street issues
        if '嫌恶设施' in text:
            idx = text.find('嫌恶设施')
            segment = text[idx:idx+100]
            if '无' in segment:
                result['street_facing'] = False
            elif any(kw in segment for kw in ['临街', '路冲', '加油站', '垃圾站', '庙', '墓']):
                result['has_street_issue'] = True

        # Overall facing
        facing_map = {'南': '南', '东南': '东南', '东': '东', '西': '西', '北': '北', '南北': '南北'}
        for kw, val in facing_map.items():
            if f'朝向\n{kw}' in text or f'朝向:\n{kw}' in text or f'朝向 {kw}' in text:
                result['facing'] = val
                break

        # Hall facing from room layout
        hall_match = re.search(r'客厅\s+(\d+(?:\.\d+)?)\s*平米?\s*([东南西北]+)', text)
        if hall_match:
            result['hall_facing'] = hall_match.group(2)
            hf = hall_match.group(2)
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
            else:
                result['hall_type'] = f'厅朝向{hf}'

        # Floor
        floor_idx = text.find('楼层\n')
        if floor_idx >= 0:
            segment = text[floor_idx:floor_idx+100]
            floor_match = re.search(r'([高低中一二三四五六七八九十百]+)/(\d+)', segment)
            if floor_match:
                result['floor_current'] = floor_match.group(1)
                result['floor_total'] = int(floor_match.group(2))
                result['floor_high'] = '高' in result['floor_current']

        # Parking
        if '有无车位' in text:
            idx = text.find('有无车位')
            segment = text[idx:idx+50]
            if '有' in segment and '无车位' not in segment:
                result['has_parking'] = True
            elif '无车位' in segment:
                result['has_parking'] = False

        # Decoration
        if '装修情况' in text:
            idx = text.find('装修情况')
            segment = text[idx:idx+50]
            if '精装' in segment:
                result['decoration'] = '精装'
            elif '简装' in segment:
                result['decoration'] = '简装'
            elif '毛坯' in segment:
                result['decoration'] = '毛坯'

        # Building year
        year_match = re.search(r'建成年代[：:]\s*(\d{4})', text)
        if year_match:
            result['building_year'] = year_match.group(1)

    except Exception as e:
        result['error'] = str(e)

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        close_chrome_and_release()

    return result


if __name__ == '__main__':
    house_id = sys.argv[1] if len(sys.argv) > 1 else '107115146490'
    print(f'Fetching: {house_id}')
    detail = fetch_property_detail_with_handover(house_id)
    print(f'Floor: {detail.get("floor_current","")}/{detail.get("floor_total","")} high:{detail.get("floor_high")}')
    print(f'Facing: {detail.get("facing")}')
    print(f'Hall facing: {detail.get("hall_facing","")} -> {detail.get("hall_type","")}')
    print(f'Parking: {detail.get("has_parking")}')
    print(f'Decoration: {detail.get("decoration")}')
    print(f'Year: {detail.get("building_year")}')
    print(f'Street issue: {"yes" if detail.get("has_street_issue") else "no"}')
    if detail.get('error'):
        print(f'Error: {detail["error"]}')
    print(f'Page length: {len(detail.get("full_text",""))} chars')
