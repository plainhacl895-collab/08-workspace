#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""探索链家内网地铁选房页面结构"""

import io
import sys
import time

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

chrome_profile = r"C:\Users\Huawei\AppData\Local\Google\Chrome\User Data"
options = Options()
options.add_argument(f"--user-data-dir={chrome_profile}")
options.add_argument("--profile-directory=Default")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")

print("Starting Chrome with user profile...")
driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(30)

try:
    print("=== 打开地铁选房页面 ===")
    driver.get("https://house.link.lianjia.com/search/sale/subway")
    time.sleep(10)
    
    print(f"页面标题: {driver.title}")
    print(f"当前URL: {driver.current_url}")
    print()
    
    # 获取页面文本
    body = driver.find_element(By.TAG_NAME, "body")
    page_text = body.text
    
    # 保存完整页面文本
    with open(r"C:\Users\Huawei\AppData\Local\Temp\subway_page_text.txt", "w", encoding="utf-8") as f:
        f.write(f"Title: {driver.title}\n")
        f.write(f"URL: {driver.current_url}\n\n")
        f.write(page_text)
    
    print("=== 页面文本（前3000字符）===")
    print(page_text[:3000])
    
    # 查找所有包含"号线"或"地铁"的元素
    print("\n=== 包含'号线'或'地铁'的元素 ===")
    all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
    found = set()
    for el in all_elements:
        text = el.text.strip()
        if ("号线" in text or "地铁" in text) and len(text) < 100 and text not in found:
            found.add(text)
            tag = el.tag_name
            cls = el.get_attribute("class") or ""
            id_attr = el.get_attribute("id") or ""
            print(f"  tag='{tag}' id='{id_attr}' class='{cls[:80]}' text='{text}'")
    
    # 查找所有链接
    print("\n=== 所有链接 ===")
    links = driver.find_elements(By.TAG_NAME, "a")
    for link in links:
        text = link.text.strip()
        href = link.get_attribute("href") or ""
        if text and len(text) < 50:
            print(f"  text='{text}' href='{href[:120]}'")
    
    # 查找所有包含 subway/tx/subway 的 CSS 类
    print("\n=== 包含 subway/tx 关键词的 class ===")
    elements_with_class = driver.find_elements(By.CSS_SELECTOR, "[class]")
    for el in elements_with_class:
        cls = el.get_attribute("class") or ""
        if "subway" in cls.lower() or "tx_" in cls.lower() or "地铁" in cls:
            text = el.text.strip()[:80]
            print(f"  class='{cls[:80]}' text='{text}'")
    
    print(f"\n=== 完整页面文本已保存到 temp 文件 ===")
    time.sleep(3)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("\n=== DONE ===")
