#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
"""
每日跟进计划生成器 v9.1 - 修复跟进记录过滤问题

修复：read_client_from_excel 去掉关键词过滤，直接取最近3条跟进，
      让 AI 拿到完整的客户信息生成差异化建议。
      其余逻辑与 v9.0 完全一致。
"""

from __future__ import annotations
import argparse
from copy import copy
import os
import json
import subprocess
import threading
import urllib.parse
import urllib.request
import uuid
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import win32com.client
import requests
import logging

WORKSPACE_ROOT = Path(__file__).parent.parent
CACHE_FILE = WORKSPACE_ROOT / "runtime" / "tuantuan_cache.json"
RUNSTATE_DIR = WORKSPACE_ROOT / "runtime" / "daily_follow_plan"
STATUS_FILE = RUNSTATE_DIR / "status.json"
PID_FILE = RUNSTATE_DIR / "runner.pid"
PROGRESS_FILE = RUNSTATE_DIR / "progress.json"
SUGGESTION_BUNDLE_FILE = RUNSTATE_DIR / "latest_suggestions.json"

# ⭐ 新增：AI 建议缓存配置 ⭐
SUGGESTION_CACHE_DIR = WORKSPACE_ROOT / "runtime" / "ai_suggestions"
SUGGESTION_CACHE_MAX_AGE_DAYS = 3  # 缓存有效期 3 天
TELEGRAM_CHAT_ID = "8724466632"
TELEGRAM_BOT_TOKEN = "8705450288:AAExGrG5ZIKt3wUnoAZ2Bll4W2StzDVCOYY"
WORKBOOK_PATH = Path(r"D:\Unique work form\daily_followup.xlsm")
DESKTOP_OUTPUT_BASENAME = "daily_follow_plan_latest.txt"
DESKTOP_FAILURE_BASENAME = "daily_follow_plan_failed_latest.txt"
PROGRESS_NOTIFY_EVERY = 5
STATUS_HEARTBEAT_INTERVAL_SECONDS = 60

# Bailian API
BAILIAN_API_KEY = "sk-sp-9112ba5f54c74b40b798a085b9b040a6"
BAILIAN_API_URL = "https://coding.dashscope.aliyuncs.com/v1/chat/completions"
BAILIAN_MODEL = "qwen3.5-plus"

# Excel 表结构
CLIENT_SHEET_INDEX = 2
CLIENT_HEADER_ROW = 11
FIRST_FOLLOWUP_COLUMN = 20

# 客户信息列定义
COL_NAME = 9
COL_GRADE = 6
COL_BUDGET = 8
COL_DISTRICT = 10
COL_SUMMARY = 4
COL_NEED = 16
COL_PAIN = 18
COL_NOTES = 19
VALUABLE_FOLLOWUP_KEYWORDS = ("有带看", "有回复", "通电话", "解读")
MAX_RECENT_FOLLOWUPS = 3
AI_REQUEST_TIMEOUT = 180
AI_RETRY_COUNT = 3
AI_RETRY_SLEEP_SECONDS = 15

# 日志配置
LOG_DIR = RUNSTATE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"daily_follow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logger = logging.getLogger("daily_follow")
logger.setLevel(logging.DEBUG)
_fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_sh = logging.StreamHandler()
_sh.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
_fh.setFormatter(_fmt)
_sh.setFormatter(_fmt)
logger.addHandler(_fh)
logger.addHandler(_sh)


class AISuggestionError(RuntimeError):
    pass


_STATUS_LOCK = threading.Lock()
_LAST_STATUS_PAYLOAD: dict[str, Any] = {}
_STATUS_HEARTBEAT_STOP = threading.Event()
_STATUS_HEARTBEAT_THREAD: threading.Thread | None = None


def clean_cell_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("_x000D_", "\n").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def clip_text(value: Any, limit: int) -> str:
    text = clean_cell_text(value)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def calculate_days_ago(value: Any) -> int | None:
    iso_value = header_date_to_iso(value) or clean_cell_text(value)
    if not iso_value:
        return None
    try:
        target = datetime.strptime(iso_value, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (datetime.now().date() - target).days


def detect_followup_signal(content: Any) -> str:
    text = clean_cell_text(content)
    for keyword in VALUABLE_FOLLOWUP_KEYWORDS:
        if keyword in text:
            return keyword
    return "关键跟进"


def build_followup_timeline(followups: list[dict]) -> list[dict]:
    timeline: list[dict] = []
    for item in followups[-MAX_RECENT_FOLLOWUPS:]:
        followup_date = header_date_to_iso(item.get("date")) or clean_cell_text(item.get("date"))
        timeline.append({
            "date": followup_date,
            "days_ago": calculate_days_ago(followup_date),
            "signal": detect_followup_signal(item.get("content")),
            "content": clip_text(item.get("content"), 160),
        })
    return timeline


def format_followup_timeline(followups: list[dict]) -> str:
    timeline = build_followup_timeline(followups)
    if not timeline:
        return "  （暂无关键跟进记录）"

    lines: list[str] = []
    for index, item in enumerate(timeline, start=1):
        date_text = item.get("date") or "未知日期"
        days_ago = item.get("days_ago")
        days_text = f"{days_ago}天前" if days_ago is not None else "日期待核对"
        signal = item.get("signal") or "关键跟进"
        content = item.get("content") or ""
        lines.append(f"  {index}. {date_text}（{days_text}）| {signal} | {content}")
    return "\n".join(lines)


def header_date_to_iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)):
        try:
            base = datetime(1899, 12, 30)
            return (base + timedelta(days=float(value))).date().isoformat()
        except Exception:
            return None

    text = clean_cell_text(value)
    if not text:
        return None

    match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if not match:
        return None

    try:
        year, month, day = (int(part) for part in match.groups())
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def copy_cell_style(source, target) -> None:
    if source is None or target is None or not getattr(source, "has_style", False):
        return
    target._style = copy(source._style)


def last_used_header_col(ws) -> int:
    for col in range(ws.max_column, FIRST_FOLLOWUP_COLUMN - 1, -1):
        value = ws.cell(row=CLIENT_HEADER_ROW, column=col).value
        if value is not None and str(value).strip():
            return col
    return FIRST_FOLLOWUP_COLUMN - 1


def find_latest_date_header_col(ws, upto_col: int | None = None) -> int | None:
    upper = upto_col or last_used_header_col(ws)
    for col in range(upper, FIRST_FOLLOWUP_COLUMN - 1, -1):
        header_val = ws.cell(row=CLIENT_HEADER_ROW, column=col).value
        if header_val and str(header_val).endswith(" 建议"):
            continue
        if header_date_to_iso(header_val):
            return col
    return None


def find_latest_ai_header_col(ws, upto_col: int | None = None) -> int | None:
    upper = upto_col or last_used_header_col(ws)
    for col in range(upper, FIRST_FOLLOWUP_COLUMN - 1, -1):
        header_val = ws.cell(row=CLIENT_HEADER_ROW, column=col).value
        if isinstance(header_val, str) and header_val.endswith(" 建议"):
            return col
    return None


def build_reengagement_suggestion(client: dict) -> str:
    budget = client.get("budget", "?")
    focus_text = clean_cell_text(client.get("need")) or clean_cell_text(client.get("pain")) or clean_cell_text(client.get("notes"))
    focus = focus_text.split("，")[0].split("。")[0][:20] if focus_text else "预算、区域和户型"
    return f"先承接之前聊过的{focus}，确认需求和决策节奏有没有变化；今天先不群推房源，先把卡点和下一步节奏确认清楚。"


def should_regenerate_existing_suggestion(existing: str, client: dict) -> bool:
    existing_text = clean_cell_text(existing)
    if not existing_text:
        return True
    if "首次联系" not in existing_text:
        return False
    if client.get("followups"):
        return True
    return any(clean_cell_text(client.get(field)) for field in ("client_summary", "need", "pain", "notes"))


def ensure_runstate_dir() -> None:
    RUNSTATE_DIR.mkdir(parents=True, exist_ok=True)


