#!/usr/bin/env python
# -*- coding: utf-8 -*-
# [!] 警告：未经用户（佳佳）明确同意，禁止修改此脚本。

"""
每日跟进检查 - 晚间复盘（集成等级分析版）v2
合并功能：
  1. 检查今天的跟进情况（应跟进/已跟进/未跟进）
  2. 对客户进行等级升降建议分析（时间+规则+AI意向）
  3. 生成 HTML 报告保存到桌面，方便手机查看
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any

# ============================================================
# 路径与配置
# ============================================================
WORKSPACE_ROOT = Path(__file__).parent.parent
CACHE_FILE = WORKSPACE_ROOT / "runtime" / "tuantuan_cache.json"
DAILY_PLAN_FILE = Path(r"C:\Users\Huawei\Desktop\daily_follow_plan_latest.txt")
REPORT_DIR = Path(r"C:\Users\Huawei\Desktop")

# Excel 写入配置（仅用于等级调整写入，可选功能）
EXCEL_PATH = Path(r"D:\Unique work form\daily_followup.xlsm")
PASSWORD = "000"
CLIENT_SHEET_INDEX = 2
GRADE_COLUMN = 6

# Telegram 通知
TELEGRAM_CHAT_ID = "8724466632"
TELEGRAM_BOT_TOKEN = "8751931066:AAFhWCoE5-8G_G9gpgv3Bna8Z1I8JsNb1b4"

# AI 配置（百炼 / DashScope）
BAILIAN_API_KEY = "sk-sp-9112ba5f54c74b40b798a085b9b040a6"
BAILIAN_API_URL = "https://coding.dashscope.aliyuncs.com/v1/chat/completions"
MODEL = "qwen3.6-plus"


def load_cache() -> dict:
    if not CACHE_FILE.exists():
        return None
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_daily_plan_rows() -> list[int]:
    """从桌面跟进计划文件中提取客户行号"""
    if not DAILY_PLAN_FILE.exists():
        print(f"[!] 跟进计划文件不存在: {DAILY_PLAN_FILE}")
        return []
    content = DAILY_PLAN_FILE.read_text(encoding="utf-8")
    rows = []
    for line in content.splitlines():
        match = re.search(r'行号：\s*(\d+)', line)
        if match:
            rows.append(int(match.group(1)))
    print(f"[OK] 从跟进计划加载 {len(rows)} 个客户行号")
    return rows


def days_since(date_str: str | None) -> int | None:
    """计算距离某天的天数"""
    if not date_str:
        return None
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return (datetime.now() - d).days
    except Exception:
        return None


# ============================================================
# 晚间复盘核心逻辑
# ============================================================
def check_today_followups(cache: dict, plan_rows: list[int]) -> dict:
    """检查今天的跟进情况（含计划内/计划外）"""
    clients = cache.get("clients", [])
    today = datetime.now().strftime("%Y-%m-%d")

    plan_set = set(plan_rows)
    plan_followed = []
    plan_not_followed = []
    unplanned_followed = []

    for client in clients:
        row = client.get("row")
        followups = client.get("followups", [])
        has_today = any(f.get("date") == today for f in followups)

        if not has_today:
            # 今天没跟进，如果这个客户在计划里，记为未跟进
            if row in plan_set:
                plan_not_followed.append(client)
            continue

        # 今天有跟进记录
        if row in plan_set:
            plan_followed.append(client)
        else:
            # 不在计划里但今天跟进了 -> 计划外跟进
            unplanned_followed.append(client)

    # 计划内总数 = 计划内已跟进 + 计划内未跟进
    should_follow = plan_followed + plan_not_followed

    return {
        "should_follow": should_follow,
        "plan_followed": plan_followed,
        "plan_not_followed": plan_not_followed,
        "unplanned_followed": unplanned_followed,
    }


# ============================================================
# 等级调整分析逻辑（从 client_grade_adjust.py 移植）
# ============================================================
def analyze_clients_intent_with_ai_batch(clients_batch: list, suggestions: dict) -> dict:
    """批量分析客户意向，返回 {row: {intent, confidence, reason, suggestion}}"""
    if not clients_batch:
        return {}

    clients_text = ""
    for i, client in enumerate(clients_batch, 1):
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 1. 基本信息 & D列总结
        summary = client.get("client_summary", "无详细画像")
        props = f"{client.get('budget', '?')}万 / {client.get('district', '?')} / {client.get('need', '?')}"
        header = f"{i}. {client['name']}（{client['grade']}级）\n   [T]画像: {props}\n   [N]详情: {summary}\n"
        
        # 2. 读取今日建议（如果有）
        suggestion = suggestions.get(client['row'], "")
        if suggestion:
            header += f"   [D]计划: {suggestion}\n"
        else:
            header += "   [D]计划: 无（非计划内跟进）\n"
        
        # 3. 最近 4 条带时间戳跟进
        all_fups = client.get("followups", [])
        recent_fups = all_fups[-4:]
        history = "   [T]近期: \n" + "\n".join([f"     - [{f['date'][:10]}] {f['content'][:30]}..." for f in recent_fups])
        
        # 3. 最近一次关键跟进 (带看/电话/回复/解读)
        keywords = ["带看", "通电话", "有回复", "解读", "邀约"]
        key_fup = None
        for f in reversed(all_fups):
            content = f.get("content", "")
            if any(k in content for k in keywords):
                key_fup = f
                break
        
        key_history = "   [K]关键: [{}] {}".format(key_fup['date'][:10], key_fup['content'][:100]) if key_fup else "   [K]关键: 无关键互动"
        
        # 4. 今日跟进
        today_fups = [f for f in all_fups if f.get("date", "")[:10] == today]
        today_text = "   [F]今日: " + (", ".join([f['content'][:30] for f in today_fups]) if today_fups else "未跟进")

        clients_text += f"{header}{history}\n{key_history}\n{today_text}\n\n"

    prompt = (
        f"你是资深房产销售总监。请复盘以下经纪人（佳佳）今日的跟进记录。\\n\\n"
        f"{clients_text}\\n"
        f"请为每个客户提供【双向分析】：\\n"
        f"1. 执行力对比：对比【今日计划】与【实际跟进】，评价执行是否到位。若未执行计划，是否合理应变？\\n"
        f"2. 客户意向：积极（明确需求/约看）/ 中性（观望）/ 负面（拒绝）\\n"
        f"3. 等级建议：升级/保持/降级。客户等级分为 A(最有希望短期成交)→B(重点跟进)→C(普通)→D(沉睡)→E(放弃) 五级。根据跟进内容质量判断，不只看互动频率。例如：客户明确说已买好房→降级；约看/明确预算/主动问房→升级；已读不回/敷衍→保持或降级。\\n"
        f"4. 判定理由：简述判断依据，引用跟进内容中的关键信息。\\n"
        f"5. 沟通点评（经纪人侧）：犀利点评佳佳的跟进话术、语气是否得当，是否遗漏关键信息。\\n"
        f"6. 改进建议（经纪人侧）：给出下一次跟进的破冰话术或高情商回复。\\n\\n"
        f"**重要：JSON 中 name 字段必须与客户列表中的姓名完全一致（包括微信、女士、先生等后缀），不得省略或简化。**\\n\\n"
        f'请按以下 JSON 格式返回：\\n{{"clients": [\\n'
        f'{{"name": "客户完整姓名（与列表严格一致）", "execution": "执行力点评（30字以内）", "intent": "积极/中性/负面", "suggestion": "升级/保持/降级", '
        f'"reason": "判定理由", "critique": "沟通点评（30字以内）", "advice": "改进建议/话术（30字以内）"}}\\n'
        f"]}}\\n\\n只返回 JSON，不要其他内容。"
    )

    headers = {
        "Authorization": f"Bearer {BAILIAN_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一名专业的房产中介业务分析助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }

    try:
        req = urllib.request.Request(
            BAILIAN_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        # 主动限流：每次调用前间隔 10 秒，防止触发阿里云 RPM 限制
        import time
        time.sleep(10)

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")

        # 增强的 JSON 解析：先用正则找 JSON 块，再尝试解析
        try:
            # 尝试提取 ```json...``` 块
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', ai_response)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                # 尝试直接找最外层 { ... }
                json_match = re.search(r'(\{[\s\S]*\})', ai_response)
                json_str = json_match.group(1) if json_match else ai_response
            
            # 清理可能的尾部多余字符
            json_str = json_str.strip()
            
            analysis_result = json.loads(json_str)

            result_dict = {}
            for analysis in analysis_result.get("clients", []):
                ai_name = analysis.get("name", "")
                # 清理 AI 返回的名字（去除可能存在的括号后缀，如“张三(A级)”）
                clean_ai_name = re.sub(r'[（\(].*?[\）\)]', '', ai_name)
                
                for client in clients_batch:
                    match = False
                    # 1. 严格匹配
                    if client["name"] == ai_name:
                        match = True
                    # 2. 清理后匹配
                    elif clean_ai_name and client["name"] == clean_ai_name:
                        match = True
                    # 3. 包含关系匹配
                    elif client["name"] in ai_name or ai_name in client["name"]:
                        match = True
                        
                    if match:
                        result_dict[client["row"]] = {
                            "intent": analysis.get("intent", "中性"),
                            "confidence": analysis.get("confidence", 0.5),
                            "reason": analysis.get("reason", ""),
                            "suggestion": analysis.get("suggestion", "保持"),
                            "critique": analysis.get("critique", ""),
                            "advice": analysis.get("advice", ""),
                        }
                        break

            if not result_dict and analysis_result.get("clients"):
                # JSON 解析成功但名字没匹配上，记录日志
                ai_names = [c.get("name") for c in analysis_result.get("clients", [])]
                client_names = [c["name"] for c in clients_batch]
                print(f"  [!] AI 返回名字不匹配: AI={ai_names}, 期望={client_names}")

            return result_dict
        except json.JSONDecodeError as e:
            print(f"  [!] AI 返回 JSON 解析失败：{e}")
            print(f"  [!] 原始回复: {ai_response[:200]}...")
            return {}

    except urllib.error.HTTPError as e:
        # 重新抛出 HTTP 错误以便外层重试逻辑捕获
        raise
    except Exception as e:
        print(f"  [!] AI 调用失败：{e}")
        raise


def needs_ai_analysis(last_followup_date: str | None) -> bool:
    """只检查今天有跟进记录的客户"""
    if not last_followup_date:
        return False
    d = days_since(last_followup_date)
    # 仅当最后跟进日期为今天（0天）时才分析，避免重复检查
    if d is not None and d == 0:
        return True
    return False


def should_upgrade(current_grade: str, days_since_val: int | None, ai_analysis: dict | None):
    """判断是否应该升级"""
    if ai_analysis and ai_analysis.get("suggestion") == "降级":
        return False, f"AI 建议降级：{ai_analysis.get('reason', '意向不明')}"
    if ai_analysis and ai_analysis.get("intent") == "负面":
        return False, f"AI 判断负面：{ai_analysis.get('reason', '客户意向消极')}"
    if days_since_val is None:
        return False, "无互动记录"
    if current_grade == "D" and days_since_val <= 30:
        return True, f"最近{days_since_val}天有互动"
    if current_grade == "C" and days_since_val <= 14:
        return True, f"最近{days_since_val}天有互动"
    if current_grade == "B" and days_since_val <= 7:
        return True, f"最近{days_since_val}天有互动"
    return False, ""


def should_downgrade(current_grade: str, days_since_val: int | None, ai_analysis: dict | None):
    """判断是否应该降级"""
    if ai_analysis and ai_analysis.get("suggestion") == "降级":
        return True, f"AI 建议降级：{ai_analysis.get('reason', '意向消极')}"
    if ai_analysis and ai_analysis.get("intent") == "负面":
        return True, f"AI 判断负面：{ai_analysis.get('reason', '客户明确不买')}"
    if days_since_val is None:
        return False, "无互动记录"
    if current_grade == "A" and days_since_val > 14:
        return True, f"{days_since_val}天无互动"
    if current_grade == "B" and days_since_val > 30:
        return True, f"{days_since_val}天无互动"
    if current_grade == "C" and days_since_val > 90:
        return True, f"{days_since_val}天无互动"
    return False, ""


def get_new_grade(current_grade: str, direction: str) -> str:
    upgrade_map = {"E": "D", "D": "C", "C": "B", "B": "A", "A": "A"}
    downgrade_map = {"A": "B", "B": "C", "C": "D", "D": "E", "E": "E"}
    if direction == "upgrade":
        return upgrade_map.get(current_grade, current_grade)
    else:
        return downgrade_map.get(current_grade, current_grade)


def analyze_all_clients(clients: list, plan_map: dict) -> dict:
    """分析所有客户的等级调整建议"""
    adjustments = {"upgrade": [], "downgrade": [], "keep": []}

    # 筛选需要 AI 分析的客户
    clients_needing_ai = []
    for client in clients:
        name = client.get("name", "")
        if not name:
            continue
        current_grade = client.get("grade", "D").strip().upper()
        if current_grade not in ["A", "B", "C", "D", "E"]:
            continue
        last_followup_date = client.get("last_followup_date")
        if needs_ai_analysis(last_followup_date):
            clients_needing_ai.append(client)

    # 逐人 AI 分析
    ai_results = {}
    if clients_needing_ai:
        print(f"需要 AI 分析的客户：{len(clients_needing_ai)}个")

        # 直接使用从缓存读取的建议，不再单独打开 Excel
        suggestions = plan_map

        for idx, client in enumerate(clients_needing_ai, 1):
            print(f"[{idx}/{len(clients_needing_ai)}] 正在分析：{client.get('name', '未知')}...")
            sys.stdout.flush()
            
            # 增加重试机制防止限流 (429) - 指数退避策略
            retries = 3
            batch_results = {}
            for attempt in range(retries):
                try:
                    # 每次只传一个客户，并附带今日建议
                    batch_results = analyze_clients_intent_with_ai_batch([client], suggestions)
                    break # 成功则跳出重试循环
                except Exception as e:
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        wait_time = 60 * (attempt + 1)  # 60s -> 120s -> 180s 指数退避
                        print(f"  [!] 触发限流，等待 {wait_time} 秒后重试 ({attempt+1}/{retries})...")
                        sys.stdout.flush()
                        import time; time.sleep(wait_time)
                    else:
                        print(f"  [!] AI 调用失败：{e}")
                        break
            
            ai_results.update(batch_results)
            sys.stdout.flush()

        print(f"[OK] AI 分析完成（共{len(ai_results)}个客户）")
        sys.stdout.flush()

    # 分析所有今天跟进过的客户（直接用 AI 的等级建议，没跟进的不报）
    # 先构建 row -> client 的映射
    client_by_row = {c.get("row"): c for c in clients}
    
    for row, ai_analysis in ai_results.items():
        client = client_by_row.get(row)
        if not client:
            continue
        name = client.get("name", "")
        if not name:
            continue
        current_grade = client.get("grade", "D").strip().upper()
        if current_grade not in ["A", "B", "C", "D", "E"]:
            continue

        ds = days_since(client.get("last_followup_date"))

        # 直接使用 AI 给出的等级建议
        suggestion = ai_analysis.get("suggestion", "保持")
        reason = ai_analysis.get("reason", "AI 判断")

        client_info = {
            "row": row,
            "name": name,
            "current_grade": current_grade,
            "days_since": ds,
            "last_followup": client.get("last_followup_date"),
            "ai_intent": ai_analysis.get("intent", "未分析"),
            "ai_reason": ai_analysis.get("reason", ""),
            "ai_suggestion": ai_analysis.get("suggestion", "未分析"),
            "ai_execution": ai_analysis.get("execution", ""),
            "ai_critique": ai_analysis.get("critique", ""),
            "ai_advice": ai_analysis.get("advice", ""),
        }

        if suggestion == "升级":
            new_grade = get_new_grade(current_grade, "upgrade")
            client_info["new_grade"] = new_grade
            client_info["reason"] = f"AI 建议升级：{reason}"
            adjustments["upgrade"].append(client_info)
        elif suggestion == "降级":
            new_grade = get_new_grade(current_grade, "downgrade")
            client_info["new_grade"] = new_grade
            client_info["reason"] = f"AI 建议降级：{reason}"
            adjustments["downgrade"].append(client_info)
        else:
            adjustments["keep"].append(client_info)

    return adjustments


# ============================================================
# HTML 报告生成
# ============================================================
def generate_html_report(result: dict, grade_analysis: dict) -> str:
    """生成完整的 HTML 复盘报告（含等级调整建议）"""
    today = datetime.now().strftime("%Y-%m-%d")
    weekday_map = {
        "Monday": "周一", "Tuesday": "周二", "Wednesday": "周三",
        "Thursday": "周四", "Friday": "周五", "Saturday": "周六", "Sunday": "周日",
    }
    weekday_cn = weekday_map.get(datetime.now().strftime("%A"), "")

    should_follow = result["should_follow"]
    plan_followed = result["plan_followed"]
    plan_not_followed = result["plan_not_followed"]
    unplanned_followed = result["unplanned_followed"]

    total_should = len(should_follow)
    total_followed = len(plan_followed)
    total_not = len(plan_not_followed)
    total_unplanned = len(unplanned_followed)
    completion_rate = (total_followed / total_should * 100) if total_should > 0 else 0

    # 构建分析数据映射：{ name: analysis_data }
    analysis_map = {}
    
    def add_to_map(c_list):
        for c in c_list:
            name = c.get("name", "")
            analysis_map[name] = c

    add_to_map(grade_analysis.get("upgrade", []))
    add_to_map(grade_analysis.get("downgrade", []))
    add_to_map(grade_analysis.get("keep", []))

    up_count = len(grade_analysis.get("upgrade", []))
    down_count = len(grade_analysis.get("downgrade", []))
    keep_count = len(grade_analysis.get("keep", []))

    # --- 辅助函数：生成点评单元格 ---
    def get_review_cell(client_name):
        analysis = analysis_map.get(client_name)
        if not analysis:
            return '<td style="color:#999">无分析数据</td>'
        
        suggestion = analysis.get("ai_suggestion", "")
        critique = analysis.get("ai_critique", "")
        advice = analysis.get("ai_advice", "")
        intent = analysis.get("ai_intent", "")
        
        # 确定样式
        if suggestion == "升级":
            bg = "background:#f0fff0;"
            label = '<span class="badge badge-success" style="font-size:10px">升级</span>'
        elif suggestion == "降级":
            bg = "background:#fff5f5;"
            label = '<span class="badge badge-danger" style="font-size:10px">降级</span>'
        else:
            bg = ""
            label = '<span class="badge badge-info" style="font-size:10px">保持</span>'
            
        content = f'{label}'
        if critique: content += f'<br><span style="color:#d9534f">👉 {critique}</span>'
        if advice: content += f'<br><span style="color:#28a745">💡 {advice}</span>'
        
        return f'<td style="{bg}">{content}</td>'

    # 1. 计划内跟进详情
    plan_rows = ""
    for c in plan_followed:
        fups = c.get("followups", [])
        today_fups = [f for f in fups if f.get("date") == today]
        fup_text = "<br>".join([f'<span style="color:#555">[{f["date"]}]</span> {f["content"]}' for f in today_fups])
        
        plan_rows += (
            f'<tr class="client-row">'
            f'<td><b>{c.get("name", "")}</b></td>'
            f'<td><span class="badge badge-{_grade_color(c.get("grade", ""))}">{c.get("grade", "")}</span></td>'
            f'<td>{fup_text}</td>'
            f'{get_review_cell(c.get("name", ""))}'
            f'</tr>\n'
        )

    # 2. 计划外跟进详情
    unplanned_rows = ""
    for c in unplanned_followed:
        fups = c.get("followups", [])
        today_fups = [f for f in fups if f.get("date") == today]
        fup_text = "<br>".join([f'<span style="color:#555">[{f["date"]}]</span> {f["content"]}' for f in today_fups])
        
        unplanned_rows += (
            f'<tr class="client-row" style="background:#e7f3ff;">'
            f'<td><b>{c.get("name", "")}</b></td>'
            f'<td><span class="badge badge-{_grade_color(c.get("grade", ""))}">{c.get("grade", "")}</span></td>'
            f'<td>{fup_text}</td>'
            f'{get_review_cell(c.get("name", ""))}'
            f'</tr>\n'
        )

    # 3. 遗漏详情
    missed_rows = ""
    for c in plan_not_followed:
        ds = days_since(c.get("last_followup_date"))
        ds_text = f"{ds}天前" if ds is not None else "从未"
        
        # 检查是否有分析数据（比如因为误操作写了跟进但其实应该算遗漏的情况，一般没有）
        analysis = analysis_map.get(c.get("name", ""))
        review_html = ""
        if analysis:
            review_html = f'<td style="color:#999">无新跟进，上次: {c.get("last_followup_date", "未知")}</td>'
        else:
            review_html = f'<td style="color:#999">未跟进</td>'

        missed_rows += (
            f'<tr class="client-row">'
            f'<td><b>{c.get("name", "")}</b></td>'
            f'<td><span class="badge badge-{_grade_color(c.get("grade", ""))}">{c.get("grade", "")}</span></td>'
            f'<td>{ds_text}</td>'
            f'{review_html}'
            f'</tr>\n'
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日复盘 - {today}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 5px; font-size: 24px; }}
        .date {{ text-align: center; color: #666; margin-bottom: 20px; font-size: 14px; }}
        .stats {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 20px; }}
        .stat-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 28px; font-weight: bold; color: #007bff; }}
        .stat-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        .section {{ margin: 20px 0; padding: 0; border-radius: 8px; border: 1px solid #eee; overflow: hidden; }}
        .section-title {{ padding: 15px; font-weight: bold; font-size: 16px; margin: 0; border-left: 5px solid #ccc; background: #f9f9f9; }}
        .section-title.success {{ border-left-color: #28a745; color: #28a745; }}
        .section-title.info {{ border-left-color: #17a2b8; color: #17a2b8; }}
        .section-title.danger {{ border-left-color: #dc3545; color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 0; font-size: 14px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; vertical-align: top; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #666; }}
        td {{ color: #333; }}
        .badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-bottom: 3px; }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
        .badge-info {{ background: #d1ecf1; color: #0c5460; }}
        .client-row:hover {{ background: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>[T] 每日工作复盘</h1>
        <div class="date">[D] {today} ({weekday_cn}) | ⏰ {datetime.now().strftime('%H:%M')}</div>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{total_should}</div>
                <div class="stat-label">应跟进</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{total_followed}</div>
                <div class="stat-label">已执行</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" style="color: {'#17a2b8' if total_unplanned > 0 else '#666'};">{total_unplanned}</div>
                <div class="stat-label">计划外</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" style="color: {'#28a745' if completion_rate >= 80 else '#dc3545'};">{completion_rate:.0f}%</div>
                <div class="stat-label">完成率</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" style="color: {'#28a745' if total_not == 0 else '#dc3545'};">{total_not}</div>
                <div class="stat-label">遗漏</div>
            </div>
        </div>

        <!-- 计划内已跟进 -->
        <h3 class="section-title success">[OK] 计划内已跟进（{total_followed}人）</h3>
        <div class="section">
            <table>
                <tr>
                    <th style="width:15%">客户</th>
                    <th style="width:8%">等级</th>
                    <th style="width:35%">今日跟进内容</th>
                    <th style="width:42%">AI 总监点评 & 建议</th>
                </tr>
                {plan_rows if plan_rows else '<tr><td colspan="4" style="text-align:center;padding:30px;color:#999">无</td></tr>'}
            </table>
        </div>

        <!-- 计划外跟进 -->
        <h3 class="section-title info">[S] 计划外自主跟进（{total_unplanned}人）</h3>
        <div class="section">
            <table>
                <tr>
                    <th style="width:15%">客户</th>
                    <th style="width:8%">等级</th>
                    <th style="width:35%">今日跟进内容</th>
                    <th style="width:42%">AI 总监点评 & 建议</th>
                </tr>
                {unplanned_rows if unplanned_rows else '<tr><td colspan="4" style="text-align:center;padding:30px;color:#999">无</td></tr>'}
            </table>
        </div>

        <!-- 遗漏 -->
        <h3 class="section-title danger">[!] 遗漏（计划内未跟进）（{total_not}人）</h3>
        <div class="section">
            <table>
                <tr>
                    <th style="width:15%">客户</th>
                    <th style="width:8%">等级</th>
                    <th style="width:35%">上次跟进</th>
                    <th style="width:42%">状态</th>
                </tr>
                {missed_rows if missed_rows else '<tr><td colspan="4" style="text-align:center;padding:30px;color:#999">无遗漏！</td></tr>'}
            </table>
        </div>
    </div>
</body>
</html>"""
    return html


