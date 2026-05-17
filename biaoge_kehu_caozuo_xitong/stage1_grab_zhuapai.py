# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
阶段 1：连接可调试 Chrome，在页面内执行与油猴脚本同源的抓取逻辑。

目标：
1. 固定 10 个区按顺序抓取（浦东优先，避免其拖累后续重试）
2. 每个区先切回全城，再设置价格 700-10000（已设置则跳过）
3. 每个区先按房源分降序，再回到第 1 页
4. 全局按真实房源 ID 去重
5. 过滤规则与油猴一致：房源分 >= 6，或最近 3 天/小时内创建
6. 浦东最多抓 33 页
7. 最终结果额外兜底：总价必须在 700-10000 万之间
8. 单区出错自动跳过，全部完成后统一判断是否达到阈值
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

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.common.exceptions import JavascriptException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


ROOT_DIR = Path(r"D:\Unique work form")
RUNTIME_DIR = ROOT_DIR / "_house_grab_runtime"
LOG_DIR = ROOT_DIR / "_house_grab_logs"
DATA_TMP = RUNTIME_DIR / "data.tmp"
DATA_JSON = RUNTIME_DIR / "data.json"
LOG_FILE = LOG_DIR / "house_grab.log"
START_CHROME_SCRIPT = ROOT_DIR / "start_chrome_worker.ps1"

BASE_URL = "https://house.link.lianjia.com/search/sale/default/gdiv_mt"
DEBUG_HOST = "127.0.0.1"
DEBUG_PORT = 9222

MIN_SCORE = 6.0
RECENT_DAYS = 3
MIN_TOTAL_PRICE = 700.0
MAX_TOTAL_PRICE = 10000.0
MAX_PAGES_PUDONG = 33
WAIT_LONG = 8.0
LOGIN_WAIT_SECONDS = 120
DISTRICT_RUN_TIMEOUT = 5400.0
DISTRICT_POLL_INTERVAL = 5.0
DISTRICT_STALL_TIMEOUT = 300.0

# 允许跳过的最大区数，超过则整体失败
MAX_SKIPPABLE_DISTRICTS = 2

# 浦东提前到第一位，避免其耗时拖累后续重试
DISTRICTS = [
    {"id": "radio-310115", "name": "浦东"},
    {"id": "radio-310105", "name": "长宁"},
    {"id": "radio-310106", "name": "静安"},
    {"id": "radio-310101", "name": "黄浦"},
    {"id": "radio-310104", "name": "徐汇"},
    {"id": "radio-310107", "name": "普陀"},
    {"id": "radio-310112", "name": "闵行"},
    {"id": "radio-310109", "name": "虹口"},
    {"id": "radio-310110", "name": "杨浦"},
    {"id": "radio-310114", "name": "嘉定"},
]


def log(stage: str, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stage}] {message}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {line}\n")


def check_debug_port() -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        return sock.connect_ex((DEBUG_HOST, DEBUG_PORT)) == 0
    finally:
        sock.close()


