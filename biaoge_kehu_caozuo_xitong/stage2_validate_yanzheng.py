# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""阶段 2：独立校验 data.json。默认不允许单独运行，除非来自总控脚本。"""

from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


ROOT_DIR = Path(r"D:\Unique work form")
RUNTIME_DIR = ROOT_DIR / "_house_grab_runtime"
LOG_DIR = ROOT_DIR / "_house_grab_logs"
DATA_JSON = RUNTIME_DIR / "data.json"
LOG_FILE = LOG_DIR / "house_grab.log"
REQUIRED_FIELDS = ["title", "price", "area"]


def log(stage: str, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stage}] {message}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {line}\n")


def direct_run_allowed() -> bool:
    return os.environ.get("HOUSE_GRAB_PIPELINE_RUN") == "1" or "--direct" in sys.argv[1:]


def validate_json() -> tuple[bool, str]:
    stage = "阶段 2"
    log(stage, "=" * 50)
    log(stage, "开始数据校验")

    if not DATA_JSON.exists():
        return False, f"数据文件不存在：{DATA_JSON}"

    try:
        data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"JSON 格式错误：{exc}"

    if not isinstance(data, list):
        return False, "data.json 不是数组结构"
    if not data:
        return False, "data.json 为空"

    for index, item in enumerate(data, start=1):
        for field in REQUIRED_FIELDS:
            if field not in item:
                return False, f"第 {index} 条数据缺少字段：{field}"
        try:
            float(item.get("price", 0) or 0)
        except Exception:
            return False, f"第 {index} 条数据的 price 不是数值"

    return True, f"校验通过，共 {len(data)} 条"


def main() -> int:
    ok, message = validate_json()
    log("阶段 2", message if ok else f"ERROR: {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    if not direct_run_allowed():
        print("ERROR: 请运行 D:\\Unique work form\\RUN_HOUSE_GRAB.cmd，不要单独运行 stage2_validate.py")
        sys.exit(2)
    sys.exit(main())
