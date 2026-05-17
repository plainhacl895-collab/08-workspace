# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Chrome 用户配置文件路径
chrome_profile = r"C:\Users\Huawei\AppData\Local\Google\Chrome\User Data"

# 设置 Chrome 选项
options = Options()
options.add_argument(f"--user-data-dir={chrome_profile}")
options.add_argument("--profile-directory=Default")
# options.add_argument("--headless=new")  # 不启用无头模式，方便调试
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

# 房源编号
property_code = "107114849197"
url = f"https://house.link.lianjia.com/housedel/view?housedelCode={property_code}"

print(f"=== Accessing Property Page ===")
print(f"URL: {url}")
print(f"Profile: {chrome_profile}")
print("")

try:
    print("Starting Chrome...")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    
    print(f"Navigating to URL...")
    driver.get(url)
    time.sleep(10)  # Wait for page to load
    
    print(f"\nPage Title: {driver.title}")
    print(f"Current URL: {driver.current_url}")
    print(f"\n=== Page Content ===")
    
    # 获取完整页面文本
    body = driver.find_element("tag name", "body")
    full_text = body.text
    
    print(full_text)
    
    # 保存到文件
    with open(r"C:\Users\Huawei\AppData\Local\Temp\property_page_content.txt", "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n")
        f.write(f"Title: {driver.title}\n")
        f.write(f"\n=== CONTENT ===\n")
        f.write(full_text)
    
    print(f"\n=== Content saved to temp file ===")
    
    time.sleep(5)
    driver.quit()
    print("\n=== DONE ===")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