def launch_debug_chrome(force: bool = False) -> bool:
    if not START_CHROME_SCRIPT.exists():
        log("阶段 1", f"ERROR: 调试启动脚本不存在：{START_CHROME_SCRIPT}")
        return False

    command = [
        "powershell",
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
        log("阶段 1", f"ERROR: 启动调试 Chrome 失败：{exc}")
        return False

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if stdout:
        log("阶段 1", f"调试启动输出：{stdout}")
    if stderr:
        log("阶段 1", f"调试启动错误：{stderr}")

    return result.returncode == 0 and check_debug_port()


def create_driver() -> WebDriver:
    """创建 Chrome WebDriver 连接，带重试机制"""
    max_retries = 3
    retry_delay = 2.0

    for attempt in range(1, max_retries + 1):
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"{DEBUG_HOST}:{DEBUG_PORT}")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            log("阶段 1", f"尝试连接 Chrome 调试端口 (尝试 {attempt}/{max_retries})...")
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(60)
            driver.set_script_timeout(3600)

            driver.current_url
            log("阶段 1", "Chrome 连接成功")
            return driver

        except Exception as e:
            log("阶段 1", f"连接失败 (尝试 {attempt}/{max_retries}): {str(e)}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                raise

    raise RuntimeError("无法连接到 Chrome 调试端口")


def wait_for_element(
    driver: WebDriver,
    by: By,
    value: str,
    timeout: float = WAIT_LONG,
) -> Optional[WebElement]:
    try:
        return WebDriverWait(driver, timeout, poll_frequency=0.2).until(
            EC.presence_of_element_located((by, value))
        )
    except TimeoutException:
        return None


def ensure_base_page(driver: WebDriver) -> bool:
    log("阶段 1", f"打开页面：{BASE_URL}")
    try:
        driver.get(BASE_URL)
    except TimeoutException:
        log("阶段 1", "页面加载超时，继续检查当前状态")

    deadline = time.time() + LOGIN_WAIT_SECONDS
    last_state = ""

    while time.time() < deadline:
        district_btn = wait_for_element(driver, By.CSS_SELECTOR, "a#radio-310105", timeout=1.5)
        if district_btn:
            return True

        current_url = (driver.current_url or "").lower()
        try:
            body_text = driver.execute_script("return document.body ? document.body.innerText : '';") or ""
        except JavascriptException:
            body_text = ""

        is_login_page = "login" in current_url or bool(re.search(r"登录|扫码登录", body_text))
        state = "login" if is_login_page else "loading"

        if state != last_state:
            if state == "login":
                log("阶段 1", "检测到登录页，等待你在专用调试窗口完成扫码登录...")
            else:
                log("阶段 1", "页面还在加载或切换中，继续等待列表出现...")
            last_state = state

        time.sleep(2)

    log("阶段 1", f"ERROR: 页面在 {LOGIN_WAIT_SECONDS} 秒内未进入可抓取状态")
    log("阶段 1", "提示：请在专用调试窗口完成登录后重试")
    return False


def safe_text(value: Any, default: str = " ") -> str:
    text = "" if value is None else str(value)
    text = text.strip()
    return text if text else default


def parse_float(value: Any, default: float = 0.0) -> float:
    text = "" if value is None else str(value).strip()
    if not text:
        return default
    text = text.replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return default
    try:
        return float(match.group())
    except ValueError:
        return default


def format_unit_price(price_text: str) -> str:
    value = parse_float(price_text, default=-1.0)
    if value < 0:
        return " "
    return f"{value / 10000:.1f}"


def escape_excel_text(value: str) -> str:
    return value.replace('"', '""')


def build_community_formula(name: str, url: str) -> str:
    if not name or not url:
        return " "
    return f'=HYPERLINK("{escape_excel_text(url)}","{escape_excel_text(name)}")'


def validate_data(houses: list[dict[str, Any]]) -> tuple[bool, str]:
    if not houses:
        return False, "数据为空"

    required_fields = ["title", "price", "area"]
    for index, house in enumerate(houses, start=1):
        for field in required_fields:
            if field not in house:
                return False, f"第 {index} 条数据缺少字段：{field}"

    return True, f"校验通过（{len(houses)} 条）"


def save_data(houses: list[dict[str, Any]]) -> tuple[bool, str]:
    try:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

        with open(DATA_TMP, "w", encoding="utf-8") as handle:
            json.dump(houses, handle, ensure_ascii=False, indent=2)

        with open(DATA_TMP, "r", encoding="utf-8") as handle:
            json.load(handle)

        if DATA_JSON.exists():
            DATA_JSON.unlink()
        DATA_TMP.rename(DATA_JSON)
        return True, f"成功保存 {len(houses)} 条数据"
    except Exception as exc:
        return False, f"保存失败：{exc}"


def install_browser_collector(driver: WebDriver) -> None:
    bootstrap_script = r"""
const districts = arguments[0];
const minScore = arguments[1];
const recentDays = arguments[2];
const minTotalPrice = arguments[3];
const maxTotalPrice = arguments[4];
const maxPagesPudong = arguments[5];

window.__codexHouseCollector = {
    districts,
    minScore,
    recentDays,
    minTotalPrice,
    maxTotalPrice,
    maxPagesPudong,
    seenHouseIds: new Set(),
    districtRunState: null,
    // 价格筛选是否已设置（避免每个区重复设置）
    priceFilterApplied: false,

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    updateDistrictRunState(patch) {
        const previous = this.districtRunState || {};
        this.districtRunState = {
            ...previous,
            ...patch,
            heartbeat: Date.now(),
        };
        return this.districtRunState;
    },

    getDistrictRunState() {
        return this.districtRunState || {
            status: 'idle',
            running: false,
            done: false,
            heartbeat: 0,
        };
    },

    startDistrictRun(district) {
        if (this.districtRunState && this.districtRunState.running) {
            throw new Error(`district_run_already_running:${this.districtRunState.district_name || ''}`);
        }

        const runId = `${district.id}-${Date.now()}`;
        this.districtRunState = {
            run_id: runId,
            district_id: district.id,
            district_name: district.name,
            status: 'running',
            running: true,
            done: false,
            stage: 'starting',
            page_count: 0,
            collected_rows: 0,
            stop_reason: '',
            error: '',
            result: null,
            started_at: Date.now(),
            heartbeat: Date.now(),
        };

        (async () => {
            try {
                const result = await this.processDistrict(district);
                this.updateDistrictRunState({
                    status: 'done',
                    running: false,
                    done: true,
                    stage: 'finished',
                    page_count: result && result.page_count ? result.page_count : 0,
                    collected_rows: result && Array.isArray(result.rows) ? result.rows.length : 0,
                    stop_reason: result && result.stop_reason ? result.stop_reason : '',
                    error: '',
                    result,
                    finished_at: Date.now(),
                });
            } catch (error) {
                this.updateDistrictRunState({
                    status: 'error',
                    running: false,
                    done: true,
                    stage: 'error',
                    error: String(error && error.stack ? error.stack : error),
                    finished_at: Date.now(),
                });
            }
        })();

        return this.getDistrictRunState();
    },

    click(element) {
        if (!element) return false;
        try {
            element.click();
            return true;
        } catch (error) {
            try {
                element.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                return true;
            } catch (innerError) {
                return false;
            }
        }
    },

    getRows() {
        return Array.from(document.querySelectorAll('tr.ked-table-row'));
    },

    getActivePage() {
        const active = document.querySelector('li.ked-pagination-item-active');
        if (!active) return null;
        const value = parseInt((active.innerText || '').trim(), 10);
        return Number.isNaN(value) ? null : value;
    },

    getRowSignature(row) {
        if (!row) return '';

        const links = row.querySelectorAll('a[href*="ershoufang"], a[href*="housedelCode="]');
        for (const link of links) {
            const href = link.href || '';
            const match = href.match(/ershoufang\/(\d{12})(?:\.html|\/|$)/i)
                || href.match(/[?&]housedelCode=(\d{12})(?:&|$)/i);
            if (match && match[1]) return match[1];
        }

        return (row.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 120);
    },

    getTableSignature(limit = 5) {
        const rows = this.getRows().slice(0, limit);
        if (!rows.length) return '';
        return rows
            .map(row => this.getRowSignature(row))
            .filter(Boolean)
            .join('|');
    },

    async waitForTableRendered(maxWait = 8000) {
        const start = Date.now();
        while (Date.now() - start < maxWait) {
            const rows = this.getRows();
            if (rows.length > 0) return rows;
            await this.sleep(100);
        }
        return [];
    },

    async waitForTableChange(previousPage, previousSignature, maxWait = 12000) {
        const start = Date.now();
        while (Date.now() - start < maxWait) {
            const rows = this.getRows();
            if (rows.length > 0) {
                const currentPage = this.getActivePage();
                const currentSignature = this.getTableSignature();
                if (previousSignature) {
                    if (currentSignature && currentSignature !== previousSignature) {
                        return true;
                    }
                } else if (previousPage !== null && currentPage !== null && currentPage !== previousPage) {
                    return true;
                }
            }
            await this.sleep(200);
        }
        return false;
    },

    async waitForDistrictApplied(districtId, previousPage, previousSignature, maxWait = 20000) {
        const start = Date.now();
        while (Date.now() - start < maxWait) {
            const districtBtn = document.querySelector(`a#${districtId}`);
            const active = districtBtn && districtBtn.classList.contains('active');
            const currentPage = this.getActivePage();
            const currentSignature = this.getTableSignature();
            const changedPage = previousPage !== null && currentPage !== null && currentPage !== previousPage;
            const changedSignature = previousSignature && currentSignature && currentSignature !== previousSignature;
            if (active && (changedSignature || (!previousSignature && changedPage))) {
                return true;
            }
            await this.sleep(200);
        }
        return false;
    },

    async waitForExpectedPage(targetPage, previousSignature, maxWait = 30000) {
        const start = Date.now();
        while (Date.now() - start < maxWait) {
            const rows = this.getRows();
            if (rows.length > 0) {
                const currentPage = this.getActivePage();
                const currentSignature = this.getTableSignature();
                if (previousSignature) {
                    if (
                        currentSignature
                        && currentSignature !== previousSignature
                        && (targetPage === null || currentPage === null || currentPage === targetPage)
                    ) {
                        return true;
                    }
                } else if (targetPage !== null && currentPage !== null && currentPage === targetPage) {
                    return true;
                }
            }
            await this.sleep(200);
        }

        const finalPage = this.getActivePage();
        if (previousSignature) {
            const finalSignature = this.getTableSignature();
            return !!(finalSignature && finalSignature !== previousSignature
                && (targetPage === null || finalPage === null || finalPage === targetPage));
        }
        return targetPage !== null && finalPage !== null && finalPage === targetPage;
    },

    async advanceToNextPage(nextButton, currentPageCount) {
        const previousPage = this.getActivePage();
        const previousSignature = this.getTableSignature();
        const targetPage = previousPage !== null ? previousPage + 1 : currentPageCount + 1;

        // 优化：第1次只等5秒，失败再逐步加长，正常翻页2-3秒就够
        const waitTimes = [5000, 12000, 20000];
        for (let attempt = 1; attempt <= 3; attempt += 1) {
            this.click(nextButton);
            const moved = await this.waitForExpectedPage(targetPage, previousSignature, waitTimes[attempt - 1]);
            if (moved) {
                return {
                    ok: true,
                    page: this.getActivePage() || targetPage,
                    signature: this.getTableSignature(),
                };
            }
            await this.sleep(1200 * attempt);
        }

        return {
            ok: false,
            page: this.getActivePage(),
            signature: this.getTableSignature(),
        };
    },

    async waitForElement(selector, timeout = 5000) {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const el = document.querySelector(selector);
            if (el) return el;
            await this.sleep(100);
        }
        return null;
    },

    // 优化：检测价格输入框当前值，已正确则跳过重新设置
    isPriceAlreadySet() {
        const minInput = document.querySelector('#range-price-min');
        const maxInput = document.querySelector('#range-price-max');
        if (!minInput || !maxInput) return false;
        return minInput.value === '700' && maxInput.value === '10000';
    },

    async prepareFullCityAndPrice() {
        const allBtn = document.querySelector('#radio-all');
        if (allBtn && !allBtn.classList.contains('active')) {
            const previousPage = this.getActivePage();
            const previousSignature = this.getTableSignature();
            this.click(allBtn);
            await this.waitForTableChange(previousPage, previousSignature, 6000);
            await this.sleep(800);
            // 切回全城后价格筛选可能被重置，需要重新检查
            this.priceFilterApplied = false;
        }

        // 价格已正确设置则跳过，节省每个区约3-5秒
        if (this.priceFilterApplied && this.isPriceAlreadySet()) {
            return;
        }

        const minInput = await this.waitForElement('#range-price-min', 6000);
        const maxInput = await this.waitForElement('#range-price-max', 6000);
        if (!minInput || !maxInput) {
            throw new Error('未找到价格输入框');
        }

        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;

        minInput.focus();
        nativeSetter.call(minInput, '700');
        minInput.dispatchEvent(new Event('input', { bubbles: true }));

        maxInput.focus();
        nativeSetter.call(maxInput, '10000');
        maxInput.dispatchEvent(new Event('input', { bubbles: true }));

        await this.sleep(600);

        const confirmBtn = Array.from(document.querySelectorAll('button.ant-btn.ant-btn-primary'))
            .find(btn => ((btn.innerText || '').replace(/\s+/g, '') === '确定'));
        if (confirmBtn) {
            const previousPage = this.getActivePage();
            const previousSignature = this.getTableSignature();
            this.click(confirmBtn);
            await this.waitForTableChange(previousPage, previousSignature, 12000);
        }

        await this.waitForTableRendered(8000);
        this.priceFilterApplied = true;
    },

    async sortByScore() {
        const otherSorter = document.querySelector('th.reconfig-visit-count .ked-table-column-sorter-inner');
        if (otherSorter) {
            this.click(otherSorter);
        }

        await this.sleep(1200);

        const scoreCol = document.querySelector('th.reconfig-sys-score .ked-table-column-sorter-inner');
        if (!scoreCol) {
            throw new Error('未找到房源分排序列');
        }

        const downArrow = scoreCol.querySelector('.anticon-caret-down');
        if (downArrow && downArrow.classList.contains('off')) {
            const previousPage = this.getActivePage();
            const previousSignature = this.getTableSignature();
            this.click(downArrow);
            // 优化：等实际表格变化而非固定2.5秒
            await this.waitForTableChange(previousPage, previousSignature, 6000);
        }

        // 保留短暂等待确保排序稳定
        await this.sleep(800);
    },

    findNextButton() {
        const nextCandidates = [
            'li.ked-pagination-next a',
            'li.ked-pagination-next',
            '.ked-pagination-next a',
            '.ked-pagination-next'
        ];

        for (const selector of nextCandidates) {
            const node = document.querySelector(selector);
            if (!node) continue;
            const disabled = node.classList.contains('ked-pagination-disabled')
                || node.classList.contains('disabled')
                || node.getAttribute('aria-disabled') === 'true';
            if (!disabled) return node;
        }

        const svgs = document.querySelectorAll('svg[data-icon="right"]');
        for (const svg of svgs) {
            const parent = svg.closest('a, button, li, div');
            if (parent && !parent.classList.contains('disabled') && !parent.classList.contains('ked-pagination-disabled')) {
                return parent;
            }
        }

        return null;
    },

    extractPageData(rows, districtName) {
        const pageData = [];

        for (const row of rows) {
            let houseId = '';
            let detailUrl = '';

            const possibleLinks = row.querySelectorAll('a[href*="ershoufang"], a[href*="housedelCode="]');
            for (const link of possibleLinks) {
                const href = link.href || '';
                const match = href.match(/ershoufang\/(\d{12})(?:\.html|\/|$)/i)
                    || href.match(/[?&]housedelCode=(\d{12})(?:&|$)/i);
                if (match && match[1]) {
                    houseId = match[1];
                    detailUrl = href;
                    break;
                }
            }

            if (houseId && this.seenHouseIds.has(houseId)) {
                continue;
            }

            if (houseId) {
                this.seenHouseIds.add(houseId);
            }

            const circle = row.querySelector('span.circle-name')?.innerText.trim() || ' ';
            const code = row.querySelector('span.house-code')?.innerText.trim() || ' ';
            const blockCode = circle + code;

            const communityAnchor = row.querySelector('a.community-name');
            const communityName = communityAnchor?.innerText.trim() || ' ';
            const communityUrl = communityAnchor?.href || '';

            const unit = row.querySelector('div.unit-type')?.innerText.trim() || ' ';
            const area = (row.querySelector('div.area-size')?.innerText || '').trim().replace('平', '') || ' ';
            const total = (row.querySelector('div.total-price span')?.innerText || '').trim().replace('万', '') || ' ';
            const priceText = (row.querySelector('div.unit-price span')?.innerText || '').trim().replace('元/平', '') || ' ';
            const floor = row.querySelector('div.floor a')?.innerText.trim() || ' ';
            const scoreStr = row.querySelector('div.sys-score')?.innerText.trim() || '0';
            const createDateStr = row.querySelector('div.create-time')?.innerText.trim() || ' ';

            const agentSpan = row.querySelector('div.maintainer span > span.re-margin');
            const agentLevel = agentSpan?.innerText.trim() || ' ';
            const agentName = agentSpan
                ? ((agentSpan.parentNode?.innerText || '').trim().replace(agentLevel, '').trim() || ' ')
                : ' ';
            const maintainer = `${agentName}${agentLevel}`.trim() || ' ';

            const score = parseFloat(scoreStr) || 0;
            const totalValue = parseFloat(total);

            const recentDayMatch = createDateStr.match(/(\d+)天前/);
            const recentHourMatch = createDateStr.match(/(\d+)小时之前/);
            const isRecent = (recentDayMatch && parseInt(recentDayMatch[1], 10) <= this.recentDays)
                || recentHourMatch;

            if (score < this.minScore && !isRecent) {
                continue;
            }

            if (!Number.isNaN(totalValue) && (totalValue < this.minTotalPrice || totalValue > this.maxTotalPrice)) {
                continue;
            }

            pageData.push({
                district: districtName,
                source_house_id: houseId,
                detail_url: detailUrl || communityUrl,
                plate: circle,
                house_code: code,
                block_code: blockCode,
                community_name: communityName,
                community_url: communityUrl,
                layout: unit,
                area,
                total_price_text: total,
                unit_price_text: priceText,
                floor,
                score_text: scoreStr,
                create_date: createDateStr,
                maintainer
            });
        }

        return pageData;
    },

    async processDistrict(district) {
        this.updateDistrictRunState({
            stage: 'prepare_filters',
            page_count: 0,
            collected_rows: 0,
            stop_reason: '',
        });
        await this.prepareFullCityAndPrice();

        const districtBtn = document.querySelector(`a#${district.id}`);
        if (!districtBtn) {
            throw new Error(`未找到区按钮：${district.id}`);
        }

        if (!districtBtn.classList.contains('active')) {
            const previousPage = this.getActivePage();
            const previousSignature = this.getTableSignature();
            this.click(districtBtn);
            const switched = await this.waitForDistrictApplied(district.id, previousPage, previousSignature, 20000);
            if (!switched) {
                throw new Error(`district_switch_timeout:${district.name}`);
            }
            await this.sleep(800);
        }

        this.updateDistrictRunState({ stage: 'sorting' });
        await this.sortByScore();

        const firstPageBtn = document.querySelector('li.ked-pagination-item-1:not(.ked-pagination-item-active) a');
        if (firstPageBtn) {
            const previousPage = this.getActivePage();
            const previousSignature = this.getTableSignature();
            this.click(firstPageBtn);
            await this.waitForTableChange(previousPage, previousSignature, 8000);
        }

        await this.waitForTableRendered(8000);

        const allRows = [];
        let pageCount = 1;
        const isPudong = district.name === '浦东';
        let lastProcessedSignature = '';
        let lastProcessedPage = null;

        while (true) {
            this.updateDistrictRunState({
                stage: 'collecting',
                page_count: pageCount,
                collected_rows: allRows.length,
            });
            const rows = await this.waitForTableRendered(8000);
            if (!rows.length) {
                return { rows: allRows, page_count: pageCount, stop_reason: 'no_rows' };
            }

            const currentPage = this.getActivePage() || pageCount;
            const currentSignature = this.getTableSignature();
            const pageData = this.extractPageData(rows, district.name);
            if (!pageData.length) {
                const samePageLoadedAgain = (
                    currentSignature
                    && lastProcessedSignature
                    && currentSignature === lastProcessedSignature
                    && lastProcessedPage === currentPage
                );
                if (samePageLoadedAgain) {
                    throw new Error(`pagination_stuck:${district.name}:page=${currentPage}`);
                }
                this.updateDistrictRunState({
                    stage: 'finished',
                    page_count: currentPage,
                    collected_rows: allRows.length,
                    stop_reason: 'no_matching_rows',
                });
                return { rows: allRows, page_count: currentPage, stop_reason: 'no_matching_rows' };
            }

            allRows.push(...pageData);
            lastProcessedPage = currentPage;
            lastProcessedSignature = currentSignature;
            this.updateDistrictRunState({
                stage: 'page_done',
                page_count: currentPage,
                collected_rows: allRows.length,
            });

            const reachPageLimit = isPudong && currentPage >= this.maxPagesPudong;
            const nextButton = this.findNextButton();
            if (nextButton && !reachPageLimit) {
                this.updateDistrictRunState({
                    stage: 'next_page',
                    page_count: currentPage,
                    collected_rows: allRows.length,
                });
                const moveResult = await this.advanceToNextPage(nextButton, currentPage);
                if (!moveResult.ok) {
                    throw new Error(`next_page_timeout:${district.name}:page=${currentPage}`);
                }
                pageCount = moveResult.page || (currentPage + 1);
                await this.sleep(1200);
                continue;
            }

            return {
                rows: allRows,
                page_count: currentPage,
                stop_reason: reachPageLimit ? 'pudong_limit' : 'no_next_button'
            };
        }
    }
};
return true;
"""
    driver.execute_script(
        bootstrap_script,
        DISTRICTS,
        MIN_SCORE,
        RECENT_DAYS,
        MIN_TOTAL_PRICE,
        MAX_TOTAL_PRICE,
        MAX_PAGES_PUDONG,
    )


def collect_district_browser_side(driver: WebDriver, district: dict[str, str]) -> dict[str, Any]:
    start_state = driver.execute_script(
        """
const district = arguments[0];
if (!window.__codexHouseCollector) {
    throw new Error('collector_not_installed');
}
return window.__codexHouseCollector.startDistrictRun(district);
""",
        district,
    )

    if not isinstance(start_state, dict) or start_state.get("status") not in {"running", "done"}:
        raise RuntimeError(f"district_start_failed: {district['name']}")

    deadline = time.time() + DISTRICT_RUN_TIMEOUT
    last_heartbeat_value = None
    last_heartbeat_seen = time.time()
    last_progress_key = None

    while time.time() < deadline:
        state = driver.execute_script(
            """
if (!window.__codexHouseCollector) {
    return null;
}
return window.__codexHouseCollector.getDistrictRunState();
"""
        )

        if not isinstance(state, dict):
            raise RuntimeError(f"district_state_missing: {district['name']}")

        heartbeat_value = state.get("heartbeat")
        if heartbeat_value and heartbeat_value != last_heartbeat_value:
            last_heartbeat_value = heartbeat_value
            last_heartbeat_seen = time.time()

        progress_key = (
            state.get("stage"),
            state.get("page_count"),
            state.get("collected_rows"),
            state.get("status"),
        )
        if progress_key != last_progress_key:
            last_progress_key = progress_key
            log(
                "阶段 1",
                f"{district['name']} 区进度："
                f"stage={state.get('stage')}, "
                f"page={state.get('page_count')}, "
                f"collected={state.get('collected_rows')}, "
                f"status={state.get('status')}",
            )

        status = state.get("status")
        if status == "done":
            result = state.get("result")
            if not isinstance(result, dict):
                raise RuntimeError(f"district_result_invalid: {district['name']}")
            return result
        if status == "error":
            raise RuntimeError(state.get("error", f"district_error: {district['name']}"))

        if time.time() - last_heartbeat_seen > DISTRICT_STALL_TIMEOUT:
            raise RuntimeError(
                f"district_stalled: {district['name']} 区 {int(DISTRICT_STALL_TIMEOUT)} 秒无进展，"
                f"stage={state.get('stage')}, page={state.get('page_count')}, "
                f"collected={state.get('collected_rows')}"
            )

        time.sleep(DISTRICT_POLL_INTERVAL)

    raise RuntimeError(
        f"district_timeout: {district['name']} 区超过 {int(DISTRICT_RUN_TIMEOUT)} 秒仍未完成"
    )


def convert_browser_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    houses: list[dict[str, Any]] = []
    crawl_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for raw in raw_rows:
        plate = safe_text(raw.get("plate"), default="")
        house_code = safe_text(raw.get("house_code"), default="")
        block_code = safe_text(raw.get("block_code"), default="")
        community_name = safe_text(raw.get("community_name"), default="")
        community_url = safe_text(raw.get("community_url"), default="")
        community_formula = build_community_formula(community_name, community_url)
        community_cell = community_formula if community_url else " "

        layout = safe_text(raw.get("layout"))
        area = safe_text(raw.get("area"))
        total_price_text = safe_text(raw.get("total_price_text"), default="")
        total_price_value = parse_float(total_price_text, default=0.0)
        unit_price_text = safe_text(raw.get("unit_price_text"), default="")
        unit_price_value = format_unit_price(unit_price_text) if unit_price_text else " "
        floor = safe_text(raw.get("floor"))
        score_text = safe_text(raw.get("score_text"), default="0")
        score_value = parse_float(score_text, default=0.0)
        create_date = safe_text(raw.get("create_date"))
        maintainer = safe_text(raw.get("maintainer"))
        detail_url = safe_text(raw.get("detail_url"), default=community_url)
        source_house_id = safe_text(raw.get("source_house_id"), default="")

        excel_columns = [
            block_code or " ",
            community_cell,
            layout,
            area,
            total_price_text or " ",
            unit_price_value,
            floor,
            score_text,
            create_date,
            maintainer,
        ]
        excel_line = "\t".join(excel_columns)

        title_parts = [part for part in [community_name, layout] if part and part != " "]
        title = " ".join(title_parts) or block_code or source_house_id

        houses.append(
            {
                "district": safe_text(raw.get("district"), default=""),
                "plate": plate,
                "house_code": house_code,
                "block_code": block_code,
                "community": community_cell,
                "community_name": community_name,
                "community_url": community_url,
                "layout": layout,
                "area": area,
                "price": total_price_value,
                "price_text": total_price_text,
                "unit_price": unit_price_value,
                "floor": floor,
                "score": score_value,
                "score_text": score_text,
                "list_date": create_date,
                "maintainer": maintainer,
                "house_id": source_house_id,
                "url": detail_url,
                "title": title,
                "crawl_time": crawl_time,
                "excel_line": excel_line,
            }
        )

    return houses


def dedupe_houses_by_id(
    houses: list[dict[str, Any]],
    seen_house_ids: set[str],
) -> tuple[list[dict[str, Any]], int]:
    kept: list[dict[str, Any]] = []
    skipped = 0

    for house in houses:
        house_id = safe_text(house.get("house_id"), default="")
        if house_id:
            if house_id in seen_house_ids:
                skipped += 1
                continue
            seen_house_ids.add(house_id)
        kept.append(house)

    return kept, skipped


def check_browser_connection(driver: Optional[WebDriver]) -> bool:
    if driver is None:
        return False
    try:
        _ = driver.current_url
        return True
    except Exception:
        return False


def main() -> int:
    log("阶段 1", "=" * 60)
    log("阶段 1", "开始房源抓取（页面内执行同源 JS 逻辑）")
    log("阶段 1", f"目标 URL: {BASE_URL}")
    log("阶段 1", f"价格要求：{int(MIN_TOTAL_PRICE)}-{int(MAX_TOTAL_PRICE)} 万")
    log("阶段 1", f"筛选规则：房源分 >= {MIN_SCORE} 或最近 {RECENT_DAYS} 天/小时内")
    log("阶段 1", f"抓取区顺序：{'、'.join(d['name'] for d in DISTRICTS)}")

    if not check_debug_port():
        log("阶段 1", "未检测到调试 Chrome，准备自动启动专用调试窗口")
        if not launch_debug_chrome(force=False):
            log("阶段 1", "普通启动失败，尝试清理旧的调试窗口后重启")
            if not launch_debug_chrome(force=True):
                log("阶段 1", f"ERROR: Chrome 调试端口 {DEBUG_PORT} 未开启")
                log("阶段 1", "提示：请在专用调试窗口中打开链家页面并完成登录")
                return 1
        log("阶段 1", "OK: 调试 Chrome 已启动，将复用 D:\\Unique work form\\ChromeDebugProfile")
        log("阶段 1", "提示：浏览器窗口已打开，请勿手动关闭")

    driver: Optional[WebDriver] = None
    all_houses: list[dict[str, Any]] = []
    seen_house_ids: set[str] = set()
    skipped_districts: list[str] = []

    try:
        log("阶段 1", "连接 Chrome...")
        driver = create_driver()
        log("阶段 1", "OK: Chrome 连接成功")

        # 只在最开始加载一次页面，后续各区直接在页面内切换
        log("阶段 1", "初始化页面（仅加载一次）...")
        if not ensure_base_page(driver):
            return 1
        install_browser_collector(driver)
        log("阶段 1", "页面就绪，开始逐区抓取")

        for idx, district in enumerate(DISTRICTS, 1):

            # 仅在浏览器连接断开时才重新加载页面
            if not check_browser_connection(driver):
                log("阶段 1", "ERROR: 浏览器连接已断开，尝试重新连接并重载页面...")
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = create_driver()
                if not ensure_base_page(driver):
                    return 1
                install_browser_collector(driver)
                log("阶段 1", "OK: Chrome 重新连接成功，页面已重新初始化")

            log("阶段 1", f"开始处理 {district['name']} 区 ({idx}/{len(DISTRICTS)})")
            try:
                result = collect_district_browser_side(driver, district)
                district_houses_raw = convert_browser_rows(result.get("rows", []))
                district_houses, skipped_duplicates = dedupe_houses_by_id(
                    district_houses_raw,
                    seen_house_ids,
                )
                all_houses.extend(district_houses)
                duplicate_note = (
                    f"，跨区去重跳过 {skipped_duplicates} 套"
                    if skipped_duplicates
                    else ""
                )
                log(
                    "阶段 1",
                    f"{district['name']} 区完成：保留 {len(district_houses)} 套"
                    f"（原始 {len(district_houses_raw)} 套{duplicate_note}），"
                    f"页数 {result.get('page_count')}, 停止原因 {result.get('stop_reason')}",
                )
            except Exception as exc:
                # 单区出错记录并跳过，不中断整体流程
                log("阶段 1", f"WARNING: {district['name']} 区出错，已跳过：{exc}")
                skipped_districts.append(district["name"])
                if len(skipped_districts) > MAX_SKIPPABLE_DISTRICTS:
                    log(
                        "阶段 1",
                        f"ERROR: 已跳过 {len(skipped_districts)} 个区"
                        f"（{', '.join(skipped_districts)}），"
                        f"超过允许上限 {MAX_SKIPPABLE_DISTRICTS}，终止抓取",
                    )
                    return 1
                continue

        # 汇总跳过情况
        if skipped_districts:
            log("阶段 1", f"注意：以下区被跳过（共 {len(skipped_districts)} 个）：{', '.join(skipped_districts)}")

        log("阶段 1", "=" * 60)
        log("阶段 1", f"抓取完成，共 {len(all_houses)} 套房源")

        if all_houses:
            avg_price = sum(house["price"] for house in all_houses) / len(all_houses)
            avg_score = sum(house["score"] for house in all_houses) / len(all_houses)
            log("阶段 1", f"平均总价：{avg_price:.1f} 万")
            log("阶段 1", f"平均房源分：{avg_score:.2f}")

        log("阶段 2", "开始数据校验")
        valid, message = validate_data(all_houses)
        if not valid:
            log("阶段 2", f"ERROR: {message}")
            return 1
        log("阶段 2", f"OK: {message}")

        log("阶段 3", "开始保存数据")
        success, message = save_data(all_houses)
        if not success:
            log("阶段 3", f"ERROR: {message}")
            return 1
        log("阶段 3", f"OK: {message}")

        log("完成", "=" * 60)
        log("完成", f"抓取完成，总计 {len(all_houses)} 套房源")
        log("完成", f"数据文件：{DATA_JSON}")

        return 0

    except Exception as exc:
        log("阶段 1", f"ERROR: 抓取失败：{exc}")
        log("阶段 1", traceback.format_exc())
        return 1
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    if os.environ.get("HOUSE_GRAB_PIPELINE_RUN") != "1" and "--direct" not in sys.argv[1:]:
        print("ERROR: 请运行 D:\\Unique work form\\RUN_HOUSE_GRAB.cmd，不要单独运行 stage1_grab.py")
        sys.exit(2)
    sys.exit(main())