def _grade_color(grade: str) -> str:
    grade = grade.strip().upper()
    if grade == "A":
        return "success"
    elif grade == "B":
        return "info"
    elif grade == "C":
        return "warning"
    else:
        return "danger"


def _ai_badge(intent: str) -> str:
    if intent == "积极":
        return '<span class="badge badge-success">积极</span>'
    elif intent == "负面":
        return '<span class="badge badge-danger">负面</span>'
    elif intent == "中性":
        return '<span class="badge badge-warning">中性</span>'
    else:
        return f'<span class="badge badge-info">{intent}</span>'


# ============================================================
# Excel 等级写入（可选，不阻断主流程）
# ============================================================
def try_apply_grade_adjustments(adjustments: dict) -> int:
    """尝试将等级调整写入 Excel，返回成功数量。失败不阻断流程。"""
    up = adjustments.get("upgrade", [])
    down = adjustments.get("downgrade", [])
    if not up and not down:
        return 0

    try:
        import pythoncom
        from win32com.client import DispatchEx

        pythoncom.CoInitialize()
        excel = None
        workbook = None

        try:
            excel = DispatchEx("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            excel.Interactive = False  # 禁止任何弹窗，防止阻塞 COM
            workbook = excel.Workbooks.Open(
                Filename=str(EXCEL_PATH),
                UpdateLinks=0,
                ReadOnly=False,
                Password=PASSWORD if PASSWORD else None,
            )
            ws = workbook.Worksheets.Item(CLIENT_SHEET_INDEX)
            updated = 0

            for c in up + down:
                row = c.get("row")
                if row:
                    ws.Cells(row, GRADE_COLUMN).Value = c["new_grade"]
                    updated += 1

            workbook.Save()
            print(f"[OK] 已写入 {updated} 个客户等级调整到 Excel")
            return updated
        except Exception as e:
            print(f"[!] Excel 写入失败（不影响报告生成）：{e}")
            return 0
        finally:
            try:
                if workbook:
                    workbook.Save()
                    workbook.Close(SaveChanges=True)
                if excel:
                    excel.Quit()
            except Exception:
                pass
            finally:
                pythoncom.CoUninitialize()
    except ImportError:
        print("[!] win32com 不可用，跳过 Excel 写入")
        return 0


def write_ai_results_to_excel(grade_analysis: dict, date_str: str) -> int:
    """将 AI 检查结果写入 Excel 跟进内容列右侧的新列"""
    if not grade_analysis:
        return 0

    try:
        import pythoncom
        from win32com.client import DispatchEx
        import time

        pythoncom.CoInitialize()
        excel = None
        workbook = None

        try:
            # 1. 杀进程防占用
            import subprocess
            subprocess.run(['taskkill', '/F', '/IM', 'EXCEL.EXE'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(6)

            excel = DispatchEx("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            excel.Interactive = False  # 禁止任何弹窗，防止阻塞 COM
            workbook = excel.Workbooks.Open(
                Filename=str(EXCEL_PATH),
                UpdateLinks=0,
                ReadOnly=False,
                Password=PASSWORD if PASSWORD else None,
            )
            ws = workbook.Worksheets.Item(CLIENT_SHEET_INDEX)
            
            # 2. 【优化】用 UsedRange 一次性读取全表到内存，不再逐列扫描
            print("[写入] 正在通过 UsedRange 读取全表到内存...")
            sys.stdout.flush()
            all_data = ws.UsedRange.Value
            ur_row = ws.UsedRange.Row  # UsedRange 起始行号（1-indexed）
            ur_col = ws.UsedRange.Column  # UsedRange 起始列号（1-indexed）
            
            # 计算表头行在 all_data 中的索引
            header_row = 11  # Excel 第 11 行
            if all_data and isinstance(all_data, tuple) and len(all_data) > 0:
                if isinstance(all_data[0], tuple):
                    # 多行数据，计算偏移
                    offset = header_row - ur_row
                    headers = all_data[offset] if 0 <= offset < len(all_data) else ()
                else:
                    # 单行数据（UsedRange 只有第 11 行）
                    headers = all_data
            else:
                headers = ()
            
            # 在内存中扫描表头（无论多少列都瞬间完成）
            date_header = f"{date_str} 检查"
            target_col = None
            
            # 从后往前找最后一个有内容的列，在其右侧写入
            for c_idx in range(len(headers) - 1, -1, -1):
                val = headers[c_idx]
                if val is not None and str(val).strip() != "":
                    target_col = c_idx + ur_col + 1
                    break
            
            if not target_col:
                # 如果全是空的（理论上不可能），就在第一列写
                target_col = ur_col + 1

            ws.Cells(header_row, target_col).Value = date_header
            # 强制清除表头背景色
            ws.Cells(header_row, target_col).Interior.Pattern = 0
            print(f"[写入] 找到最后使用的列，准备在第 {target_col} 列写入")
            
            # 3. 批量写入
            all_results = []
            for c_list in [grade_analysis.get("upgrade", []), grade_analysis.get("downgrade", []), grade_analysis.get("keep", [])]:
                for c in c_list:
                    all_results.append(c)

            updated = 0
            for c in all_results:
                row = c.get("row")
                if row:
                    action = c.get("ai_suggestion", "保持")
                    reason = c.get('ai_reason', '') or c.get('reason', '')
                    intent = c.get('ai_intent', '')
                    advice = c.get('ai_advice', '')
                    parts = [f"{action}: {reason} ({intent})"]
                    if advice:
                        parts.append(f"建议: {advice}")
                    content = " | ".join(parts)
                    cell = ws.Cells(row, target_col)
                    cell.Value = content
                    # 强制清除内容单元格背景色
                    cell.Interior.Pattern = 0
                    updated += 1

            print(f"[写入] 正在保存...")
            sys.stdout.flush()
            workbook.Save()
            print(f"[OK] 已将 {updated} 个检查结果写入 Excel 第 {target_col} 列")
            return updated

        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"[!] Excel 写入失败：{e}")
            return 0
        finally:
            try:
                if workbook:
                    workbook.Close(SaveChanges=False)  # 已 Save() 过，不再重复保存
                if excel:
                    excel.Quit()
            except Exception:
                pass
            finally:
                pythoncom.CoUninitialize()
    except ImportError:
        print("[!] win32com 不可用，跳过 Excel 写入")
        return 0


# ============================================================
# Telegram 通知
# ============================================================
def send_telegram_report(file_path: str) -> bool:
    """通过 Telegram Bot 发送报告文件"""
    try:
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            print(f"[!] 文件过大 ({file_size} bytes)，跳过发送")
            return False

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="chat_id"',
            "",
            TELEGRAM_CHAT_ID,
            f"--{boundary}",
            'Content-Disposition: form-data; name="document"; filename="daily_review.html"',
            "Content-Type: text/html",
            "",
        ]
        with open(file_path, "r", encoding="utf-8") as f:
            body_lines.append(f.read())
        body_lines.extend([
            f"--{boundary}--",
            "",
        ])
        body = "\r\n".join(body_lines).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("ok"):
                print("[OK] Telegram 报告已发送")
                return True
            else:
                print(f"[!] Telegram 发送失败: {result.get('description', '')}")
                return False
    except Exception as e:
        print(f"[!] Telegram 发送异常: {e}")
        return False


# ============================================================
# 主入口
# ============================================================
def main():
    print("=" * 60)
    print("[每日复盘] 晚间检查（集成等级分析）")
    print("=" * 60)
    print()

    # 1. 刷新缓存并加载数据
    print("[1/5] 正在刷新缓存 (读取 Excel 最新数据)...")
    sys.stdout.flush()
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))
        from cache import build_cache
        cache_data = build_cache()
        clients = cache_data.get("clients", [])
        today = datetime.now().strftime("%Y-%m-%d")
        today_mmdd = today.split("-")[1] + "-" + today.split("-")[2]
        today_no_dash = today_mmdd.replace("-", "")
        print(f"[OK] 从 Excel 读取最新数据：{len(clients)} 个客户")
    except Exception as e:
        print(f"[X] 读取数据失败：{e}")
        import traceback; traceback.print_exc()
        return 1

    # 重新组织 client 数据格式以兼容后续逻辑
    cache = {"generated_at": cache_data.get("generated_at"), "clients": []}
    for c in clients:
        c_data = {
            "row": c["row"],
            "name": c["name"],
            "grade": c.get("grade", "D"),
            "client_summary": c.get("decode", ""),
            "need": c.get("need", ""),
            "district": c.get("district", ""),
            "budget": c.get("budget"),
            "followups": c.get("followups", []),
            "ai_checks": {},
            "ai_suggestions": {},
            "last_followup_date": c.get("last_followup_date")
        }
        # 兼容旧缓存和新缓存的字段
        if c.get("ai_suggestion"):
            c_data["ai_suggestions"][today] = c["ai_suggestion"]
        if c.get("ai_check"):
            c_data["ai_checks"][today] = c["ai_check"]
            
        # 从 JSON 缓存中读取建议列
        if c.get("ai_suggestion"):
            c_data["ai_suggestions"][today] = c["ai_suggestion"]
        cache["clients"].append(c_data)
    clients = cache.get("clients", [])
    print(f"[OK] 加载 {len(clients)} 个客户")
    sys.stdout.flush()

    # 2. 加载跟进计划（从缓存中获取今日建议）
    today_str = datetime.now().strftime("%Y-%m-%d")
    plan_rows = []
    client_plan_map = {} # map row -> plan_text
    
    for client in clients:
        suggestions = client.get("ai_suggestions", {})
        if suggestions.get(today_str):
            plan_rows.append(client["row"])
            client_plan_map[client["row"]] = suggestions[today_str]
    
    print(f"[OK] 从缓存读取到 {len(plan_rows)} 条今日跟进建议")
    sys.stdout.flush()

    # 3. 检查今日跟进情况
    print("检查今日跟进情况...")
    result = check_today_followups(cache, plan_rows)
    print(f"  计划内应跟: {len(result['should_follow'])} | 计划内已跟: {len(result['plan_followed'])} | 计划外跟进: {len(result['unplanned_followed'])} | 遗漏: {len(result['plan_not_followed'])}")
    sys.stdout.flush()

    # 4. 等级调整分析
    print("\n开始等级调整分析...")
    sys.stdout.flush()
    grade_analysis = analyze_all_clients(clients, client_plan_map)
    up = len(grade_analysis["upgrade"])
    down = len(grade_analysis["downgrade"])
    keep = len(grade_analysis["keep"])
    print(f"  升级建议: {up} | 降级建议: {down} | 保持: {keep}")
    sys.stdout.flush()

    # 5. 【已禁用】复盘脚本仅出建议，不自动改等级
    # print("\n尝试将等级调整写入 Excel...")
    # sys.stdout.flush()
    # try_apply_grade_adjustments(grade_analysis)

    # 6. 将检查结果写入跟进内容下一列
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"\n将检查结果写入 Excel（{today_str}）...")
    sys.stdout.flush()
    write_ai_results_to_excel(grade_analysis, today_str)

    # 7. 生成 HTML 报告
    print("\n生成 HTML 报告...")
    sys.stdout.flush()
    html = generate_html_report(result, grade_analysis)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"daily_review_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"[OK] 报告已保存: {report_path}")
    sys.stdout.flush()

    # 同时保存一份 latest 方便下次引用
    latest_path = REPORT_DIR / "daily_review_latest.html"
    latest_path.write_text(html, encoding="utf-8")

    # 7. 发送 Telegram 通知
    print("\n发送 Telegram 通知...")
    sys.stdout.flush()
    send_telegram_report(str(latest_path))

    print("\n" + "=" * 60)
    print("[OK] 复盘完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
