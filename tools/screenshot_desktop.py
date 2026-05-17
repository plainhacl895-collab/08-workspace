#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""截取整个电脑屏幕并保存到桌面"""

import sys
import time
import os
from datetime import datetime

# 配置：使用 Windows Python 3.11 (带 Pillow)
PYTHON_PATH = r"C:\Users\Huawei\AppData\Local\Programs\Python\Python311\python.exe"
SAVE_DIR = os.path.join(os.path.expanduser("~"), "Desktop")

def take_screenshot():
    try:
        from PIL import ImageGrab
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        save_path = os.path.join(SAVE_DIR, filename)
        
        print(f"正在截取屏幕...", flush=True)
        
        # 等待 1 秒，让可能弹出的窗口稳定
        time.sleep(1)
        
        # 截取全屏
        img = ImageGrab.grab(all_screens=True)
        img.save(save_path)
        
        print(f"截图成功：{save_path}", flush=True)
        return save_path
        
    except ImportError:
        print("错误：未安装 Pillow 库。请使用正确的 Python 环境运行。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"截图失败：{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    path = take_screenshot()
    print(path)