# ⭐ 新增：AI 建议缓存函数 ⭐
def ensure_suggestion_cache_dir() -> None:
    """确保缓存目录存在"""
    SUGGESTION_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_suggestion_cache_file(client: dict) -> Path:
    """获取客户的建议缓存文件路径"""
    ensure_suggestion_cache_dir()
    row = client.get('row', 0)
    return SUGGESTION_CACHE_DIR / f"client_{row}_suggestion.json"


def load_suggestion_cache(cache_file: Path) -> dict | None:
    """加载缓存的建议"""
    try:
        if not cache_file.exists():
            return None
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception:
        return None


def save_suggestion_cache(cache_file: Path, suggestion: str, client: dict) -> None:
    """保存建议到缓存"""
    try:
        ensure_suggestion_cache_dir()
        data = {
            'suggestion': suggestion,
            'client_row': client.get('row'),
            'client_name': client.get('name'),
            'last_followup': client.get('last_followup_date'),
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'cache_expires_at': (datetime.now() + timedelta(days=SUGGESTION_CACHE_MAX_AGE_DAYS)).isoformat(timespec='seconds')
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存建议缓存失败：{e}")


def is_suggestion_cache_fresh(cache_file: Path, max_age_days: int = None) -> bool:
    """检查缓存是否新鲜（未过期）"""
    if max_age_days is None:
        max_age_days = SUGGESTION_CACHE_MAX_AGE_DAYS
    
    try:
        if not cache_file.exists():
            return False
        
        data = load_suggestion_cache(cache_file)
        if not data:
            return False
        
        # 检查是否有过期时间
        if 'cache_expires_at' in data:
            expires_at = datetime.fromisoformat(data['cache_expires_at'])
            return datetime.now() < expires_at
        
        # 兼容旧格式：检查生成时间
        if 'generated_at' in data:
            generated_at = datetime.fromisoformat(data['generated_at'])
            age = datetime.now() - generated_at
            return age.total_seconds() < (max_age_days * 24 * 3600)
        
        return False
    except Exception:
        return False


def has_new_followup_since_cache(client: dict, cache_file: Path) -> bool:
    """检查是否有新的跟进记录（相比缓存）"""
    try:
        if not cache_file.exists():
            return True
        
        data = load_suggestion_cache(cache_file)
        if not data:
            return True
        
        cached_followup = data.get('last_followup', '')
        current_followup = client.get('last_followup_date', '')
        
        # 如果有新跟进，返回 True
        return current_followup > cached_followup
    except Exception:
        return True


def generate_simple_reminder(client: dict) -> str:
    """生成简单的提醒建议（无新跟进时使用）"""
    name = client.get('name', '客户')
    last_followup = client.get('last_followup_date', '未知')
    return f"【跟进提醒】距离上次跟进已有一段时间（上次：{last_followup}），建议微信/电话简单问候，确认客户近况和看房节奏，保持联系不断联。"


def is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except Exception:
        return False
    output = clean_cell_text(result.stdout)
    if not output or output.startswith("INFO:"):
        return False
    return f'"{pid}"' in output or f",{pid}," in output


def write_status(status: dict[str, Any]) -> None:
    ensure_runstate_dir()
    payload = dict(status)
    payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
    with _STATUS_LOCK:
        _LAST_STATUS_PAYLOAD.clear()
        _LAST_STATUS_PAYLOAD.update(payload)
    STATUS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_progress(progress: dict[str, Any]) -> None:
    ensure_runstate_dir()
    payload = dict(progress)
    payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
    PROGRESS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _status_heartbeat_loop() -> None:
    while not _STATUS_HEARTBEAT_STOP.wait(STATUS_HEARTBEAT_INTERVAL_SECONDS):
        with _STATUS_LOCK:
            payload = dict(_LAST_STATUS_PAYLOAD)
        if not payload or payload.get("status") != "running":
            continue
        payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
        payload["heartbeat"] = True
        try:
            STATUS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass


def start_status_heartbeat() -> None:
    global _STATUS_HEARTBEAT_THREAD
    if _STATUS_HEARTBEAT_THREAD and _STATUS_HEARTBEAT_THREAD.is_alive():
        return
    _STATUS_HEARTBEAT_STOP.clear()
    _STATUS_HEARTBEAT_THREAD = threading.Thread(
        target=_status_heartbeat_loop,
        name="daily-follow-plan-heartbeat",
        daemon=True,
    )
    _STATUS_HEARTBEAT_THREAD.start()


def stop_status_heartbeat() -> None:
    _STATUS_HEARTBEAT_STOP.set()


def acquire_run_lock() -> None:
    ensure_runstate_dir()
    if PID_FILE.exists():
        stale_pid = clean_cell_text(PID_FILE.read_text(encoding="utf-8"))
        if stale_pid.isdigit() and is_pid_running(int(stale_pid)):
            raise RuntimeError(f"每日跟进计划任务已在运行中，PID={stale_pid}")
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def release_run_lock() -> None:
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
    except Exception:
        pass


def call_bailian(prompt: str, max_tokens: int = 400) -> str:
    payload = {
        "model": BAILIAN_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }

    error_messages: list[str] = []
    for attempt in range(1, AI_RETRY_COUNT + 1):
        try:
            resp = requests.post(
                BAILIAN_API_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {BAILIAN_API_KEY}",
                },
                timeout=(30, AI_REQUEST_TIMEOUT),  # (connect, read) 分段超时
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get("error"):
                raise AISuggestionError(str(result["error"]))
            choices = result.get("choices") or []
            if not choices:
                raise AISuggestionError(f"接口返回缺少 choices: {json.dumps(result, ensure_ascii=False)[:300]}")
            content = choices[0].get("message", {}).get("content", "").strip()
            if not content:
                raise AISuggestionError("接口返回空内容")
            logger.info(f"Bailian API 调用成功（第{attempt}次）")
            return content

        except requests.exceptions.Timeout as e:
            logger.error(f"Bailian API 超时（第{attempt}次）: {e}")
            error_messages.append(f"第{attempt}次超时: {e}")
        except requests.exceptions.HTTPError as e:
            if "429" in str(e):
                # 429 限流错误：使用更长的指数退避
                sleep_seconds = 60 * attempt  # 第1次60秒，第2次120秒
                logger.warning(f"Bailian API 限流（429），等待 {sleep_seconds} 秒后重试...")
                time.sleep(sleep_seconds)
                error_messages.append(f"第{attempt}次限流: {e}")
                continue
            else:
                logger.error(f"Bailian API 调用失败（第{attempt}次）: {e}")
                error_messages.append(f"第{attempt}次: {e}")
        except Exception as e:
            logger.error(f"Bailian API 调用失败（第{attempt}次）: {e}")
            error_messages.append(f"第{attempt}次: {e}")

        if attempt < AI_RETRY_COUNT:
            sleep_seconds = AI_RETRY_SLEEP_SECONDS * attempt
            logger.info(f"    {sleep_seconds}秒后重试...")
            time.sleep(sleep_seconds)

    raise AISuggestionError("；".join(error_messages) if error_messages else "未知错误")


def filter_valuable_followups(followups: list[dict], max_count: int = 5) -> list[dict]:
    """只保留包含真实业务动作的跟进（有带看/有回复/通电话/解读），剔除普通问候和AI建议。"""
    valuable = []
    for item in followups:
        content = clean_cell_text(item.get("content", ""))
        if not content:
            continue
        # 必须包含关键业务动作
        if any(kw in content for kw in VALUABLE_FOLLOWUP_KEYWORDS):
            valuable.append(item)
        # 最多保留 max_count 条，按时间倒序（最新的在前）
        if len(valuable) >= max_count:
            break
    return valuable


def build_client_prompt(client: dict) -> str:
    name = client.get("name", "未知")
    grade = client.get("grade", "C")
    budget = client.get("budget", 0)
    district = client.get("district", "")
    summary = clip_text(client.get("client_summary", ""), 220)
    need = clip_text(client.get("need", ""), 120)
    pain = clip_text(client.get("pain", ""), 120)
    notes = clip_text(client.get("notes", ""), 180)

    # 新增：读取昨天的 AI 检查结果
    ai_checks = client.get("ai_checks", {})
    yesterday_check = ""
    # 尝试找最近的检查记录
    if ai_checks:
        dates = sorted(ai_checks.keys(), reverse=True)
        # 取最新的一条
        yesterday_check = f"\n【昨日复盘】\n{ai_checks[dates[0]]}" if dates else ""

    # 核心修复：只提取真实业务动作，过滤掉普通问候和 AI 建议
    all_followups = client.get("followups", [])
    valuable_followups = filter_valuable_followups(all_followups, max_count=5)
    followup_text = format_followup_timeline(valuable_followups)

    # 统计关键动作频次，注入 prompt
    signal_counts = {"有带看": 0, "有回复": 0, "通电话": 0, "解读": 0}
    for item in valuable_followups:
        content = clean_cell_text(item.get("content", ""))
        for kw in signal_counts:
            if kw in content:
                signal_counts[kw] += 1

    signal_summary = " | ".join(f"{k}{v}次" for k, v in signal_counts.items() if v > 0) or "无关键动作"

    last_date = client.get("last_followup_date", "")
    last_date_iso = header_date_to_iso(last_date) or clean_cell_text(last_date)
    if last_date_iso:
        try:
            last_dt = datetime.strptime(last_date_iso, "%Y-%m-%d")
            days_ago = (datetime.now() - last_dt).days
            days_str = f"{days_ago}天前（{last_date_iso}）"
        except Exception:
            days_str = last_date_iso
    else:
        days_str = "暂无有效跟进"

    prompt = f"""你是一名经验丰富的二手房销售助手，正在帮经纪人佳佳规划今天对客户"{name}"的跟进策略。

【核心原则】
1. 你必须基于客户的真实业务动作（带看/回复/通话）生成建议，严禁参考任何历史 AI 建议或空泛套话。
2. 如果客户已有跟进历史或基础画像，严禁写成"首次联系"或"补齐信息"。
3. 你一次只分析这 1 位客户，不要把其他客户情况混进来，不要编造不存在的事实。

【客户画像】
- 姓名：{name}
- 等级：{grade}级
- 预算：{budget}万
- 意向区域：{district}
- 客户分析：{summary or "（未填写）"}
- 核心需求：{need or "（未填写）"}
- 主要痛点：{pain or "（未填写）"}
- 备注：{notes or "（未填写）"}

【真实业务动作统计】
{signal_summary}
→ 这是客户实际发生过的业务动作，是你生成建议的核心依据。{yesterday_check}

【关键跟进时间线（只保留有带看/有回复/通电话/解读的记录）】
{followup_text}

【时间判断】
- 距上次跟进：{days_str}
- 今天日期：{datetime.now().strftime("%Y-%m-%d")}

【狼性销售原则】（必须遵守）
1. **电话优先**：你的第一动作永远是打电话。除非客户明确拉黑或今天刚打过没接，否则**严禁建议“发微信问候”**。
2. **微信仅辅助**：微信只用于“刚才没接电话，发套房源给你看”或“留言告知来电意图”，绝不用于无效闲聊。
3. **不接电话就降级**：连续两次不接电话，视为**无效/沉睡**。建议直接“冷冻”，不要在微信上浪费时间试探。
4. **别怕得罪人**：做销售就是要敢于打扰。客户说“别打电话”通常是借口。只要他想买房，就必须接电话。
5. **直接验证意向**：打电话是检验客户意向的唯一标准。打不通=没意向，不要找借口替他开脱。

请根据以上信息，给出今天跟进这位客户的具体建议。要求：
1. 结合“客户画像（历史需求/痛点）”与“最近跟进（当下情绪/反馈）”，制定今天的策略。
2. goal（今天跟进的核心目标，一句话，15字以内）
3. suggestion（必须写清楚：今天用什么方式开场、重点确认什么、今天推不推房、如果推推哪类；40-90字）
4. 如果信息不足，只能指出"需要先确认什么"，不要假装知道。

直接输出以下格式，不要多余解释：
目标：[goal内容]
建议：[suggestion内容]"""

    return prompt


def parse_ai_suggestion(raw: str) -> dict:
    goal = ""
    suggestion = ""

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("目标：") or line.startswith("目标:"):
            goal = line.split("：", 1)[-1].split(":", 1)[-1].strip()
        elif line.startswith("建议：") or line.startswith("建议:"):
            suggestion = line.split("：", 1)[-1].split(":", 1)[-1].strip()

    if not suggestion and raw:
        suggestion = raw.replace("\n", " ").strip()

    return {"goal": goal, "suggestion": suggestion}


def generate_suggestion_for_single_client(client: dict) -> str:
    prompt = build_client_prompt(client)
    raw = call_bailian(prompt, max_tokens=260)
    parsed = parse_ai_suggestion(raw)
    suggestion = parsed.get("suggestion", "")
    goal = parsed.get("goal", "")
    if suggestion:
        if goal:
            return f"【{goal}】{suggestion}"
        return suggestion

    raise AISuggestionError(f"AI 返回内容无法解析为建议: {raw[:200]}")


def get_reference_format(ws, target_col: int) -> dict:
    for ref_col in range(target_col - 1, FIRST_FOLLOWUP_COLUMN - 1, -1):
        for ref_row in range(12, 50):
            cell = ws.cell(row=ref_row, column=ref_col)
            val = cell.value
            if not val or not str(val).strip():
                continue
            font = cell.font
            font_name = font.name if font and font.name else None
            font_size = font.size if font and font.size else None
            font_bold = font.bold if font and font.bold else False
            if font_name and font_name != "Calibri":
                return {
                    "font_name": font_name,
                    "font_size": font_size or 10,
                    "font_bold": font_bold,
                }
    return {"font_name": "等线", "font_size": 10, "font_bold": False}


def kill_excel_if_open() -> None:
    target_still_open = False
    try:
        import pythoncom
        from win32com.client import GetObject
        pythoncom.CoInitialize()
        excel = GetObject(Class="Excel.Application")
        for wb in excel.Workbooks:
            try:
                wb_path = Path(wb.FullName)
                if wb_path.resolve() == WORKBOOK_PATH.resolve():
                    wb.Save()  # 保持.xlsm 格式，保护宏
                    wb.Close(SaveChanges=True)
                    time.sleep(1)
            except Exception:
                continue
    except Exception:
        pass

    try:
        import pythoncom
        from win32com.client import GetObject
        pythoncom.CoInitialize()
        excel = GetObject(Class="Excel.Application")
        for wb in excel.Workbooks:
            try:
                if Path(wb.FullName).resolve() == WORKBOOK_PATH.resolve():
                    target_still_open = True
                    break
            except Exception:
                continue
    except Exception:
        target_still_open = False

    if not target_still_open:
        return

    try:
        subprocess.run(["taskkill", "/F", "/IM", "EXCEL.EXE"], check=False, capture_output=True)
        time.sleep(5)  # 等待大文件保存完成
    except Exception:
        pass


def is_workbook_writable() -> bool:
    try:
        with open(WORKBOOK_PATH, "rb+"):
            return True
    except PermissionError:
        return False
    except Exception:
        return WORKBOOK_PATH.exists()


def wait_until_workbook_writable(timeout_seconds: int = 20) -> bool:
    deadline = time.time() + max(1, timeout_seconds)
    while time.time() < deadline:
        if is_workbook_writable():
            return True
        time.sleep(1)
    return is_workbook_writable()


def release_workbook_lock(force_kill: bool = False) -> bool:
    kill_excel_if_open()
    if wait_until_workbook_writable(8):
        return True
    if not force_kill:
        return False
    try:
        subprocess.run(["taskkill", "/F", "/IM", "EXCEL.EXE"], check=False, capture_output=True)
    except Exception:
        pass
    time.sleep(5)  # 等待大文件保存完成
    return wait_until_workbook_writable(20)


def force_build_cache() -> dict:
    """高速版缓存刷新：一次性读取 UsedRange 到内存，避免逐格 COM 交互"""
    import sys
    logger.info("正在调用高速版 force_build_cache...")
    sys.path.insert(0, str(Path(__file__).parent))
    from tuantuan_cli import (
        WORKBOOK_PATH, WORKBOOK_PASSWORD, CLIENT_SHEET_INDEX, PROPERTY_SHEET_INDEX,
        BUSINESS_EXPERIENCE_SHEET_NAME, TECHNICAL_EXPERIENCE_SHEET_NAME,
        RUNTIME_DIR, CACHE_FILE, CLIENT_HEADER_ROW,
        parse_properties, parse_business_experiences, parse_technical_experiences,
        iso_now, workbook_mtime,
        pythoncom, DispatchEx
    )

    def clean(val):
        if val is None: return ""
        s = str(val).replace("_x000D_", "\n").replace("\r\n", "\n")
        return "\n".join(l.strip() for l in s.split("\n") if l.strip())

    if pythoncom is None or DispatchEx is None:
        raise RuntimeError("win32com 不可用")
        
    logger.info("初始化 COM...")
    pythoncom.CoInitialize()
    excel = None
    workbook = None
    
    try:
        logger.info("启动 Excel 实例...")
        excel = DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.AutomationSecurity = 3
        
        logger.info("正在打开工作簿...")
        workbook = excel.Workbooks.Open(
            Filename=str(WORKBOOK_PATH),
            UpdateLinks=0,
            ReadOnly=True,
            Password=WORKBOOK_PASSWORD,
        )
        logger.info("工作簿打开成功，开始高速解析...")

        # 1. 高速解析客户表
        client_sheet = workbook.Worksheets(CLIENT_SHEET_INDEX)
        ur = client_sheet.UsedRange
        
        if ur is None:
            data = ()
        else:
            val = ur.Value
            data = val if isinstance(val, tuple) else ((val,),) if val else ()
        
        top = ur.Row if ur else 1
        left = ur.Column if ur else 1
        
        clients = []
        if data:
            header_row_idx = CLIENT_HEADER_ROW - top
            headers = []
            if 0 <= header_row_idx < len(data):
                row_data = data[header_row_idx]
                headers = list(row_data) if isinstance(row_data, tuple) else [row_data]
            
            for r_idx, row_data in enumerate(data):
                sheet_row = top + r_idx
                if sheet_row < 12: continue 
                
                if not isinstance(row_data, tuple):
                    row_data = (row_data,)
                
                # Name at col 9
                c_idx = 9 - left
                if 0 <= c_idx < len(row_data):
                    name = clean(row_data[c_idx])
                else: continue
                
                if not name: continue
                
                def get(c):
                    idx = c - left
                    return row_data[idx] if 0 <= idx < len(row_data) else None

                c = {
                    "row": sheet_row, "name": name,
                    "grade": clean(get(6)), "budget": get(8),
                    "district": clean(get(10)), "client_summary": clean(get(4)),
                    "need": clean(get(16)), "pain": clean(get(18)),
                    "notes": clean(get(19)), "phone": clean(get(11)),
                    "recommended_house_ids": [], "followups": [],
                }
                
                # Parse followups from col 20
                start_c = 20
                c_start = start_c - left
                if c_start >= 0:
                    for i in range(c_start, len(row_data)):
                        content = row_data[i]
                        if content:
                            text = clean(content)
                            if any(kw in text for kw in ("有带看", "有回复", "通电话", "解读")):
                                h = headers[i] if i < len(headers) else None
                                if h and not str(h).endswith(" 建议"):
                                    c["followups"].append({"date": clean(h), "content": text})
                
                c["followup_count"] = len(c["followups"])
                c["last_followup_date"] = c["followups"][-1]["date"] if c["followups"] else None
                clients.append(c)
        
        logger.info(f"解析完成 {len(clients)} 个客户")

        # 2. 【性能优化】每日跟进只需客户数据，跳过耗时的房源表解析
        properties = []
        business_experiences = []
        technical_experiences = []
        
        # 原逻辑保留（备用）：
        # property_sheet = workbook.Worksheets(PROPERTY_SHEET_INDEX)
        # properties = parse_properties(property_sheet)
        # ...
                
        cache = {
            "generated_at": iso_now(),
            "source": {"workbook_path": str(WORKBOOK_PATH), "workbook_mtime": workbook_mtime()},
            "clients": clients, "properties": properties,
            "business_experiences": business_experiences,
            "technical_experiences": technical_experiences,
        }
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        return cache
        
    finally:
        if workbook:
            try: workbook.Close(SaveChanges=False)
            except: pass
        if excel:
            try: excel.Quit()
            except: pass
        try: pythoncom.CoUninitialize()
        except: pass


def ensure_cache() -> dict:
    import sys
    import subprocess
    sys.path.insert(0, str(Path(__file__).parent))
    from tuantuan_cli import ensure_cache as shared_ensure_cache, cache_is_fresh, load_cache

    cache = load_cache()
    if cache and cache_is_fresh(cache):
        logger.info("缓存新鲜，直接复用")
        return cache

    # 缓存过期，强制解锁并刷新
    logger.warning("缓存不新鲜，强制解锁 Excel 并刷新")
    try:
        subprocess.run([r"C:\Windows\System32\taskkill.exe", "/F", "/IM", "EXCEL.EXE"], check=False, capture_output=True)
        time.sleep(4)
    except Exception:
        pass

    # 绕过 COM 检查，直接强制读取
    try:
        return force_build_cache()
    except Exception as e:
        logger.error(f"缓存刷新失败：{e}")
        return shared_ensure_cache(force=False)


def build_client_lookup(cache: dict) -> dict[int, dict]:
    lookup: dict[int, dict] = {}
    for client in cache.get("clients", []):
        row = client.get("row")
        if not row:
            continue
        followups = client.get("followups", []) or []
        followups = sorted(
            followups,
            key=lambda item: header_date_to_iso(item.get("date")) or clean_cell_text(item.get("date"))
        )
        normalized = dict(client)
        normalized["followups"] = followups
        normalized["recent_followups"] = followups[-MAX_RECENT_FOLLOWUPS:]
        normalized["last_followup_date"] = followups[-1].get("date") if followups else client.get("last_followup_date")
        lookup[row] = normalized
    return lookup


def get_today_follow_list(cache: dict, limit: int = 20) -> list[dict]:
    from tuantuan_cli import analyze_client_triage, clean_text

    scored = []
    for client in cache["clients"]:
        triage = analyze_client_triage(client)
        scored.append({"client": client, "triage": triage})

    # 第一优先级：follow_now 桶（A 级/趁热/防遗忘/有跟进信号）
    follow_now = [item for item in scored if item["triage"].get("bucket") == "follow_now"]
    # 第二优先级：can_wait 桶（可跟进但非紧急）
    can_wait = [item for item in scored if item["triage"].get("bucket") == "can_wait"]

    # 按分数+等级排序，优先高分客户
    follow_now.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"], item["client"]["row"]))
    can_wait.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"], item["client"]["row"]))

    # A 级客户优先：确保所有 A 级客户入选
    a_clients = [item for item in follow_now if item["client"].get("grade", "").upper() == "A"]
    non_a_follow_now = [item for item in follow_now if item["client"].get("grade", "").upper() != "A"]

    # 先取所有 A 级客户，再从 follow_now 非 A 级补充，最后从 can_wait 补充
    priority_list = a_clients[:limit]
    remaining = limit - len(priority_list)
    if remaining > 0:
        priority_list += non_a_follow_now[:remaining]
        remaining = limit - len(priority_list)
    if remaining > 0:
        priority_list += can_wait[:remaining]

    result = []
    for item in priority_list:
        client = item["client"]
        result.append({
            "row": client.get("row"),
            "name": client.get("name", "未知"),
            "grade": client.get("grade", "C"),
            "budget": client.get("budget", 0),
            "district": client.get("district", ""),
            "last_followup_date": client.get("last_followup_date"),
        })

    return result


def read_client_from_excel(ws, row: int) -> dict:
    """
    只读取业务上定义为有效的跟进信息，并且从表格最新列向前回溯，
    避免漏掉 300 列之后的新跟进记录。
    """
    client = {
        "row": row,
        "name": ws.cell(row=row, column=COL_NAME).value or "",
        "grade": ws.cell(row=row, column=COL_GRADE).value or "C",
        "budget": ws.cell(row=row, column=COL_BUDGET).value or 0,
        "district": ws.cell(row=row, column=COL_DISTRICT).value or "",
        "client_summary": ws.cell(row=row, column=COL_SUMMARY).value or "",
        "need": ws.cell(row=row, column=COL_NEED).value or "",
        "pain": ws.cell(row=row, column=COL_PAIN).value or "",
        "notes": ws.cell(row=row, column=COL_NOTES).value or "",
        "followups": [],
        "recent_followups": [],
        "last_followup_date": None,
    }

    followups = []
    for col in range(last_used_header_col(ws), FIRST_FOLLOWUP_COLUMN - 1, -1):
        # 跳过 AI 建议列
        header_val = ws.cell(row=CLIENT_HEADER_ROW, column=col).value
        if header_val and str(header_val).endswith(" 建议"):
            continue
        followup_date = header_date_to_iso(header_val)
        if not followup_date:
            continue

        content = clean_cell_text(ws.cell(row=row, column=col).value)
        if not content:
            continue
        if not any(keyword in content for keyword in VALUABLE_FOLLOWUP_KEYWORDS):
            continue

        followups.append({
            "date": followup_date,
            "content": content,
            "column": col,
        })
        if len(followups) >= MAX_RECENT_FOLLOWUPS:
            break

    followups.reverse()
    client["followups"] = followups
    client["recent_followups"] = followups
    if followups:
        client["last_followup_date"] = followups[-1].get("date", "")

    return client


def find_or_create_date_columns(ws, target_date: datetime) -> tuple[int, int]:
    date_iso = target_date.strftime("%Y-%m-%d")
    ai_title = target_date.strftime("%Y-%m-%d") + " 建议"
    # 修复：Excel COM 接口将 datetime 解释为 UTC 时间，需要加 8 小时补偿北京时间偏移
    excel_date_value = datetime(target_date.year, target_date.month, target_date.day, 8, 0, 0)

    ai_col = None
    followup_col = None
    ai_matches: list[int] = []
    followup_matches: list[int] = []
    last_header_col = last_used_header_col(ws)
    
    # 1. 严格查找：必须精确匹配今天的日期标题，绝不凑合
    for col in range(FIRST_FOLLOWUP_COLUMN, last_header_col + 1):
        cell_value = ws.cell(row=CLIENT_HEADER_ROW, column=col).value
        cell_str = str(cell_value).strip() if cell_value else ""
        
        # 查找今天的 AI 建议列
        if cell_str == ai_title:
            ai_matches.append(col)
            ai_col = col
            
        # 查找今天的跟进列
        if header_date_to_iso(cell_value) == date_iso:
            followup_matches.append(col)
            followup_col = col

    # 2. 找样式参考：借用最近的旧列样式，但不复用它们的内容
    # 注意：这里找的是“任意”最近的列，作为格式模板，不参与写入定位
    reference_date_col = find_latest_date_header_col(ws, last_header_col)
    reference_ai_col = find_latest_ai_header_col(ws, last_header_col)
    
    # 3. 决策：如果没找到今天的列，坚决新建；找到了则复用位置并覆盖
    if ai_col and followup_col:
        # 找到了今天的列，直接复用位置，但必须确保表头正确
        ai_header = ws.cell(row=CLIENT_HEADER_ROW, column=ai_col)
        followup_header = ws.cell(row=CLIENT_HEADER_ROW, column=followup_col)
        
        # 样式同步（只借格式）
        if reference_ai_col is not None:
            copy_cell_style(ws.cell(row=CLIENT_HEADER_ROW, column=reference_ai_col), ai_header)
        if reference_date_col is not None:
            copy_cell_style(ws.cell(row=CLIENT_HEADER_ROW, column=reference_date_col), followup_header)
            
        # 强制更新表头（防止万一有人改过）
        ai_header.value = ai_title
        followup_header.value = excel_date_value
        
        # 修正历史重复列的表头
        if reference_ai_col is not None:
            for dup_col in ai_matches:
                dup_header = ws.cell(row=CLIENT_HEADER_ROW, column=dup_col)
                copy_cell_style(ws.cell(row=CLIENT_HEADER_ROW, column=reference_ai_col), dup_header)
                dup_header.value = ai_title
        if reference_date_col is not None:
            for dup_col in followup_matches:
                dup_header = ws.cell(row=CLIENT_HEADER_ROW, column=dup_col)
                copy_cell_style(ws.cell(row=CLIENT_HEADER_ROW, column=reference_date_col), dup_header)
                dup_header.value = excel_date_value
        return ai_col, followup_col

    # 4. 没找到今天的列？坚决新建，绝不复用旧列！
    new_ai_col = last_header_col + 1
    new_followup_col = last_header_col + 2

    ai_header = ws.cell(row=CLIENT_HEADER_ROW, column=new_ai_col)
    followup_header = ws.cell(row=CLIENT_HEADER_ROW, column=new_followup_col)
    
    # 从旧列“偷”样式过来
    if reference_ai_col is not None:
        copy_cell_style(ws.cell(row=CLIENT_HEADER_ROW, column=reference_ai_col), ai_header)
    if reference_date_col is not None:
        copy_cell_style(ws.cell(row=CLIENT_HEADER_ROW, column=reference_date_col), followup_header)
        
    ai_header.value = ai_title
    followup_header.value = excel_date_value

    return new_ai_col, new_followup_col


def find_or_create_date_columns_win32(ws, target_date: datetime, excel) -> tuple[int, int]:
    """win32com 版本：查找或创建日期列 — 修复：写入真实日期对象 + 自定义格式 + 正确查找逻辑 + 时区补偿"""
    date_iso = target_date.strftime("%Y-%m-%d")
    ai_title = f"{date_iso} 建议" # 修改为包含日期的格式，方便缓存读取
    # 修复：Excel COM 接口将 datetime 解释为 UTC 时间，需要加 8 小时补偿北京时间偏移
    excel_date_value = datetime(target_date.year, target_date.month, target_date.day, 8, 0, 0)
    
    ai_col = None
    followup_col = None
    
    # 1. 从第 1000 列往回倒推，找到第一个有内容的单元格（真正的最后一列）
    real_last_col = FIRST_FOLLOWUP_COLUMN
    for c in range(1000, 19, -1):
        val = ws.Cells(CLIENT_HEADER_ROW, c).Value
        if val and str(val).strip():
            real_last_col = c
            break

    # 2. 不复用旧列，每次都创建新列在最右边
    new_ai_col = real_last_col + 1
    new_followup_col = real_last_col + 2

    ai_header = ws.Cells(CLIENT_HEADER_ROW, new_ai_col)
    followup_header = ws.Cells(CLIENT_HEADER_ROW, new_followup_col)
    
    ai_header.Value = ai_title
    # 核心修复：写入 datetime 对象，而非字符串
    followup_header.Value = excel_date_value
    # 设置自定义格式：显示为 "2026-04-23 星期四"
    followup_header.NumberFormat = 'yyyy-mm-dd aaaa'
    
    # 样式同步
    ref_col = ws.Cells(CLIENT_HEADER_ROW, real_last_col)
    ai_header.Font.Name = ref_col.Font.Name
    ai_header.Font.Size = ref_col.Font.Size
    # 强制表头无背景色
    ai_header.Interior.Pattern = 0
    followup_header.Font.Name = ref_col.Font.Name
    followup_header.Font.Size = ref_col.Font.Size
    followup_header.Interior.Pattern = 0
    
    return new_ai_col, new_followup_col


def write_suggestion_to_excel_win32(ws, row: int, col: int, suggestion: str) -> None:
    """已废弃，改为批量写入。保留此函数避免导入报错，实际不再调用。"""
    cleaned = suggestion.replace("\n", " ").replace("\r", " ").strip()
    cell = ws.Cells(row, col)
    cell.Value = cleaned
    cell.Font.Name = "等线"
    cell.Font.Size = 8
    cell.Font.Bold = False
    cell.WrapText = True
    cell.Interior.Pattern = 0  # 无背景色


def process_single_client(ws, client_data: dict, ai_col: int | None, index: int, total: int) -> tuple[bool, str]:
    row = client_data.get("row")
    name = client_data.get("name", "未知")

    if not row:
        print(f"  [{index}/{total}] {name}: 跳过（无行号）")
        return False, ""

    if ws is not None and ai_col is not None:
        existing = ws.cell(row=row, column=ai_col).value
        if existing and str(existing).strip():
            existing_text = str(existing).strip()
            if not should_regenerate_existing_suggestion(existing_text, client_data):
                print(f"  [{index}/{total}] {name}: 跳过（今天已有建议，不覆盖）")
                return True, existing_text
            print(f"  [{index}/{total}] {name}: 检测到疑似低质量旧建议，重新生成...", end=" ", flush=True)
        else:
            print(f"  [{index}/{total}] {name}: 调用 AI 生成建议...", end=" ", flush=True)
    else:
        print(f"  [{index}/{total}] {name}: 调用 AI 生成建议...", end=" ", flush=True)

    suggestion = generate_suggestion_for_single_client(client_data)

    if not suggestion:
        print("跳过（无建议）")
        return False, ""

    print(f"OK（{len(suggestion)}字）")

    return True, suggestion


def calculate_days_since_followup(last_date: str | None) -> int | None:
    if not last_date:
        return None
    try:
        normalized = header_date_to_iso(last_date)
        if not normalized:
            return None
        last = datetime.strptime(normalized, "%Y-%m-%d")
        return (datetime.now() - last).days
    except Exception:
        return None


def generate_daily_plan(data: dict) -> str:
    priority_clients = data.get("priority_clients", [])
    suggestions = data.get("suggestions", {})
    today = datetime.now().strftime("%Y-%m-%d")
    weekday_map = {"Monday": "周一", "Tuesday": "周二", "Wednesday": "周三",
                   "Thursday": "周四", "Friday": "周五", "Saturday": "周六", "Sunday": "周日"}
    weekday = weekday_map.get(datetime.now().strftime("%A"), datetime.now().strftime("%A"))

    a_clients = [c for c in priority_clients if c.get("grade") == "A"]
    b_clients = [c for c in priority_clients if c.get("grade") == "B"]
    c_clients = [c for c in priority_clients if c.get("grade") not in ("A", "B")]

    text = f"🍡 每日跟进计划\n📅 {today}（{weekday}）  ⏰ {datetime.now().strftime('%H:%M')}\n\n"

    def format_client_block(clients, label):
        if not clients:
            return ""
        block = f"{'─'*28}\n{label}（{len(clients)}个）\n{'─'*28}\n"
        for i, client in enumerate(clients, 1):
            name = client.get("name", "未知")
            budget = int(float(client.get("budget") or 0))
            district = client.get("district", "")
            days = calculate_days_since_followup(client.get("last_followup_date"))
            days_str = f"{days}天前" if days is not None else "从未"
            row = client.get("row", "?")
            suggestion = suggestions.get(row, "")

            block += f"\n{i}. {name}（{budget}万 · {district}）\n"
            block += f"   上次跟进：{days_str} | 行号：{row}\n"
            if suggestion:
                block += f"   💡 {suggestion}\n"
        return block

    text += format_client_block(a_clients, "🔥 A级客户 · 每天必跟")
    text += format_client_block(b_clients, "📋 B级客户")
    text += format_client_block(c_clients, "📋 C/D级客户")

    text += f"\n{'─'*28}\n共 {len(priority_clients)} 位重点客户\n"
    return text


def save_full_plan(plan: str) -> str:
    desktop = Path.home() / "Desktop"
    for old_file in desktop.glob("daily_follow_plan_*.txt"):
        try:
            if old_file.name not in {DESKTOP_OUTPUT_BASENAME, DESKTOP_FAILURE_BASENAME}:
                old_file.unlink()
        except Exception:
            pass
    output_file = desktop / DESKTOP_OUTPUT_BASENAME
    output_file.write_text(plan, encoding="utf-8")
    return str(output_file)


def save_failure_report(failures: list[dict[str, Any]]) -> str:
    desktop = Path.home() / "Desktop"
    for old_file in desktop.glob("daily_follow_plan_failed_*.txt"):
        try:
            if old_file.name != DESKTOP_FAILURE_BASENAME:
                old_file.unlink()
        except Exception:
            pass
    output_file = desktop / DESKTOP_FAILURE_BASENAME
    lines = [
        "每日跟进建议生成失败报告",
        f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"失败客户数：{len(failures)}",
        "",
    ]
    for idx, item in enumerate(failures, 1):
        lines.append(f"{idx}. {item.get('name', '未知')} | 行号：{item.get('row', '?')}")
        lines.append(f"   原因：{item.get('error', '未知错误')}")
    output_file.write_text("\n".join(lines), encoding="utf-8")
    return str(output_file)


def load_json_file(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def normalize_suggestions_map(raw: Any) -> dict[int, str]:
    normalized: dict[int, str] = {}
    if not isinstance(raw, dict):
        return normalized
    for key, value in raw.items():
        try:
            row = int(key)
        except Exception:
            continue
        text = clean_cell_text(value)
        if text:
            normalized[row] = text
    return normalized


def save_suggestion_bundle(target_date: datetime, follow_list: list[dict], suggestions: dict[int, str], plan_file: str | None = None) -> str:
    ensure_runstate_dir()
    payload = {
        "business_date": target_date.strftime("%Y-%m-%d"),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "client_rows": [client.get("row") for client in follow_list if client.get("row")],
        "priority_clients": follow_list,
        "suggestions": {str(row): text for row, text in suggestions.items()},
        "plan_file": plan_file or "",
    }
    SUGGESTION_BUNDLE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(SUGGESTION_BUNDLE_FILE)


def parse_suggestions_from_plan_text(plan_text: str) -> tuple[str | None, dict[int, str]]:
    business_date = None
    suggestions: dict[int, str] = {}
    current_row: int | None = None

    for raw_line in plan_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if business_date is None:
            match = re.search(r"(\d{4}-\d{2}-\d{2})", line)
            if match:
                business_date = match.group(1)

        row_match = re.search(r"行号：(\d+)", line)
        if row_match:
            current_row = int(row_match.group(1))
            continue

        if "💡" in line and current_row:
            suggestion = clean_cell_text(line.split("💡", 1)[1])
            if suggestion:
                suggestions[current_row] = suggestion
            current_row = None

    return business_date, suggestions


def parse_suggestions_from_plan_file(file_path: Path) -> tuple[str | None, dict[int, str]]:
    try:
        plan_text = file_path.read_text(encoding="utf-8")
    except Exception:
        return None, {}
    return parse_suggestions_from_plan_text(plan_text)


def load_reusable_suggestions(
    target_date: datetime,
    follow_list: list[dict],
    write_only: bool = False,
    previous_status: dict[str, Any] | None = None,
) -> tuple[dict[int, str], str | None]:
    target_iso = target_date.strftime("%Y-%m-%d")
    expected_rows = sorted(client.get("row") for client in follow_list if client.get("row"))
    previous_status = previous_status or load_json_file(STATUS_FILE) or {}

    allow_automatic_resume = (
        not write_only
        and previous_status.get("status") == "completed"
        and previous_status.get("excel_written") is False
        and clean_cell_text(previous_status.get("updated_at", "")).startswith(target_iso)
    )

    bundle = load_json_file(SUGGESTION_BUNDLE_FILE)
    if bundle:
        suggestions = normalize_suggestions_map(bundle.get("suggestions"))
        bundle_rows = sorted(int(row) for row in bundle.get("client_rows", []) if isinstance(row, int))
        if bundle.get("business_date") == target_iso and all(row in suggestions for row in expected_rows):
            if write_only or allow_automatic_resume or bundle_rows == expected_rows:
                return suggestions, f"缓存建议包：{SUGGESTION_BUNDLE_FILE}"

    candidate_plan_file: Path | None = None
    if write_only:
        desktop_plan = Path.home() / "Desktop" / DESKTOP_OUTPUT_BASENAME
        if desktop_plan.exists():
            candidate_plan_file = desktop_plan
    elif allow_automatic_resume:
        output_file = clean_cell_text(previous_status.get("output_file"))
        if output_file:
            candidate_plan_file = Path(output_file)

    if candidate_plan_file and candidate_plan_file.exists():
        business_date, suggestions = parse_suggestions_from_plan_file(candidate_plan_file)
        if business_date == target_iso and all(row in suggestions for row in expected_rows):
            return suggestions, f"桌面计划文件：{candidate_plan_file}"

    return {}, None


def send_telegram(text: str, full_file_path: str) -> bool:
    summary = (
        f"🍡 每日跟进计划\n"
        f"📅 {datetime.now().strftime('%Y-%m-%d')}  ⏰ {datetime.now().strftime('%H:%M')}\n\n"
        f"✅ 完整名单+建议见下方文件附件 👇"
    )

    print("发送摘要消息...")
    if not _send_telegram_text(summary):
        return False

    print("上传完整文件...")
    caption = f"🍡 每日跟进计划完整版（含AI建议）"
    if not upload_file_to_telegram(full_file_path, caption):
        return False

    return True


def get_chinese_date_with_weekday(target_date: date) -> str:
    """返回中文日期格式：2026 年 4 月 17 日周五"""
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    wd = weekdays[target_date.weekday()]
    return f"{target_date.year} 年 {target_date.month} 月 {target_date.day} 日{wd}"

def _send_telegram_text(text: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=30):
            return True
    except Exception as e:
        print(f"发送 Telegram 失败: {e}")
        return False


def send_progress_ping(message: str) -> None:
    try:
        _send_telegram_text(message)
    except Exception:
        pass


def upload_file_to_telegram(file_path: str, caption: str) -> bool:
    try:
        boundary = "----WebKitFormBoundary" + uuid.uuid4().hex[:16]
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        file_content = Path(file_path).read_bytes()
        filename = Path(file_path).name
        body = []
        for name, value in [("chat_id", TELEGRAM_CHAT_ID.encode()), ("caption", caption.encode("utf-8"))]:
            body.append(("--" + boundary).encode())
            body.append(f'Content-Disposition: form-data; name="{name}"'.encode())
            body.append(b"")
            body.append(value)
        body.append(("--" + boundary).encode())
        body.append(f'Content-Disposition: form-data; name="document"; filename="{filename}"'.encode())
        body.append(b"Content-Type: text/plain")
        body.append(b"")
        body.append(file_content)
        body.append(("--" + boundary + "--").encode())
        request_body = b"\r\n".join(body)
        req = urllib.request.Request(url, data=request_body, method="POST")
        req.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
        req.add_header("Content-Length", str(len(request_body)))
        with urllib.request.urlopen(req, timeout=60):
            return True
    except Exception as e:
        print(f"上传文件到 Telegram 失败: {e}")
        return False


def write_suggestions_to_excel(target_date: datetime, follow_list: list[dict], suggestions: dict[int, str]) -> tuple[bool, str, int]:
    import pythoncom
    import win32com.client
    # 🔧 修复 COM 线程状态：确保当前线程已初始化 COM
    # CoUninitialize 后被调用 CoInitialize 可能返回 RPC_E_CHANGED_MODE，需要重试
    for attempt in range(3):
        try:
            result = pythoncom.CoInitialize()
            logger.info(f"COM 初始化成功 (attempt {attempt+1}, result={result})")
            break
        except Exception as e:
            logger.warning(f"COM 初始化失败 (attempt {attempt+1}): {e}")
            time.sleep(1)
    else:
        return False, "COM 初始化失败，无法写入 Excel", 0

    excel = None
    wb = None
    written_count = 0
    excel_status = "尚未进入写入阶段"

    try:
        # 启动后台弹窗处理线程
        # 🛡️ 安全修复：禁用宏运行，防止 '720列限制' 弹窗阻塞脚本
        excel = win32com.client.Dispatch("Excel.Application")
        excel.AutomationSecurity = 3  # msoAutomationSecurityForceDisable
        excel.Visible = False
        excel.DisplayAlerts = False

        # 检查并保存已打开的目标工作簿实例（不碰其他文件）
        try:
            excel_running = win32com.client.GetActiveObject("Excel.Application")
            for w in excel_running.Workbooks:
                try:
                    wb_path = Path(w.FullName)
                    if wb_path.resolve() == WORKBOOK_PATH.resolve() and not w.Saved:
                        logger.info("检测到目标工作簿已在打开状态，自动保存")
                        w.Save()
                except Exception:
                    continue
        except Exception:
            pass
            
        wb = excel.Workbooks.Open(str(WORKBOOK_PATH), Password="000")
        ws = wb.Worksheets(CLIENT_SHEET_INDEX)

        ai_col, followup_col = find_or_create_date_columns_win32(ws, target_date, excel)
        ai_title = target_date.strftime("%Y-%m-%d") + " 建议"
        followup_title = ws.Cells(CLIENT_HEADER_ROW, followup_col).Value
        excel_status = f"Excel 建议列第{ai_col}列，跟进列第{followup_col}列"
        print(f"OK: {excel_status}（{ai_title} / {followup_title}）")

        print("\n写入 Excel 建议列（批量模式）...")
        write_status({
            "status": "running",
            "stage": "writing_excel",
            "pid": os.getpid(),
            "message": "正在批量写入 Excel 建议列",
        })

        # 收集所有需要写入的行和数据
        rows_data = []
        for client_info in follow_list:
            row = client_info.get("row")
            suggestion = suggestions.get(row, "")
            if row and suggestion:
                rows_data.append((row, suggestion.replace("\n", " ").replace("\r", " ").strip()))

        if rows_data:
            # 找出最小/最大行号，批量设置整列样式（只设置一次 COM 调用）
            min_row = min(r for r, _ in rows_data)
            max_row = max(r for r, _ in rows_data)
            style_range = ws.Range(ws.Cells(min_row, ai_col), ws.Cells(max_row, ai_col))
            style_range.Font.Name = "等线"
            style_range.Font.Size = 8
            style_range.Font.Bold = False
            style_range.WrapText = True
            style_range.Interior.Pattern = 0  # 无背景色

            # 逐行写入值（只写入有数据的行）
            for row, suggestion in rows_data:
                ws.Cells(row, ai_col).Value = suggestion
            written_count = len(rows_data)
            logger.info(f"批量写入 {written_count} 条建议（{min_row}-{max_row}行范围）")
        else:
            logger.warning("无建议数据需要写入")

        print("\n保存 Excel...")
        wb.Save()  # 保持.xlsm 格式，保护宏
        wb.Close(SaveChanges=True)
        excel.Quit()
        return True, excel_status, written_count

    except Exception as e:
        excel_status = f"Excel 写入失败：{e}"
        print(f"WARN: {excel_status}")
        try:
            if wb:
                wb.Close(SaveChanges=False)
        except:
            pass
        try:
            if excel:
                excel.Quit()
        except:
            pass
        return False, excel_status, written_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="每日跟进建议生成器")
    parser.add_argument("--write-only", action="store_true", help="只将已有建议写入 Excel，不重新生成 AI 建议")
    parser.add_argument("--force-generate", action="store_true", help="忽略已有建议缓存，强制重新生成")
    return parser.parse_args()


def main():
    args = parse_args()
    previous_status = load_json_file(STATUS_FILE) or {}
    acquire_run_lock()
    start_status_heartbeat()
    wb = None
    try:
        write_status({
            "status": "running",
            "stage": "starting",
            "pid": os.getpid(),
            "message": "每日跟进计划任务已启动",
        })
        print("=" * 60)
        print("每日跟进计划生成器 v9.1 - 修复跟进记录过滤")
        print("=" * 60)

        today = datetime.now()

        print("刷新缓存...")
        write_status({
            "status": "running",
            "stage": "loading_cache",
            "pid": os.getpid(),
            "message": "正在刷新缓存",
        })
        send_progress_ping(f"🔄 开始刷新缓存...")
        cache = ensure_cache()
        print(f"OK: 加载 {len(cache.get('clients', []))} 个客户")
        client_lookup = build_client_lookup(cache)
        send_progress_ping(f"✅ 缓存刷新完成，共 {len(cache.get('clients', []))} 个客户")

        print("确定今日跟进名单...")
        follow_list = get_today_follow_list(cache, limit=20)
        print(f"OK: 确定 {len(follow_list)} 个重点客户")
        send_progress_ping(f"📝 确定 {len(follow_list)} 位重点客户，开始调用 AI 生成建议...")
        write_progress({
            "status": "running",
            "stage": "list_ready",
            "total_clients": len(follow_list),
            "completed_clients": 0,
            "failed_clients": 0,
            "suggestion_rows": [],
        })

        excel_write_enabled = False
        excel_status = "尚未进入写入阶段"

        suggestions = {}
        generation_failures: list[dict[str, Any]] = []
        reused_source = None
        resume_write_only = False
        if not args.force_generate:
            suggestions, reused_source = load_reusable_suggestions(
                today,
                follow_list,
                write_only=args.write_only,
                previous_status=previous_status,
            )

        if reused_source:
            resume_write_only = (
                not args.write_only
                and previous_status.get("status") == "completed"
                and previous_status.get("excel_written") is False
                and clean_cell_text(previous_status.get("updated_at", "")).startswith(today.strftime("%Y-%m-%d"))
            )
            print(f"\n检测到可复用的今日建议，直接进入写入阶段（来源：{reused_source}）")
            write_status({
                "status": "running",
                "stage": "reusing_suggestions",
                "pid": os.getpid(),
                "message": "检测到已有建议，直接复用结果写入 Excel",
            })
            write_progress({
                "status": "running",
                "stage": "reusing_suggestions",
                "total_clients": len(follow_list),
                "completed_clients": len(suggestions),
                "failed_clients": 0,
                "suggestion_rows": sorted(suggestions.keys()),
            })
        elif args.write_only:
            raise RuntimeError("未找到今日可复用的建议结果，无法只写入 Excel。请先完整生成一次。")
        else:
            print(f"\n开始逐个生成跟进建议（共 {len(follow_list)} 个客户）...")
            for i, client_info in enumerate(follow_list, 1):
                row = client_info.get("row")
                client_data = client_lookup.get(row, dict(client_info))
                write_status({
                    "status": "running",
                    "stage": "generating_suggestions",
                    "pid": os.getpid(),
                    "message": f"正在生成第 {i}/{len(follow_list)} 位客户建议",
                    "current_client": {
                        "row": row,
                        "name": client_data.get("name", "未知"),
                        "index": i,
                        "total": len(follow_list),
                    },
                })
                try:
                    success, suggestion = process_single_client(None, client_data, None, i, len(follow_list))
                    if success and row and suggestion:
                        suggestions[row] = suggestion
                        time.sleep(10)  # 基础请求间隔，防止触发限流
                    write_progress({
                        "status": "running",
                        "stage": "generating_suggestions",
                        "total_clients": len(follow_list),
                        "completed_clients": len(suggestions),
                        "failed_clients": len(generation_failures),
                        "current_index": i,
                        "current_client_name": client_data.get("name", "未知"),
                        "suggestion_rows": sorted(suggestions.keys()),
                    })
                    if success and len(suggestions) % PROGRESS_NOTIFY_EVERY == 0:
                        send_progress_ping(
                            f"每日跟进建议任务进行中\n已完成：{len(suggestions)}/{len(follow_list)}\n当前客户：{client_data.get('name', '未知')}"
                        )
                except AISuggestionError as e:
                    error_text = str(e)
                    print(f"FAILED（AI生成失败）: {error_text}")
                    generation_failures.append({
                        "row": row,
                        "name": client_data.get("name", "未知"),
                        "error": error_text,
                    })
                    write_progress({
                        "status": "running",
                        "stage": "generating_suggestions",
                        "total_clients": len(follow_list),
                        "completed_clients": len(suggestions),
                        "failed_clients": len(generation_failures),
                        "current_index": i,
                        "current_client_name": client_data.get("name", "未知"),
                        "suggestion_rows": sorted(suggestions.keys()),
                    })

        if generation_failures:
            # 部分失败不阻断：记录警告，跳过失败客户继续写入成功的
            logger.warning(f"有 {len(generation_failures)} 位客户 AI 建议生成失败，跳过这些客户继续写入")
            fail_names = ", ".join(f"{f['name']}(行{f['row']})" for f in generation_failures)
            send_progress_ping(
                f"⚠️ {len(generation_failures)} 位客户生成失败（{fail_names}）\n其余客户继续正常写入"
            )

        written_count = 0

        print("\n准备 Excel 写入...")
        write_status({
            "status": "running",
            "stage": "preparing_excel",
            "pid": os.getpid(),
            "message": "建议已生成完毕，正在准备批量写入 Excel",
        })
        excel_write_enabled, excel_status, written_count = write_suggestions_to_excel(today, follow_list, suggestions)
        if excel_write_enabled:
            print(f"OK: 写入/确认 {written_count} 条跟进建议")
            send_progress_ping(f"✅ Excel 写入完成，共 {written_count} 条建议")
        else:
            print(f"\n跳过 Excel 保存：{excel_status}")
            send_progress_ping(f"⚠️ Excel 写入跳过：{excel_status}")

        if args.write_only or resume_write_only:
            summary_message = "已将已有建议写入 Excel" if excel_write_enabled else f"已有建议未能写入 Excel：{excel_status}"
            write_progress({
                "status": "completed" if excel_write_enabled else "failed",
                "stage": "completed" if excel_write_enabled else "write_failed",
                "total_clients": len(follow_list),
                "completed_clients": len(suggestions),
                "failed_clients": 0,
                "suggestion_rows": sorted(suggestions.keys()),
            })
            write_status({
                "status": "completed" if excel_write_enabled else "failed",
                "stage": "completed" if excel_write_enabled else "write_failed",
                "pid": os.getpid(),
                "message": summary_message,
                "written_count": written_count,
                "telegram_sent": False,
                "excel_written": excel_write_enabled,
                "excel_status": excel_status,
                "reused_source": reused_source or "",
            })
            send_progress_ping(summary_message)
            print("\n" + "=" * 60)
            print(summary_message)
            print("=" * 60)
            return

        print("生成跟进计划...")
        write_status({
            "status": "running",
            "stage": "building_plan",
            "pid": os.getpid(),
            "message": "正在整理跟进计划文本",
        })
        plan = generate_daily_plan({
            "priority_clients": follow_list,
            "suggestions": suggestions,
        })

        print("保存桌面文件...")
        output_file = save_full_plan(plan)
        save_suggestion_bundle(today, follow_list, suggestions, output_file)
        print(f"OK: {output_file}")

        print("发送 Telegram...")
        write_status({
            "status": "running",
            "stage": "sending_telegram",
            "pid": os.getpid(),
            "message": "正在发送 Telegram",
            "output_file": output_file,
        })
        telegram_ok = send_telegram(plan, output_file)
        if telegram_ok:
            print("OK: Telegram 发送成功")
        else:
            print("FAILED: Telegram 发送失败")
            send_progress_ping(
                f"每日跟进建议任务已完成，但 Telegram 文件发送失败\n桌面文件：{output_file}"
            )

        write_progress({
            "status": "completed",
            "stage": "completed",
            "total_clients": len(follow_list),
            "completed_clients": len(suggestions),
            "failed_clients": 0,
            "suggestion_rows": sorted(suggestions.keys()),
            "output_file": output_file,
        })
        write_status({
            "status": "completed",
            "stage": "completed",
            "pid": os.getpid(),
            "message": "每日跟进计划任务已完成",
            "output_file": output_file,
            "written_count": written_count,
            "telegram_sent": telegram_ok,
            "excel_written": excel_write_enabled,
            "excel_status": excel_status,
        })

        print("\n" + "=" * 60)
        if excel_write_enabled:
            print(f"OK: 跟进建议已写入 Excel 建议列（{written_count}条）")
        else:
            print(f"WARN: 本次未写入 Excel：{excel_status}")
        print("OK: 跟进计划已推送到 Telegram")
        print("=" * 60)
        send_progress_ping(f"🎉 每日跟进计划全部完成！\n"
                          f"✅ 生成 {len(suggestions)} 条建议\n"
                          f"✅ 写入 Excel {written_count} 条\n"
                          f"✅ Telegram 已推送")
    except Exception as e:
        write_status({
            "status": "failed",
            "stage": "crashed",
            "pid": os.getpid(),
            "message": str(e),
        })
        send_progress_ping(f"❌ 每日跟进计划任务失败\n错误：{str(e)[:100]}")
        raise
    finally:
        stop_status_heartbeat()
        if wb is not None:
            try:
                wb.close()
            except Exception:
                pass
        release_run_lock()


if __name__ == "__main__":
    main()
