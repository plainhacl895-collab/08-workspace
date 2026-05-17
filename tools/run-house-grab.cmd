# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
房源抓取总控入口 - 工作区版本

功能：
1. 阶段 1：抓取房源数据
2. 阶段 2：验证数据
3. 阶段 3：写入 Excel

用法：python C:\Users\Huawei\.openclaw\workspace-tuantuan\biaoge_kehu_caozuo_xitong\house_grab_pipeline_zhuapai.py
"""

import sys
import io
from pathlib import Path

# 设置编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 添加路径
WORK_DIR = Path(r"D:\Unique work form")
sys.path.insert(0, str(WORK_DIR))

# 导入总控
from house_grab_pipeline_zhuapai import main

if __name__ == "__main__":
    main()
