# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
房源详情查询单入口脚本。

唯一正式入口：
    cmd /c D:\ExcelData\RUN_HOUSE_DETAIL.cmd "帮我查看 107114497878 这套"
"""

from __future__ import annotations

import io
import json
import os
import re
import socket
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import win32com.client
from selenium import webdriver
from selenium.common.exceptions import JavascriptException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


ROOT_DIR = Path(r"D:\ExcelData")
RUNTIME_DIR = ROOT_DIR / "_house_grab_runtime"
LOG_DIR = ROOT_DIR / "_house_grab_logs"
WORKBOOK_PATH = ROOT_DIR / "daily_followup.xlsm"
DATA_JSON = RUNTIME_DIR / "data.json"
DETAIL_RESULT_JSON = RUNTIME_DIR / "last_house_detail.json"
DETAIL_RESULT_TXT = RUNTIME_DIR / "last_house_detail.txt"
LOG_FILE = LOG_DIR / "house_detail.log"
START_CHROME_SCRIPT = ROOT_DIR / "start_chrome_worker.ps1"

DEBUG_HOST = "127.0.0.1"
DEBUG_PORT = 9222
DETAIL_URL_TEMPLATE = "https://house.link.lianjia.com/housedel/view?housedelCode={house_id}"
SHEET_INDEX = 4
START_ROW = 4
HOUSE_ID_COLUMN = 13
DETAIL_URL_COLUMN = 14

RAW_DETAIL_JS = r"""
return (() => {
    const bodyText = document.body ? (document.body.innerText || '') : '';
    const tdTexts = Array.from(document.querySelectorAll('td'))
        .map(td => (td.innerText || '').trim())
        .filter(Boolean);
    const followBlocks = Array.from(document.querySelectorAll('.detail-follow-block'))
        .map(block => ({
            valid: !!block.querySelector('.valid-label'),
            time: block.querySelector('.detail-time')?.innerText?.trim() || '',
            content: block.querySelector('.detail-follow-content')?.innerText?.trim() || '',
        }))
        .filter(item => item.time || item.content);
    const reviewTexts = Array.from(document.querySelectorAll('.dianping-content'))
        .map(el => (el.innerText || '').trim())
        .filter(Boolean);

    return {
        url: location.href,
        titleH1: document.querySelector('h1')?.innerText?.trim() || '',
        postUlog: document.querySelector('.post_ulog')?.innerText?.trim() || '',
        priceText: document.querySelector('.price-wrap .price')?.innerText?.trim() || '',
        floorText: document.querySelector('#floor-info-container')?.innerText?.trim() || '',
        bodyText,
        tdTexts,
        followBlocks,
        reviewTexts,
    };
})();
"""

WAIT_STATUS_JS = r"""
return (() => {
    const bodyText = document.body ? (document.body.innerText || '') : '';
    const priceText = document.querySelector('.price-wrap .price')?.innerText?.trim() || '';
    const floorText = document.querySelector('#floor-info-container')?.innerText?.trim() || '';
    const tdTexts = Array.from(document.querySelectorAll('td'))
        .map(td => (td.innerText || '').trim())
        .filter(Boolean);
    const labels = ['所在城区：', '所属商圈：', '建筑类型：', '建成年代：', '车位比例：'];
    const filledLabelCount = tdTexts.filter(text => {
        return labels.some(label => text.startsWith(label) && text.slice(label.length).trim());
    }).length;
    const needLogin =
        /登录|扫码登录/.test(bodyText) ||
        !!document.querySelector('.login-container, .login-panel, .login-wrapper');

    return {
        url: location.href,
        needLogin,
        priceText,
        floorText,
        filledLabelCount,
        bodyText,
    };
})();
"""


class DetailFailure(RuntimeError):
    pass


def log(stage: str, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stage}] {message}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {line}\n")


def write_result(payload: dict[str, Any]) -> None:
    DETAIL_RESULT_JSON.parent.mkdir(parents=True, exist_ok=True)
    DETAIL_RESULT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DETAIL_RESULT_TXT.write_text(payload.get("text", payload.get("message", "")) + "\n", encoding="utf-8")


def direct_run_allowed() -> bool:
    return os.environ.get("HOUSE_DETAIL_CMD_ENTRY") == "1" or "--direct" in sys.argv[1:]


def check_debug_port() -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        return sock.connect_ex((DEBUG_HOST, DEBUG_PORT)) == 0
    finally:
        sock.close()


def launch_debug_chrome(force: bool = False) -> bool:
    if not START_CHROME_SCRIPT.exists():
        log("详情", f"ERROR: 调试 Chrome 启动脚本不存在：{START_CHROME_SCRIPT}")
        return False

    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(START_CHROME_SCRIPT),
    ]
    if force:
        command.append("-Force")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=45,
        )
    except Exception as exc:
        log("详情", f"ERROR: 启动调试 Chrome 失败：{exc}")
        return False

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if stdout:
        log("详情", f"调试启动输出：{stdout}")
    if stderr:
        log("详情", f"调试启动错误：{stderr}")
    return result.returncode == 0 and check_debug_port()


def create_driver() -> WebDriver:
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"{DEBUG_HOST}:{DEBUG_PORT}")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    driver.set_script_timeout(60)
    return driver


def normalize_text(value: Any) -> str:
    text = str(value or "").strip().replace("\u3000", " ")
    return "".join(text.split()).lower()


def normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def extract_house_id(value: Any) -> str:
    match = re.search(r"(\d{12})", str(value or ""))
    return match.group(1) if match else ""


def parse_hyperlink_formula(value: Any) -> tuple[str, str]:
    text = str(value or "").strip()
    if not text.startswith("=HYPERLINK("):
        return "", ""
    match = re.match(r'=HYPERLINK\("([^"]*)","([^"]*)"\)', text, flags=re.IGNORECASE)
    if not match:
        return "", ""
    return match.group(2), match.group(1)


def build_record(
    *,
    house_id: str,
    block_code: str,
    community_name: str,
    district: str,
    detail_url: str,
    source: str,
    price: Any = "",
    score: Any = "",
    row_number: Optional[int] = None,
) -> dict[str, Any]:
    return {
        "house_id": str(house_id or "").strip(),
        "block_code": str(block_code or "").strip(),
        "community_name": str(community_name or "").strip(),
        "district": str(district or "").strip(),
        "detail_url": str(detail_url or "").strip(),
        "source": source,
        "price": price,
        "score": score,
        "row_number": row_number,
    }


def load_records_from_data_json() -> list[dict[str, Any]]:
    if not DATA_JSON.exists():
        return []

    try:
        data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    records: list[dict[str, Any]] = []
    for item in data:
        house_id = str(item.get("house_id", "") or "").strip()
        block_code = str(item.get("block_code", "") or "").strip()
        community_name = str(item.get("community_name", "") or item.get("community", "") or "").strip()
        district = str(item.get("district", "") or "").strip()
        detail_url = str(item.get("url", "") or "").strip()
        if not detail_url and house_id:
            detail_url = DETAIL_URL_TEMPLATE.format(house_id=house_id)
        if not house_id and not block_code and not community_name:
            continue
        records.append(
            build_record(
                house_id=house_id or extract_house_id(block_code),
                block_code=block_code,
                community_name=community_name,
                district=district,
                detail_url=detail_url,
                source="data_json",
                price=item.get("price_text", item.get("price", "")),
                score=item.get("score_text", item.get("score", "")),
            )
        )
    return records


def load_records_from_workbook() -> list[dict[str, Any]]:
    if not WORKBOOK_PATH.exists():
        return []

    excel = None
    wb = None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        wb = excel.Workbooks.Open(str(WORKBOOK_PATH), Password="000")
        
        ws = wb.Worksheets(SHEET_INDEX)
        records: list[dict[str, Any]] = []
        last_row = ws.UsedRange.Rows.Count

        for row_index in range(START_ROW, last_row + 1):
            block_code = str(ws.Cells(row_index, 2).Value or "").strip()
            community_formula = ws.Cells(row_index, 3).Value
            community_name, community_url = parse_hyperlink_formula(community_formula)
            district = str(ws.Cells(row_index, 1).Value or "").strip()
            house_id = str(ws.Cells(row_index, HOUSE_ID_COLUMN).Value or "").strip()
            detail_url = str(ws.Cells(row_index, DETAIL_URL_COLUMN).Value or "").strip()

            if not house_id:
                house_id = extract_house_id(block_code) or extract_house_id(community_url)
            if not detail_url and house_id:
                detail_url = DETAIL_URL_TEMPLATE.format(house_id=house_id)
            if not any([house_id, block_code, community_name]):
                continue

            records.append(
                build_record(
                    house_id=house_id,
                    block_code=block_code,
                    community_name=community_name,
                    district=district,
                    detail_url=detail_url,
                    source="workbook",
                    price=ws.Cells(row_index, 6).Value,
                    score=ws.Cells(row_index, 9).Value,
                    row_number=row_index,
                )
            )
        return records
    except Exception:
        return []
    finally:
        try:
            if wb:
                wb.Close(SaveChanges=False)
            if excel:
                excel.Quit()
        except:
            pass


def dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for record in records:
        key = (
            record.get("house_id", ""),
            record.get("block_code", ""),
            record.get("community_name", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped


def build_search_text(record: dict[str, Any]) -> str:
    parts = [
        record.get("house_id", ""),
        record.get("block_code", ""),
        record.get("community_name", ""),
        record.get("district", ""),
    ]
    return normalize_text(" ".join(str(part or "") for part in parts))


def resolve_query(query: str) -> tuple[str, Optional[dict[str, Any]], list[dict[str, Any]]]:
    query = (query or "").strip()
    if not query:
        raise DetailFailure("查询内容为空")

    records = dedupe_records(load_records_from_data_json() + load_records_from_workbook())
    query_house_id = extract_house_id(query)
    if query_house_id:
        for record in records:
            if record.get("house_id") == query_house_id:
                return query_house_id, record, []
        return (
            query_house_id,
            build_record(
                house_id=query_house_id,
                block_code=query_house_id,
                community_name="",
                district="",
                detail_url=DETAIL_URL_TEMPLATE.format(house_id=query_house_id),
                source="query_direct",
            ),
            [],
        )

    normalized_query = normalize_text(query)
    if not normalized_query:
        raise DetailFailure("无法从查询中提取有效关键词")

    exact_matches: list[dict[str, Any]] = []
    fuzzy_matches: list[dict[str, Any]] = []

    for record in records:
        search_text = build_search_text(record)
        if not search_text:
            continue

        if normalized_query == normalize_text(record.get("block_code")):
            exact_matches.append(record)
            continue
        if normalized_query == normalize_text(record.get("community_name")):
            exact_matches.append(record)
            continue
        if normalized_query in search_text:
            fuzzy_matches.append(record)

    if len(exact_matches) == 1:
        return exact_matches[0]["house_id"], exact_matches[0], []
    if len(exact_matches) > 1:
        return "", None, exact_matches[:8]
    if len(fuzzy_matches) == 1:
        return fuzzy_matches[0]["house_id"], fuzzy_matches[0], []
    if len(fuzzy_matches) > 1:
        return "", None, fuzzy_matches[:8]

    raise DetailFailure("未找到匹配房源，请提供 12 位房源编号，或更完整的小区名/板块编号")


def format_candidate(record: dict[str, Any]) -> str:
    community = record.get("community_name") or "--"
    block_code = record.get("block_code") or "--"
    district = record.get("district") or "--"
    house_id = record.get("house_id") or "--"
    price = record.get("price") or "--"
    return f"{district} | {community} | {block_code} | house_id={house_id} | 总价={price}"


def wait_for_detail_page(driver: WebDriver, timeout: float = 45.0) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            state = driver.execute_script(WAIT_STATUS_JS) or {}
        except JavascriptException:
            time.sleep(1)
            continue

        current_url = str(state.get("url", "") or "")
        body_text = str(state.get("bodyText", "") or "")
        price_text = str(state.get("priceText", "") or "")
        floor_text = str(state.get("floorText", "") or "")
        filled_label_count = int(state.get("filledLabelCount", 0) or 0)

        if state.get("needLogin") or "login" in current_url.lower():
            return "login"

        price_ready = bool(re.search(r"\d", price_text))
        floor_ready = bool(normalize_space(floor_text))
        body_ready = any(token in body_text for token in ["产权面积：", "维护人：", "小区信息：", "是否唯一："])
        td_ready = filled_label_count >= 3

        if price_ready and (floor_ready or body_ready or td_ready):
            return "ready"

        time.sleep(1)
    return "timeout"


def parse_lines(body_text: str) -> list[str]:
    return [line.strip() for line in str(body_text or "").splitlines() if line.strip()]


def find_line_value(lines: list[str], label: str) -> str:
    for index, line in enumerate(lines):
        if label not in line:
            continue

        if line.startswith(label):
            suffix = line[len(label) :].strip()
            if suffix:
                return suffix

        if line == label or line.endswith(label):
            for next_line in lines[index + 1 :]:
                candidate = normalize_space(next_line)
                if not candidate:
                    continue
                if candidate in {"收起", "举报", "上传", "<", ">"}:
                    continue
                if candidate.endswith("："):
                    continue
                return candidate

        _, _, suffix = line.partition(label)
        if suffix:
            candidate = normalize_space(suffix)
            if candidate:
                return candidate

    return ""


def find_regex_group(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return ""
    return normalize_space(match.group(1))


def parse_label_map(body_text: str, td_texts: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    candidates = list(td_texts)
    candidates.extend(line for line in str(body_text or "").splitlines() if line.strip())

    for text in candidates:
        for segment in re.split(r"[\t\n]+", str(text)):
            segment = normalize_space(segment)
            if "：" not in segment:
                continue
            label, value = segment.split("：", 1)
            label = f"{label.strip()}："
            value = value.strip()
            if label and value and label not in mapping:
                mapping[label] = value
    return mapping


def parse_follow_items(raw_items: list[dict[str, Any]]) -> str:
    valid_items: list[tuple[float, str, str]] = []
    now = datetime.now()

    for item in raw_items:
        if not item.get("valid"):
            continue
        time_text = normalize_space(item.get("time"))
        content = normalize_space(item.get("content"))
        if not time_text or not content:
            continue

        try:
            if re.match(r"^\d{4}-\d{2}-\d{2}", time_text):
                parsed = datetime.fromisoformat(time_text.replace(" ", "T"))
            else:
                parsed = datetime.fromisoformat(f"{now.year}-{time_text}".replace(" ", "T"))
                if parsed > now:
                    parsed = parsed.replace(year=parsed.year - 1)
            sort_key = parsed.timestamp()
        except Exception:
            sort_key = 0.0

        valid_items.append((sort_key, time_text, content))

    valid_items.sort(key=lambda item: item[0], reverse=True)

    deduped: list[str] = []
    seen_contents: set[str] = set()
    for _, time_text, content in valid_items:
        key = normalize_text(content)
        if key in seen_contents:
            continue
        seen_contents.add(key)
        deduped.append(f"房屋跟进日期和状态：{time_text}\n{content}")
        if len(deduped) >= 8:
            break

    return "\n\n".join(deduped)


def extract_section(lines: list[str], start_markers: list[str], end_markers: list[str]) -> list[str]:
    start_index: Optional[int] = None
    for index, line in enumerate(lines):
        if any(marker in line for marker in start_markers):
            start_index = index + 1
            break
    if start_index is None:
        return []

    section: list[str] = []
    for line in lines[start_index:]:
        if any(marker in line for marker in end_markers):
            break
        if line in {"收起", "举报"}:
            continue
        section.append(line)
    return section


def extract_review_text(snapshot: dict[str, Any], lines: list[str]) -> str:
    review_texts = [normalize_space(item) for item in snapshot.get("reviewTexts", []) if normalize_space(item)]
    if review_texts:
        return "\n\n".join(review_texts)

    section = extract_section(lines, ["经纪人点评"], ["房主自荐", "证件信息"])
    cleaned: list[str] = []
    for line in section:
        if line == "经纪人点评":
            continue
        if line.startswith("(填写内容将在外网展示给用户)"):
            continue
        if line in {"合格", "审核通过，外网可见", "暂无经纪人点评"}:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def resolve_title(snapshot: dict[str, Any], lines: list[str]) -> str:
    for candidate in [snapshot.get("postUlog"), snapshot.get("titleH1")]:
        candidate = normalize_space(candidate)
        if candidate:
            return candidate

    community_line = find_line_value(lines, "小区信息：")
    if community_line:
        community = re.split(r"[\(（]", community_line)[0].strip()
        if community:
            return community

    if lines:
        first_line = lines[0].split("房源编号：")[0].strip()
        first_line = re.sub(r"(不限购|钥匙|满五唯一|满五|唯一|VR房|VR看房|近地铁|随时看房)+", " ", first_line)
        first_line = normalize_space(first_line)
        if first_line:
            return first_line

    return "这套房源"


def parse_detail(snapshot: dict[str, Any], house_id: str) -> dict[str, Any]:
    body_text = str(snapshot.get("bodyText", "") or "")
    td_texts = [str(item or "").strip() for item in snapshot.get("tdTexts", []) if str(item or "").strip()]
    lines = parse_lines(body_text)
    label_map = parse_label_map(body_text, td_texts)

    price_text = normalize_space(snapshot.get("priceText"))
    if price_text and re.search(r"\d", price_text):
        price_value = find_regex_group(price_text, r"([\d.]+)")
        price = f"{price_value}万" if price_value else "--"
    else:
        price = find_line_value(lines, "业主预期价：") or find_line_value(lines, "总价：")
        if price and not price.endswith("万") and re.search(r"\d", price):
            price_value = find_regex_group(price, r"([\d.]+)")
            price = f"{price_value}万" if price_value else price

    area = find_regex_group(body_text, r"产权面积：\s*([\d.]+)\s*平米")
    if area:
        area = f"{area}平"
    if not area:
        area = find_line_value(lines, "面积")
    if area and not area.endswith("平"):
        area = f"{area}平"

    unit_price = find_regex_group(body_text, r"单价[:：]\s*([\d.]+)\s*元/平米")
    if unit_price:
        unit_price = f"{(float(unit_price) / 10000):.2f}万/平"

    floor = normalize_space(snapshot.get("floorText")) or find_line_value(lines, "楼层")
    district = label_map.get("所在城区：") or find_regex_group(body_text, r"所在城区：\s*([^\t\n]+)")
    biz_circle = label_map.get("所属商圈：") or find_regex_group(body_text, r"所属商圈：\s*([^\t\n]+)")
    property_fee = label_map.get("物业费：") or find_regex_group(body_text, r"物业费：\s*([^\t\n]+)")
    building_type = label_map.get("建筑类型：") or find_regex_group(body_text, r"建筑类型：\s*([^\t\n]+)")
    build_year = label_map.get("建成年代：") or find_regex_group(body_text, r"建成年代：\s*([^\t\n]+)")
    lift_ratio = label_map.get("梯户比例：") or find_regex_group(body_text, r"梯户比例：\s*([^\t\n]+)")
    parking_ratio = label_map.get("车位比例：") or find_regex_group(body_text, r"车位比例：\s*([^\t\n]+)")
    parking_fee = label_map.get("停车服务费：") or find_regex_group(body_text, r"停车服务费：\s*([^\t\n]+)")

    unique_value = find_line_value(lines, "是否唯一：")
    full_five = find_line_value(lines, "是否满N：") or find_line_value(lines, "房本日期，满五")
    parking_info = find_line_value(lines, "有无车位：")
    no_parking = parking_info or "无车位"

    follow_text = parse_follow_items(snapshot.get("followBlocks", []))
    review_text = extract_review_text(snapshot, lines)
    title = resolve_title(snapshot, lines)

    critical_filled = sum(
        1
        for value in [price, area, floor, district, biz_circle, building_type]
        if normalize_space(value) not in {"", "--"}
    )
    if critical_filled < 4:
        raise DetailFailure("详情页已打开，但关键信息仍未加载完整，请稍后再试")

    return {
        "needLogin": False,
        "title": title,
        "price": price or "--",
        "unitPrice": unit_price or "--",
        "floor": floor or "--",
        "area": area or "--",
        "district": district or "--",
        "bizCircle": biz_circle or "--",
        "propertyFee": property_fee or "--",
        "buildingType": building_type or "--",
        "buildYear": build_year or "--",
        "liftRatio": lift_ratio or "--",
        "parkingRatio": parking_ratio or "--",
        "parkingFee": parking_fee or "--",
        "uniqueValue": unique_value or "--",
        "fullFive": full_five or "--",
        "noParking": no_parking or "--",
        "follow": follow_text,
        "tags": review_text,
        "url": str(snapshot.get("url", "") or "").strip(),
        "houseId": house_id,
    }


def fetch_house_detail(driver: WebDriver, house_id: str) -> dict[str, Any]:
    target_url = DETAIL_URL_TEMPLATE.format(house_id=house_id)
    original_handle = driver.current_window_handle
    existing_handles = set(driver.window_handles)
    driver.switch_to.new_window("tab")
    new_handle = next(handle for handle in driver.window_handles if handle not in existing_handles)

    try:
        driver.switch_to.window(new_handle)
        driver.get(target_url)
        page_state = wait_for_detail_page(driver)
        if page_state == "login":
            return {"needLogin": True, "url": driver.current_url, "houseId": house_id}
        if page_state == "timeout":
            raise DetailFailure(f"详情页加载超时：{house_id}")

        snapshot = driver.execute_script(RAW_DETAIL_JS)
        if not isinstance(snapshot, dict):
            raise DetailFailure("详情页快照结果无效")
        return parse_detail(snapshot, house_id)
    finally:
        try:
            driver.close()
        except Exception:
            pass
        try:
            driver.switch_to.window(original_handle)
        except Exception:
            pass


def format_detail_text(detail: dict[str, Any], record: Optional[dict[str, Any]], query: str) -> str:
    title = detail.get("title", "这套房源")
    lines = [
        title,
        f"查询词：{query}",
        f"房源编号：{detail.get('houseId', '--')}",
        f"详情链接：{detail.get('url', '--')}",
        "",
        f"总价：{detail.get('price', '--')}",
        f"单价：{detail.get('unitPrice', '--')}",
        f"楼层：{detail.get('floor', '--')}",
        f"面积：{detail.get('area', '--')}",
        "",
        f"所在城区：{detail.get('district', '--')}",
        f"所属商圈：{detail.get('bizCircle', '--')}",
        f"建筑类型：{detail.get('buildingType', '--')}",
        f"建成年代：{detail.get('buildYear', '--')}",
        f"物业费：{detail.get('propertyFee', '--')}",
        f"梯户比例：{detail.get('liftRatio', '--')}",
        f"车位比例：{detail.get('parkingRatio', '--')}",
        f"停车服务费：{detail.get('parkingFee', '--')}",
        f"是否唯一：{detail.get('uniqueValue', '--')}",
        f"房本日期/满五：{detail.get('fullFive', '--')}",
        f"车位情况：{detail.get('noParking', '--')}",
    ]

    if record:
        lines.extend(
            [
                "",
                f"表内板块编号：{record.get('block_code') or '--'}",
                f"表内小区：{record.get('community_name') or '--'}",
                f"数据来源：{record.get('source') or '--'}",
            ]
        )
        if record.get("row_number"):
            lines.append(f"表内行号：{record.get('row_number')}")

    lines.extend(["", "跟进记录：", detail.get("follow") or "无"])
    lines.extend(["", "房源标签/点评：", detail.get("tags") or "无"])
    return "\n".join(lines).strip()


def main() -> int:
    if not direct_run_allowed():
        print('请运行 cmd /c D:\\Unique work form\\RUN_HOUSE_DETAIL.cmd "用户原话"')
        return 2

    query = " ".join(sys.argv[1:]).strip()
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if DETAIL_RESULT_JSON.exists():
        DETAIL_RESULT_JSON.unlink()
    if DETAIL_RESULT_TXT.exists():
        DETAIL_RESULT_TXT.unlink()

    try:
        log("详情", f"开始查询：{query}")
        house_id, record, candidates = resolve_query(query)

        if candidates:
            candidate_lines = [format_candidate(item) for item in candidates]
            payload = {
                "success": False,
                "status": "ambiguous",
                "message": "匹配到多套房源，请提供更精确的房源编号",
                "query": query,
                "candidates": candidate_lines,
                "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": "匹配到多套房源，请指定更精确的房源编号：\n" + "\n".join(candidate_lines),
            }
            write_result(payload)
            return 1

        if not check_debug_port():
            log("详情", "调试端口未就绪，尝试启动专用调试 Chrome")
            if not launch_debug_chrome():
                raise DetailFailure("无法连接专用调试 Chrome，请确认专用浏览器窗口可用并已登录")

        driver = create_driver()
        try:
            detail = fetch_house_detail(driver, house_id)
        finally:
            driver.quit()

        if detail.get("needLogin"):
            payload = {
                "success": False,
                "status": "need_login",
                "message": "请在专用调试 Chrome 窗口扫码登录链家后再试",
                "query": query,
                "house_id": house_id,
                "record": record,
                "detail": detail,
                "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": "请在专用调试 Chrome 窗口扫码登录链家后再试。",
            }
            write_result(payload)
            return 1

        text = format_detail_text(detail, record, query)
        payload = {
            "success": True,
            "status": "success",
            "message": "详情抓取成功",
            "query": query,
            "house_id": house_id,
            "record": record,
            "detail": detail,
            "text": text,
            "started_at": started_at,
            "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        write_result(payload)
        log("详情", f"查询完成：{house_id}")
        return 0

    except DetailFailure as exc:
        message = str(exc)
        log("详情", f"ERROR: {message}")
        payload = {
            "success": False,
            "status": "error",
            "message": message,
            "query": query,
            "started_at": started_at,
            "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": f"详情查询失败：{message}",
        }
        write_result(payload)
        return 1

    except (TimeoutException, WebDriverException) as exc:
        message = f"Selenium 执行失败：{exc}"
        log("详情", f"ERROR: {message}")
        payload = {
            "success": False,
            "status": "error",
            "message": message,
            "query": query,
            "started_at": started_at,
            "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": f"详情查询失败：{message}",
        }
        write_result(payload)
        return 1

    except Exception as exc:
        message = f"未预期错误：{exc}"
        log("详情", f"ERROR: {message}")
        log("详情", traceback.format_exc())
        payload = {
            "success": False,
            "status": "error",
            "message": message,
            "query": query,
            "started_at": started_at,
            "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": f"详情查询失败：{message}",
        }
        write_result(payload)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
