#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import hashlib
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

# 导入 experience_workflow 模块（使用完整模块名）
import importlib
experience_workflow = importlib.import_module('experience_workflow_gongzuoliu')

apply_draft_revision = experience_workflow.apply_draft_revision
build_approved_entry = experience_workflow.build_approved_entry
build_business_excel_content = experience_workflow.build_business_excel_content
build_experience_draft = experience_workflow.build_experience_draft
build_technical_excel_payload = experience_workflow.build_technical_excel_payload
dedupe_entries = experience_workflow.dedupe_entries
experience_signature = experience_workflow.experience_signature
list_experience_drafts = experience_workflow.list_experience_drafts
load_experience_draft = experience_workflow.load_experience_draft
load_experience_store = experience_workflow.load_experience_store
parse_draft_revision_instruction = experience_workflow.parse_draft_revision_instruction
save_experience_draft = experience_workflow.save_experience_draft
search_entries = experience_workflow.search_entries
summarize_draft = experience_workflow.summarize_draft
upsert_approved_entry = experience_workflow.upsert_approved_entry

try:
    import pythoncom
    from win32com.client import DispatchEx, GetObject
except ImportError:  # pragma: no cover
    pythoncom = None
    DispatchEx = None
    GetObject = None


# 数据文件路径（主数据表）
WORKBOOK_PATH = Path(r"D:\Unique work form\daily_followup.xlsm")
WORKBOOK_PASSWORD = "000"
EXPORT_CSV_VBS = Path(r"D:\Unique work form\export_csv.vbs")
HOUSE_DETAIL_CMD = Path(r"D:\Unique work form\RUN_HOUSE_DETAIL.cmd")
HOUSE_DETAIL_JSON = Path(r"D:\Unique work form\_house_grab_runtime\last_house_detail.json")

# 【注意】数据表路径保持 D 盘，因为这是主数据表位置
# 脚本本身已迁移到工作区，由工作区统一管理

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = WORKSPACE_ROOT / "runtime"
CACHE_FILE = RUNTIME_DIR / "tuantuan_cache.json"
PROPERTY_DETAIL_CACHE_FILE = RUNTIME_DIR / "property_detail_cache.json"
CORE_GUARD_MANIFEST = WORKSPACE_ROOT / "workspace" / "config" / "protected_core.json"
BUSINESS_EXPERIENCE_SHEET_NAME = "Experience"
TECHNICAL_EXPERIENCE_SHEET_NAME = "Technical"
DASHSCOPE_BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
DASHSCOPE_API_KEY = "sk-sp-9112ba5f54c74b40b798a085b9b040a6"
DASHSCOPE_DEFAULT_MODEL = "qwen3.5-plus"

PROTECTED_CORE_PATHS = [
    "AGENTS.md",
    "BOOTSTRAP.md",
    "CORE_GUARD.md",
    "MEMORY.md",
    "SOUL.md",
    "TEAM.md",
    "TOOLS.md",
    "USER.md",
    "memory/团团助手系统设计.md",
    "tools/experience_workflow.py",
    "tools/LOCK_TUANTUAN_CORE.ps1",
    "tools/RUN_TUANTUAN_qidong.cmd",
    "tools/tuantuan_cli_zhiling.py",
    "tools/UNLOCK_TUANTUAN_CORE.ps1",
    "workspace/config/triggers.yaml",
]

ALLOWED_WRITE_AREAS = [
    "runtime/",
    "temp/",
    "memory/experience/drafts/",
    "memory/experience/approved_store.json",
    "D:/Unique work form/daily_followup.xlsm",
]

CLIENT_SHEET_INDEX = 2
PROPERTY_SHEET_INDEX = 4
CLIENT_HEADER_ROW = 11
CLIENT_START_ROW = 12
PROPERTY_START_ROW = 4
FIRST_FOLLOWUP_COLUMN = 20
FOLLOWUP_GROUP_RE = re.compile(r"^[A-Z][0-9]{1,2}$")
HYPERLINK_RE = re.compile(r'=HYPERLINK\("([^"]*)","([^"]*)"\)', re.IGNORECASE)
XL_TO_LEFT = -4159
CLIENT_FIELD_COLUMNS = {
    "client_summary": 4,
    "summary": 4,
    "analysis": 4,
    "grade": 6,
    "rooms": 7,
    "budget": 8,
    "name": 9,
    "district": 10,
    "phone": 11,
    "decode": 12,
    "status": 12,
    "decision_speed": 13,
    "decision": 13,
    "info_style": 14,
    "info": 14,
    "interaction_style": 15,
    "interact": 15,
    "need": 16,
    "ideal_phrase": 17,
    "idea": 17,
    "pain": 18,
    "notes": 19,
    "areas": 19,
}
CLIENT_FIELD_ALIASES = {
    "budget": ["预算", "总价", "价格"],
    "rooms": ["户型", "房型", "几房"],
    "district": ["区域", "板块", "片区", "常看区域"],
    "client_summary": ["客户分析", "客户情况", "客户画像", "分析", "摘要"],
    "need": ["需求"],
    "pain": ["痛点"],
    "notes": ["备注"],
    "decision_speed": ["决策速度", "决策节奏", "急迫性"],
    "info_style": ["信息处理方式", "信息偏好"],
    "interaction_style": ["互动态度", "信任度", "性格", "客户性格"],
    "ideal_phrase": ["最想说的话"],
    "decode": ["解读", "状态"],
    "grade": ["等级"],
}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    payload, exit_code = args.handler(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tuantuan_cli",
        description="团团助手统一数据入口。所有客户、房源、跟进操作都通过这里完成。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="检查数据入口、缓存、依赖是否正常。")
    doctor.add_argument("--rebuild", action="store_true", help="强制重建缓存。")
    doctor.set_defaults(handler=cmd_doctor)

    refresh = subparsers.add_parser("refresh", help="从主表重建缓存。")
    refresh.add_argument("--sync-csv", action="store_true", help="额外同步旧版 CSV 导出。")
    refresh.set_defaults(handler=cmd_refresh)

    client_search = subparsers.add_parser("client-search", help="按姓名、电话或行号查客户候选。")
    client_search.add_argument("--query", required=True, help="姓名、电话尾号或客户行号。")
    client_search.add_argument("--limit", type=int, default=10, help="最多返回多少个候选。")
    client_search.set_defaults(handler=cmd_client_search)

    client_context = subparsers.add_parser("client-context", help="读取单个客户的完整上下文。")
    client_context.add_argument("--query", required=True, help="姓名、电话尾号或客户行号。")
    client_context.add_argument("--recent-limit", type=int, default=12, help="最近跟进条数。")
    client_context.add_argument("--include-all-followups", action="store_true", help="返回全部跟进记录。")
    client_context.set_defaults(handler=cmd_client_context)

    property_search = subparsers.add_parser("property-search", help="按条件筛选房源。")
    property_search.add_argument("--query", help="房源编号、小区名、板块或区域关键词。")
    property_search.add_argument("--district", help="限定区域。")
    property_search.add_argument("--community", help="限定小区。")
    property_search.add_argument("--rooms", type=int, help="限定房间数。")
    property_search.add_argument("--min-price", type=float, help="最低总价（万）。")
    property_search.add_argument("--max-price", type=float, help="最高总价（万）。")
    property_search.add_argument("--min-sqm", type=float, help="最小面积。")
    property_search.add_argument("--max-sqm", type=float, help="最大面积。")
    property_search.add_argument("--min-score", type=float, help="最低房源分。")
    property_search.add_argument("--limit", type=int, default=20, help="最多返回多少套。")
    property_search.set_defaults(handler=cmd_property_search)

    property_detail = subparsers.add_parser("property-detail", help="抓取单套房源详情。")
    property_detail.add_argument("--house-id", help="12 位房源编号。")
    property_detail.add_argument("--query", help="房源编号、小区名或板块关键词。")
    property_detail.set_defaults(handler=cmd_property_detail)

    write_followup = subparsers.add_parser("write-followup", help="给单个客户写入跟进。")
    write_followup.add_argument("--query", required=True, help="姓名、电话尾号或客户行号。")
    write_followup.add_argument("--content", required=True, help="跟进内容。")
    write_followup.add_argument("--date", default=date.today().isoformat(), help="跟进日期，格式 YYYY-MM-DD。")
    write_followup.add_argument("--dry-run", action="store_true", help="只预览目标客户和日期列，不实际写入。")
    write_followup.add_argument("--skip-refresh", action="store_true", help="写入后跳过缓存重建。")
    write_followup.set_defaults(handler=cmd_write_followup)

    update_followup = subparsers.add_parser("update-followup", help="修改单个客户的历史跟进记录（智能合并，不会丢失原内容）。")
    update_followup.add_argument("--query", required=True, help="姓名、电话尾号或客户行号。")
    update_followup.add_argument("--date", required=True, help="跟进日期，格式 YYYY-MM-DD。")
    update_followup.add_argument("--instruction", required=True, help="修改指令，例如：'把决策权描述改成客户本人主导' 或 '修正老婆话语权描述'。")
    update_followup.add_argument("--dry-run", action="store_true", help="只预览修改效果，不实际写入。")
    update_followup.add_argument("--skip-refresh", action="store_true", help="更新后跳过缓存重建。")
    update_followup.set_defaults(handler=cmd_update_followup)

    client_update = subparsers.add_parser("client-update", help="安全更新客户基础信息。")
    client_update.add_argument("--query", required=True, help="姓名、电话尾号或客户行号。")
    client_update.add_argument(
        "--set",
        action="append",
        required=True,
        help="字段更新，格式 field=value，可重复传入。",
    )
    client_update.add_argument("--dry-run", action="store_true", help="只预览修改，不实际写入。")
    client_update.add_argument("--skip-refresh", action="store_true", help="更新后跳过缓存重建。")
    client_update.set_defaults(handler=cmd_client_update)

    client_update_from_text = subparsers.add_parser("client-update-from-text", help="把自然语言修改意见转成客户字段更新。")
    client_update_from_text.add_argument("--query", required=True, help="姓名、电话尾号或客户行号。")
    client_update_from_text.add_argument("--instruction", required=True, help="自然语言修改意见。")
    client_update_from_text.add_argument("--dry-run", action="store_true", help="只预览解析结果，不实际写入。")
    client_update_from_text.add_argument("--skip-refresh", action="store_true", help="更新后跳过缓存重建。")
    client_update_from_text.set_defaults(handler=cmd_client_update_from_text)

    client_triage = subparsers.add_parser("client-triage", help="按跟进优先级盘点客户。")
    client_triage.add_argument("--limit", type=int, default=15, help="每个分组最多返回多少个客户。")
    client_triage.set_defaults(handler=cmd_client_triage)

    client_daily_brief = subparsers.add_parser("client-daily-brief", help="生成今天值得跟进客户的可执行清单。")
    client_daily_brief.add_argument("--limit", type=int, default=20, help="最多返回多少位重点客户。")
    client_daily_brief.add_argument("--wait-limit", type=int, default=10, help="最多返回多少位可暂缓客户。")
    client_daily_brief.set_defaults(handler=cmd_client_daily_brief)

    client_match = subparsers.add_parser("client-match-properties", help="按客户需求筛房并避开重复推荐。")
    client_match.add_argument("--query", required=True, help="姓名、电话尾号或客户行号。")
    client_match.add_argument("--limit", type=int, default=10, help="最多返回多少套房源。")
    client_match.add_argument("--include-recommended", action="store_true", help="允许返回历史已推荐过的房源。")
    client_match.set_defaults(handler=cmd_client_match_properties)

    experience_draft = subparsers.add_parser("experience-draft", help="从自然语言生成经验草稿，等待人工审阅。")
    experience_draft.add_argument("--text", required=True, help="经验原文或总结原话。")
    experience_draft.add_argument("--question", help="对应的原始问题。")
    experience_draft.add_argument("--feedback", help="你对模型判断的修正或补充。")
    experience_draft.add_argument("--kind", choices=["auto", "business", "technical"], default="auto", help="经验类型。")
    experience_draft.add_argument("--title", help="可选标题。")
    experience_draft.add_argument("--tag", action="append", help="显式标签，例如 S5/C3/B9/T2。可重复传入。")
    experience_draft.set_defaults(handler=cmd_experience_draft)

    experience_draft_list = subparsers.add_parser("experience-draft-list", help="查看经验草稿列表。")
    experience_draft_list.add_argument("--status", help="按状态筛选，例如 draft 或 approved。")
    experience_draft_list.add_argument("--kind", choices=["business", "technical"], help="按经验类型筛选。")
    experience_draft_list.add_argument("--limit", type=int, default=20, help="最多返回多少条草稿。")
    experience_draft_list.set_defaults(handler=cmd_experience_draft_list)

    experience_draft_revise = subparsers.add_parser("experience-draft-revise", help="用自然语言修改经验草稿。")
    experience_draft_revise.add_argument("--draft-id", required=True, help="草稿 ID。")
    experience_draft_revise.add_argument("--instruction", required=True, help="自然语言修改意见。")
    experience_draft_revise.add_argument("--dry-run", action="store_true", help="只预览修改结果，不实际保存。")
    experience_draft_revise.set_defaults(handler=cmd_experience_draft_revise)

    experience_approve = subparsers.add_parser("experience-approve", help="批准经验草稿并写入正式经验库。")
    experience_approve.add_argument("--draft-id", required=True, help="草稿 ID。")
    experience_approve.add_argument("--review-note", help="审核备注。")
    experience_approve.add_argument("--dry-run", action="store_true", help="只预览将要写入的内容。")
    experience_approve.add_argument("--skip-refresh", action="store_true", help="批准后跳过缓存刷新。")
    experience_approve.set_defaults(handler=cmd_experience_approve)

    experience_query = subparsers.add_parser("experience-query", help="查询已批准经验和历史经验。")
    experience_query.add_argument("--query", required=True, help="查询语句。")
    experience_query.add_argument("--kind", choices=["auto", "business", "technical"], default="auto", help="限定经验类型。")
    experience_query.add_argument("--limit", type=int, default=5, help="最多返回多少条经验。")
    experience_query.set_defaults(handler=cmd_experience_query)

    client_recommend = subparsers.add_parser("client-recommend-properties", help="为单个客户先粗筛房源，再抓详情后精选推荐。")
    client_recommend.add_argument("--query", required=True, help="姓名、电话尾号或客户行号。")
    client_recommend.add_argument("--candidate-limit", type=int, default=5, help="粗筛后最多抓详情的候选套数。")
    client_recommend.add_argument("--final-limit", type=int, default=3, help="最终最多推荐多少套。")
    client_recommend.add_argument("--include-recommended", action="store_true", help="允许返回历史已推荐过的房源。")
    client_recommend.set_defaults(handler=cmd_client_recommend_properties)

    client_grade_adjust = subparsers.add_parser("client-grade-adjust", help="分析客户等级升降级建议并执行调整。")
    client_grade_adjust.set_defaults(handler=cmd_client_grade_adjust)

    core_guard_status = subparsers.add_parser("core-guard-status", help="检查受保护核心架构是否完好。")
    core_guard_status.set_defaults(handler=cmd_core_guard_status)

    core_guard_freeze = subparsers.add_parser("core-guard-freeze", help="冻结当前核心架构快照。")
    core_guard_freeze.add_argument("--reason", help="可选：本次冻结的原因。")
    core_guard_freeze.set_defaults(handler=cmd_core_guard_freeze)

    return parser


def cmd_doctor(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    payload: dict[str, Any] = {
        "command": "doctor",
        "workbook_exists": WORKBOOK_PATH.exists(),
        "workbook_path": str(WORKBOOK_PATH),
        "cache_path": str(CACHE_FILE),
        "house_detail_cmd_exists": HOUSE_DETAIL_CMD.exists(),
        "export_csv_exists": EXPORT_CSV_VBS.exists(),
        "win32com_available": pythoncom is not None and DispatchEx is not None,
    }
    if not WORKBOOK_PATH.exists():
        payload["status"] = "error"
        payload["message"] = "主表不存在。"
        return payload, 1

    cache = ensure_cache(force=args.rebuild)
    payload["status"] = "ok"
    payload["cache_generated_at"] = cache["generated_at"]
    payload["workbook_mtime"] = cache["source"]["workbook_mtime"]
    payload["client_count"] = len(cache["clients"])
    payload["property_count"] = len(cache["properties"])
    payload["business_experience_count"] = len(cache.get("business_experiences", []))
    payload["technical_experience_count"] = len(cache.get("technical_experiences", []))
    payload["cache_is_fresh"] = cache_is_fresh(cache)
    core_guard = evaluate_core_guard()
    payload["core_guard"] = {
        "status": core_guard.get("status"),
        "protected_count": core_guard.get("protected_count"),
        "drift_count": len(core_guard.get("drift", [])),
        "unlocked_count": len(core_guard.get("unlocked_paths", [])),
        "manifest_path": str(CORE_GUARD_MANIFEST),
    }
    return payload, 0


def cmd_refresh(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    cache = build_cache()
    payload: dict[str, Any] = {
        "status": "ok",
        "command": "refresh",
        "cache_generated_at": cache["generated_at"],
        "client_count": len(cache["clients"]),
        "property_count": len(cache["properties"]),
        "business_experience_count": len(cache.get("business_experiences", [])),
        "technical_experience_count": len(cache.get("technical_experiences", [])),
        "cache_path": str(CACHE_FILE),
    }
    if args.sync_csv:
        payload["csv_sync"] = run_export_csv()
    return payload, 0


def cmd_core_guard_status(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    payload = evaluate_core_guard()
    return payload, 0 if payload.get("status") == "ok" else 1


def cmd_core_guard_freeze(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    manifest = freeze_core_guard_manifest(reason=clean_text(getattr(args, "reason", "")))
    status = evaluate_core_guard()
    return {
        "status": "success",
        "command": "core-guard-freeze",
        "manifest_path": str(CORE_GUARD_MANIFEST),
        "manifest": manifest,
        "verification": {
            "status": status.get("status"),
            "protected_count": status.get("protected_count"),
            "drift_count": len(status.get("drift", [])),
            "unlocked_count": len(status.get("unlocked_paths", [])),
        },
    }, 0


def cmd_client_search(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    cache = ensure_cache()
    matches = search_clients(cache["clients"], args.query)
    if not matches:
        return {"status": "not_found", "query": args.query, "candidates": [], "message": "没有找到匹配客户。"}, 1

    candidates = [client_brief(item["record"]) for item in matches[: args.limit]]
    status = "success" if len(matches) == 1 else "ambiguous"
    payload = {"status": status, "query": args.query, "match_count": len(matches), "candidates": candidates}
    if len(matches) > 1:
        payload["message"] = "命中多个客户，请改用更精确的姓名、电话或直接使用行号。"
    return payload, 0 if len(matches) == 1 else 1


def cmd_client_context(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1

    client = resolved["client"]
    followups = client.get("followups", [])
    if not args.include_all_followups:
        followups = followups[-args.recent_limit :]
    payload = {
        "status": "success",
        "query": args.query,
        "client": client_without_followups(client),
        "followups": {
            "total": client.get("followup_count", 0),
            "latest_date": client.get("last_followup_date"),
            "recent": list(reversed(followups)),
        },
    }
    return payload, 0


def cmd_property_search(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    cache = ensure_cache()
    matches = search_properties(cache["properties"], args)
    payload = {
        "status": "success",
        "query": args.query,
        "filters": {
            "district": args.district,
            "community": args.community,
            "rooms": args.rooms,
            "min_price": args.min_price,
            "max_price": args.max_price,
            "min_sqm": args.min_sqm,
            "max_sqm": args.max_sqm,
            "min_score": args.min_score,
        },
        "match_count": len(matches),
        "properties": [property_brief(item["record"]) for item in matches[: args.limit]],
    }
    return payload, 0


def cmd_property_detail(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    house_id = clean_text(args.house_id)
    source_record: dict[str, Any] | None = None

    if not house_id:
        if not args.query:
            return {"status": "error", "message": "请提供 --house-id 或 --query。"}, 1
        cache = ensure_cache()
        search_args = argparse.Namespace(
            query=args.query,
            district=None,
            community=None,
            rooms=None,
            min_price=None,
            max_price=None,
            min_sqm=None,
            max_sqm=None,
            min_score=None,
            limit=10,
        )
        matches = search_properties(cache["properties"], search_args)
        if not matches:
            return {"status": "not_found", "query": args.query, "message": "没有找到匹配房源。"}, 1
        if len(matches) > 1:
            return {
                "status": "ambiguous",
                "query": args.query,
                "message": "命中多套房源，请优先使用房源编号。",
                "candidates": [property_brief(item["record"]) for item in matches[:10]],
            }, 1
        source_record = matches[0]["record"]
        house_id = source_record["house_id"]

    if not HOUSE_DETAIL_CMD.exists():
        return {"status": "error", "message": "房源详情脚本入口不存在。", "house_detail_cmd": str(HOUSE_DETAIL_CMD)}, 1

    result = subprocess.run(
        ["cmd", "/c", str(HOUSE_DETAIL_CMD), house_id],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    payload: dict[str, Any] = {
        "command": "property-detail",
        "house_id": house_id,
        "exit_code": result.returncode,
        "stdout": clean_text(result.stdout),
        "stderr": clean_text(result.stderr),
    }
    if source_record:
        payload["record"] = property_brief(source_record)
    if HOUSE_DETAIL_JSON.exists():
        try:
            payload["detail_result"] = json.loads(HOUSE_DETAIL_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload["detail_result_error"] = "last_house_detail.json 不是有效 JSON。"

    payload["status"] = "success" if result.returncode == 0 else "error"
    return payload, 0 if result.returncode == 0 else 1


def fetch_property_detail_payload(
    house_id: str,
    source_record: dict[str, Any] | None = None,
    detail_cache: dict[str, Any] | None = None,
) -> dict[str, Any]:
    house_id = clean_text(house_id)
    if not house_id:
        return {"status": "error", "message": "缺少房源编号。", "house_id": house_id}
    if not HOUSE_DETAIL_CMD.exists():
        return {
            "status": "error",
            "message": "房源详情脚本入口不存在。",
            "house_detail_cmd": str(HOUSE_DETAIL_CMD),
            "house_id": house_id,
        }

    cache_store = detail_cache if detail_cache is not None else load_property_detail_cache()
    cached_payload = load_cached_property_detail(cache_store, house_id)
    if cached_payload is not None:
        payload = dict(cached_payload)
        if source_record and "record" not in payload:
            payload["record"] = property_brief(source_record)
        payload["cache_hit"] = True
        return payload

    result = subprocess.run(
        ["cmd", "/c", str(HOUSE_DETAIL_CMD), house_id],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    payload: dict[str, Any] = {
        "command": "property-detail",
        "house_id": house_id,
        "exit_code": result.returncode,
        "stdout": clean_text(result.stdout),
        "stderr": clean_text(result.stderr),
    }
    if source_record:
        payload["record"] = property_brief(source_record)
    if HOUSE_DETAIL_JSON.exists():
        try:
            payload["detail_result"] = json.loads(HOUSE_DETAIL_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload["detail_result_error"] = "last_house_detail.json 不是有效 JSON。"

    payload["status"] = "success" if result.returncode == 0 else "error"
    payload["cache_hit"] = False
    store_property_detail(cache_store, house_id, payload)
    if detail_cache is None:
        save_property_detail_cache(cache_store)
    return payload


def load_property_detail_cache() -> dict[str, Any]:
    if not PROPERTY_DETAIL_CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(PROPERTY_DETAIL_CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_property_detail_cache(cache: dict[str, Any]) -> None:
    PROPERTY_DETAIL_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROPERTY_DETAIL_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cached_property_detail(cache: dict[str, Any], house_id: str) -> dict[str, Any] | None:
    entry = cache.get(house_id)
    if not isinstance(entry, dict):
        return None
    fetched_at = clean_text(entry.get("fetched_at"))
    payload = entry.get("payload")
    if not isinstance(payload, dict):
        return None
    if payload.get("status") != "success":
        return None
    if not fetched_at.startswith(date.today().isoformat()):
        return None
    return payload


def store_property_detail(cache: dict[str, Any], house_id: str, payload: dict[str, Any]) -> None:
    cache[house_id] = {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "payload": payload,
    }


def freeze_core_guard_manifest(reason: str = "") -> dict[str, Any]:
    manifest = {
        "version": 1,
        "frozen_at": datetime.now().isoformat(timespec="seconds"),
        "workspace_root": str(WORKSPACE_ROOT),
        "reason": clean_text(reason),
        "protected_paths": PROTECTED_CORE_PATHS,
        "allowed_write_areas": ALLOWED_WRITE_AREAS,
        "hashes": {path: sha256_file(WORKSPACE_ROOT / path) for path in PROTECTED_CORE_PATHS},
    }
    CORE_GUARD_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    CORE_GUARD_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def evaluate_core_guard() -> dict[str, Any]:
    if not CORE_GUARD_MANIFEST.exists():
        return {
            "status": "missing_manifest",
            "command": "core-guard-status",
            "manifest_exists": False,
            "manifest_path": str(CORE_GUARD_MANIFEST),
            "message": "核心保护清单尚未冻结，请先执行 core-guard-freeze。",
            "protected_count": len(PROTECTED_CORE_PATHS),
            "drift": [],
            "unlocked_paths": [],
            "allowed_write_areas": ALLOWED_WRITE_AREAS,
        }

    try:
        manifest = json.loads(CORE_GUARD_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "invalid_manifest",
            "command": "core-guard-status",
            "manifest_exists": True,
            "manifest_path": str(CORE_GUARD_MANIFEST),
            "message": f"核心保护清单读取失败：{exc}",
            "protected_count": len(PROTECTED_CORE_PATHS),
            "drift": [],
            "unlocked_paths": [],
            "allowed_write_areas": ALLOWED_WRITE_AREAS,
        }

    protected_paths = manifest.get("protected_paths", PROTECTED_CORE_PATHS)
    expected_hashes = manifest.get("hashes", {})
    drift: list[dict[str, Any]] = []
    unlocked_paths: list[str] = []
    missing_paths: list[str] = []

    for relative_path in protected_paths:
        path = WORKSPACE_ROOT / relative_path
        if not path.exists():
            missing_paths.append(relative_path)
            drift.append({"path": relative_path, "issue": "missing"})
            continue

        actual_hash = sha256_file(path)
        expected_hash = expected_hashes.get(relative_path)
        if expected_hash and actual_hash != expected_hash:
            drift.append(
                {
                    "path": relative_path,
                    "issue": "modified",
                    "expected_sha256": expected_hash,
                    "actual_sha256": actual_hash,
                }
            )

        if not path_is_readonly(path):
            unlocked_paths.append(relative_path)

    return {
        "status": "ok" if not drift else "drift",
        "command": "core-guard-status",
        "manifest_exists": True,
        "manifest_path": str(CORE_GUARD_MANIFEST),
        "frozen_at": manifest.get("frozen_at"),
        "reason": manifest.get("reason", ""),
        "protected_count": len(protected_paths),
        "allowed_write_areas": manifest.get("allowed_write_areas", ALLOWED_WRITE_AREAS),
        "missing_paths": missing_paths,
        "unlocked_paths": unlocked_paths,
        "drift": drift,
    }


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_is_readonly(path: Path) -> bool:
    try:
        file_attributes = getattr(path.stat(), "st_file_attributes", 0)
    except OSError:
        return False
    if file_attributes:
        return bool(file_attributes & 0x1)
    return False


def cmd_write_followup(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """
    【自动添加跟进标签规则】
    执行写入跟进时，根据内容自动添加标签：
    - 如果内容描述的是“已完成的带看/看房” → 添加【有带看】
    - 如果内容描述的是“已通的电话” → 添加【通电话】
    - 如果内容描述的是“客户的回复/回应” → 添加【有回复】
    - 如果内容描述的是“分析/判断/想法” → 添加【解读】
    
    示例：
    - “带看了天山星城” → 【有带看】
    - “电话沟通 10 分钟” → 【通电话】
    - “客户回复说再看看” → 【有回复】
    - “客户纠结价格” → 【解读】
    - “约下次看房” → 【解读】（因为不是已完成的行为）
    """
    # AI 注意：请根据上述规则，在写入跟进前自动添加对应标签
    # 理解整个跟进内容的语义，不要只看关键词
    # 例如：“电话约看房”是通电话，不是有带看
    
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1

    client = resolved["client"]
    followup_insights = analyze_followup_content(client, clean_text(args.content), cache["properties"])
    if args.dry_run:
        preview = preview_followup_target(args.date)
        return {
            "status": "success",
            "command": "write-followup",
            "dry_run": True,
            "query": args.query,
            "client": client_brief(client),
            "preview": {
                "row": client["row"],
                "date": preview["date"],
                "column": preview["column"],
                "created_new_date_column": preview["created_new_date_column"],
                "content": clean_text(args.content),
            },
            "followup_insights": followup_insights,
        }, 0

    try:
        write_result = write_followup_via_excel(
            row_number=client["row"],
            content=args.content,
            date_str=args.date,
        )
    except Exception as exc:
        return {
            "status": "error",
            "message": f"写入跟进失败：{exc}",
            "query": args.query,
            "client": client_brief(client),
        }, 1

    # 【优化】跳过缓存刷新，避免 Excel 对话框问题
    # 缓存只是加速查询，晚几分钟更新没关系
    # 用户可以手动刷新：cmd /c RUN_TUANTUAN_qidong.cmd refresh
    refreshed = None
    # if not args.skip_refresh:
    #     refreshed = build_cache()

    payload = {
        "status": "success",
        "command": "write-followup",
        "query": args.query,
        "client": client_brief(client),
        "write_result": write_result,
        "followup_insights": followup_insights,
    }
    if refreshed is not None:
        payload["cache_generated_at"] = refreshed["generated_at"]
    return payload, 0


def cmd_update_followup(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """智能更新跟进记录：读取原内容 -> 分析修改指令 -> 合并生成新内容 -> 写入"""
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1

    client = resolved["client"]
    preview = preview_followup_target(args.date)
    existing_content = ""
    if preview.get("column"):
        existing_content = get_existing_followup_content(client["row"], preview["column"])

    if not existing_content:
        return {
            "status": "error",
            "message": f"未找到 {args.date} 的跟进记录，无法修改。",
            "query": args.query,
            "client": client_brief(client),
            "date": args.date,
        }, 1

    # 调用 LLM 智能合并修改
    merged_content = merge_followup_content(existing_content, args.instruction)

    if args.dry_run:
        return {
            "status": "success",
            "command": "update-followup",
            "dry_run": True,
            "query": args.query,
            "client": client_brief(client),
            "preview": {
                "row": client["row"],
                "date": preview["date"],
                "column": preview["column"],
                "existing_content": existing_content,
                "instruction": args.instruction,
                "merged_content": merged_content,
            },
        }, 0

    try:
        update_result = update_followup_via_excel(
            row_number=client["row"],
            content=merged_content,
            date_str=args.date,
        )
    except Exception as exc:
        return {
            "status": "error",
            "message": f"更新跟进失败：{exc}",
            "query": args.query,
            "client": client_brief(client),
        }, 1

    # 【优化】跳过缓存刷新，避免 Excel 对话框问题
    # 缓存只是加速查询，晚几分钟更新没关系
    # 用户可以手动刷新：cmd /c RUN_TUANTUAN_qidong.cmd refresh
    refreshed = None
    # if not args.skip_refresh:
    #     refreshed = build_cache()

    payload = {
        "status": "success",
        "command": "update-followup",
        "query": args.query,
        "client": client_brief(client),
        "update_result": update_result,
        "merge_info": {
            "original": existing_content,
            "instruction": args.instruction,
            "merged": merged_content,
        },
    }
    if refreshed is not None:
        payload["cache_generated_at"] = refreshed["generated_at"]
    return payload, 0


def merge_followup_content(existing: str, instruction: str) -> str:
    """使用 LLM 智能合并原内容和修改指令"""
    prompt = f"""你是房产经纪助手。请根据修改指令，在原跟进记录基础上进行修改，保留其他信息。

原跟进记录：
{existing}

修改指令：
{instruction}

要求：
1. 只修改指令中提到的部分，其他内容原样保留
2. 保持原有语气和格式
3. 直接输出修改后的完整内容，不要解释

修改后的内容："""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL)
        response = client.chat.completions.create(
            model=DASHSCOPE_DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        merged = response.choices[0].message.content.strip()
        return merged if merged else existing
    except Exception:
        # LLM 调用失败时返回原内容
        return existing


def get_existing_followup_content(row_number: int, column: int) -> str:
    """获取指定单元格的跟进内容"""
    if pythoncom is None or DispatchEx is None or GetObject is None:
        return ""
    
    pythoncom.CoInitialize()
    excel = None
    workbook = None
    created_app = False
    opened_here = False

    try:
        try:
            excel = GetObject(Class="Excel.Application")
        except Exception:
            excel = DispatchEx("Excel.Application")
            created_app = True

        excel.DisplayAlerts = False
        workbook = find_open_workbook(excel, WORKBOOK_PATH)
        if workbook is None:
            workbook = excel.Workbooks.Open(
                Filename=str(WORKBOOK_PATH),
                UpdateLinks=0,
                ReadOnly=True,
                Password=WORKBOOK_PASSWORD,
            )
            opened_here = True

        ws = workbook.Worksheets(CLIENT_SHEET_INDEX)
        return clean_text(ws.Cells(row_number, column).Value)
    finally:
        if workbook is not None and opened_here:
            try:
                workbook.Close(SaveChanges=False)
            except Exception:
                pass
        if excel is not None and created_app:
            try:
                excel.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def update_followup_via_excel(*, row_number: int, content: str, date_str: str) -> dict[str, Any]:
    """更新指定日期的跟进记录"""
    if pythoncom is None or DispatchEx is None or GetObject is None:
        raise RuntimeError("win32com 不可用，无法进行安全写入。")

    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    content = clean_text(content)
    if not content:
        raise ValueError("跟进内容为空。")

    # 先用 openpyxl 找到列号（避免 win32com 日期转换问题）
    preview = preview_followup_target(date_str)
    target_col = preview["column"]
    created_new = preview["created_new_date_column"]

    pythoncom.CoInitialize()
    excel = None
    workbook = None
    created_app = False
    opened_here = False

    try:
        try:
            excel = GetObject(Class="Excel.Application")
        except Exception:
            excel = DispatchEx("Excel.Application")
            created_app = True

        excel.DisplayAlerts = False
        workbook = find_open_workbook(excel, WORKBOOK_PATH)
        if workbook is None:
            workbook = excel.Workbooks.Open(
                Filename=str(WORKBOOK_PATH),
                UpdateLinks=0,
                ReadOnly=False,
                Password=WORKBOOK_PASSWORD,
            )
            opened_here = True

        ws = workbook.Worksheets(CLIENT_SHEET_INDEX)
        existing = clean_text(ws.Cells(row_number, target_col).Value)
        if target_col == FIRST_FOLLOWUP_COLUMN and looks_like_group(existing):
            raise RuntimeError("首个跟进列仍占用组别标记，拒绝覆盖，请改用更晚日期。")
        
        if existing == content:
            action = "unchanged"
        else:
            ws.Cells(row_number, target_col).Value = content
            action = "updated" if existing else "written"
        
        workbook.Save()

        return {
            "row": row_number,
            "column": target_col,
            "date": target_date.isoformat(),
            "old_content": existing,
            "new_content": content,
            "action": action,
            "created_new_date_column": created_new,
        }
    finally:
        if workbook is not None and opened_here:
            try:
                workbook.Close(SaveChanges=False)
            except Exception:
                pass
        if excel is not None and created_app:
            try:
                excel.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def cmd_client_update(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1

    client = resolved["client"]
    updates = parse_client_updates(args.set, client)
    if args.dry_run:
        return {
            "status": "success",
            "command": "client-update",
            "dry_run": True,
            "query": args.query,
            "client": client_brief(client),
            "updates": updates,
        }, 0

    try:
        write_result = update_client_fields_via_excel(client["row"], updates)
    except Exception as exc:
        return {
            "status": "error",
            "message": f"更新客户基础信息失败：{exc}",
            "query": args.query,
            "client": client_brief(client),
            "updates": updates,
        }, 1

    # 【优化】跳过缓存刷新，避免 Excel 对话框问题
    # 缓存只是加速查询，晚几分钟更新没关系
    # 用户可以手动刷新：cmd /c RUN_TUANTUAN_qidong.cmd refresh
    refreshed = None
    # if not args.skip_refresh:
    #     refreshed = build_cache()

    payload = {
        "status": "success",
        "command": "client-update",
        "query": args.query,
        "client": client_brief(client),
        "updates": write_result,
    }
    if refreshed is not None:
        payload["cache_generated_at"] = refreshed["generated_at"]
    return payload, 0


def cmd_client_update_from_text(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1

    client = resolved["client"]
    plan = parse_client_update_instruction(client, args.instruction)
    if not plan["updates"] and not plan["ignored_fields"]:
        return {
            "status": "no_update",
            "command": "client-update-from-text",
            "query": args.query,
            "client": client_brief(client),
            "instruction": clean_text(args.instruction),
            "message": "没有从这句话里解析出可执行的字段修改。",
        }, 1

    if args.dry_run:
        return {
            "status": "success",
            "command": "client-update-from-text",
            "dry_run": True,
            "query": args.query,
            "client": client_brief(client),
            "instruction": clean_text(args.instruction),
            "updates": plan["updates"],
            "ignored_fields": plan["ignored_fields"],
            "unparsed_clauses": plan["unparsed_clauses"],
        }, 0

    try:
        write_result = update_client_fields_via_excel(client["row"], plan["updates"])
    except Exception as exc:
        return {
            "status": "error",
            "message": f"按自然语言更新客户失败：{exc}",
            "query": args.query,
            "client": client_brief(client),
            "instruction": clean_text(args.instruction),
            "updates": plan["updates"],
        }, 1

    # 【优化】跳过缓存刷新，避免 Excel 对话框问题
    # 缓存只是加速查询，晚几分钟更新没关系
    # 用户可以手动刷新：cmd /c RUN_TUANTUAN_qidong.cmd refresh
    refreshed = None
    # if not args.skip_refresh:
    #     refreshed = build_cache()

    payload = {
        "status": "success",
        "command": "client-update-from-text",
        "query": args.query,
        "client": client_brief(client),
        "instruction": clean_text(args.instruction),
        "updates": write_result,
        "ignored_fields": plan["ignored_fields"],
        "unparsed_clauses": plan["unparsed_clauses"],
    }
    if refreshed is not None:
        payload["cache_generated_at"] = refreshed["generated_at"]
    return payload, 0


def cmd_client_triage(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    cache = ensure_cache()
    scored = []
    for client in cache["clients"]:
        triage = analyze_client_triage(client)
        scored.append({"client": client, "triage": triage})

    follow_now = [item for item in scored if item["triage"]["bucket"] == "follow_now"]
    can_wait = [item for item in scored if item["triage"]["bucket"] == "can_wait"]
    low_signal = [item for item in scored if item["triage"]["bucket"] == "low_signal"]

    follow_now.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"], item["client"]["row"]))
    can_wait.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"], item["client"]["row"]))
    low_signal.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"], item["client"]["row"]))

    return {
        "status": "success",
        "command": "client-triage",
        "generated_at": cache["generated_at"],
        "follow_now": [triage_brief(item) for item in follow_now[: args.limit]],
        "can_wait": [triage_brief(item) for item in can_wait[: args.limit]],
        "low_signal": [triage_brief(item) for item in low_signal[: args.limit]],
    }, 0


def cmd_client_daily_brief(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    cache = ensure_cache()
    scored: list[dict[str, Any]] = []
    for client in cache["clients"]:
        triage = analyze_client_triage(client)
        scored.append({"client": client, "triage": triage})

    # 分桶：A 级、趁热、保底、其他
    grade_a = [item for item in scored if clean_text(item["client"].get("grade")).upper() == "A"]
    is_re_hot = [item for item in scored if item["triage"].get("is_re_hot", False) and item not in grade_a]
    is_forget_protection = [
        item for item in scored
        if item["triage"].get("is_forget_protection", False)
        and item not in grade_a
        and item not in is_re_hot
    ]
    can_wait = [item for item in scored if item["triage"]["bucket"] == "can_wait" and item not in grade_a and item not in is_re_hot and item not in is_forget_protection]
    low_signal_count = len([item for item in scored if item["triage"]["bucket"] == "low_signal"])

    # 排序：保底按 score 排序
    is_forget_protection.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"], item["client"]["row"]))
    can_wait.sort(key=lambda item: (-item["triage"]["score"], item["client"]["name"], item["client"]["row"]))

    # 组装：A 级全部 + 趁热全部 + 保底凑满 limit
    priority_list = grade_a + is_re_hot
    remaining = max(0, args.limit - len(priority_list))
    priority_list += is_forget_protection[:remaining]

    return {
        "status": "success",
        "command": "client-daily-brief",
        "generated_at": cache["generated_at"],
        "priority_clients": [daily_brief_item(item) for item in priority_list],
        "can_wait": [daily_brief_item(item) for item in can_wait[: args.wait_limit]],
        "summary": {
            "priority_count": len(priority_list),
            "can_wait_count": len(can_wait),
            "low_signal_count": low_signal_count,
            "grade_a_count": len(grade_a),
            "re_hot_count": len(is_re_hot),
            "forget_protection_count": min(len(is_forget_protection), remaining),
        },
    }, 0


def cmd_client_match_properties(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1

    client = resolved["client"]
    matches, excluded = match_properties_for_client(
        client=client,
        properties=cache["properties"],
        limit=args.limit,
        include_recommended=args.include_recommended,
    )
    return {
        "status": "success",
        "command": "client-match-properties",
        "query": args.query,
        "client": client_brief(client),
        "client_preferences": build_client_preferences_summary(client),
        "excluded_recommended_count": len(excluded),
        "excluded_recommended_ids": excluded[:20],
        "properties": matches,
    }, 0


def cmd_client_recommend_properties(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    cache = ensure_cache()
    resolved = resolve_single_client(cache["clients"], args.query)
    if resolved["status"] != "success":
        return resolved, 1

    client = resolved["client"]
    recommendation = recommend_properties_for_client(
        client=client,
        properties=cache["properties"],
        candidate_limit=max(1, int(args.candidate_limit)),
        final_limit=max(1, int(args.final_limit)),
        include_recommended=args.include_recommended,
    )

    status = "success" if recommendation["final_recommendations"] else "no_recommendation"
    message = (
        f"已为 {client.get('name')} 先粗筛房源，再抓详情精选推荐。"
        if recommendation["final_recommendations"]
        else f"已完成粗筛和详情复核，但暂时没有足够把握直接推荐给 {client.get('name')} 的房源。"
    )

    return {
        "status": status,
        "command": "client-recommend-properties",
        "query": args.query,
        "client": client_brief(client),
        "client_preferences": build_client_preferences_summary(client),
        "message": message,
        "recommendation_summary": recommendation["summary"],
        "excluded_recommended_count": len(recommendation["excluded_recommended"]),
        "excluded_recommended_ids": recommendation["excluded_recommended"][:20],
        "rough_candidates": recommendation["rough_candidates"],
        "reviewed_candidates": recommendation["reviewed_candidates"],
        "final_recommendations": recommendation["final_recommendations"],
    }, 0


def cmd_experience_draft(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    try:
        draft = build_experience_draft(
            text=args.text,
            question=args.question or "",
            feedback=args.feedback or "",
            requested_kind=args.kind,
            title=args.title or "",
            explicit_tags=args.tag,
        )
    except ValueError as exc:
        return {"status": "error", "command": "experience-draft", "message": str(exc)}, 1

    path = save_experience_draft(WORKSPACE_ROOT, draft)
    return {
        "status": "success",
        "command": "experience-draft",
        "draft_id": draft["id"],
        "draft_path": str(path),
        "draft": draft,
        "next_step": "请先审阅草稿；确认后再执行 experience-approve。",
    }, 0


def cmd_experience_draft_list(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    drafts = list_experience_drafts(WORKSPACE_ROOT, status=args.status, kind=args.kind)
    return {
        "status": "success",
        "command": "experience-draft-list",
        "count": len(drafts),
        "drafts": [summarize_draft(item) for item in drafts[: args.limit]],
    }, 0


def cmd_experience_draft_revise(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    draft = load_experience_draft(WORKSPACE_ROOT, args.draft_id)
    if draft is None:
        return {
            "status": "not_found",
            "command": "experience-draft-revise",
            "draft_id": args.draft_id,
            "message": "没有找到对应的经验草稿。",
        }, 1

    plan = parse_draft_revision_instruction(draft, args.instruction)
    if not plan["changes"] and not plan["ignored_fields"]:
        return {
            "status": "no_update",
            "command": "experience-draft-revise",
            "draft_id": args.draft_id,
            "instruction": clean_text(args.instruction),
            "message": "这句修改意见里没有解析出可执行的草稿修改。",
            "unparsed_clauses": plan["unparsed_clauses"],
        }, 1

    revised = apply_draft_revision(draft, plan)
    if args.dry_run:
        return {
            "status": "success",
            "command": "experience-draft-revise",
            "dry_run": True,
            "draft_id": args.draft_id,
            "instruction": clean_text(args.instruction),
            "changes": plan["changes"],
            "ignored_fields": plan["ignored_fields"],
            "unparsed_clauses": plan["unparsed_clauses"],
            "draft": revised,
        }, 0

    path = save_experience_draft(WORKSPACE_ROOT, revised)
    return {
        "status": "success",
        "command": "experience-draft-revise",
        "draft_id": args.draft_id,
        "draft_path": str(path),
        "instruction": clean_text(args.instruction),
        "changes": plan["changes"],
        "ignored_fields": plan["ignored_fields"],
        "unparsed_clauses": plan["unparsed_clauses"],
        "draft": revised,
    }, 0


def cmd_experience_approve(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    draft = load_experience_draft(WORKSPACE_ROOT, args.draft_id)
    if draft is None:
        return {
            "status": "not_found",
            "command": "experience-approve",
            "draft_id": args.draft_id,
            "message": "没有找到对应的经验草稿。",
        }, 1

    approved = build_approved_entry(draft, args.review_note or "")
    preview = preview_experience_excel_sync(approved)
    if args.dry_run:
        return {
            "status": "success",
            "command": "experience-approve",
            "dry_run": True,
            "draft_id": args.draft_id,
            "entry": approved,
            "excel_preview": preview,
        }, 0

    excel_sync = sync_experience_entry_to_excel(approved)
    approved["excel_sync"] = excel_sync
    upsert_approved_entry(WORKSPACE_ROOT, approved)

    draft["status"] = "approved"
    draft["updated_at"] = approved["updated_at"]
    draft["review"] = approved.get("review", {})
    draft["excel_sync"] = excel_sync
    save_experience_draft(WORKSPACE_ROOT, draft)

    # 【优化】跳过缓存刷新，避免 Excel 对话框问题
    # 缓存只是加速查询，晚几分钟更新没关系
    # 用户可以手动刷新：cmd /c RUN_TUANTUAN_qidong.cmd refresh
    refreshed = None
    # if not args.skip_refresh:
    #     refreshed = build_cache()

    payload = {
        "status": "success",
        "command": "experience-approve",
        "draft_id": args.draft_id,
        "entry": approved,
        "excel_sync": excel_sync,
    }
    if refreshed is not None:
        payload["cache_generated_at"] = refreshed["generated_at"]
    return payload, 0


def cmd_experience_query(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    cache = ensure_cache()
    store_entries = load_experience_store(WORKSPACE_ROOT).get("entries", [])
    entries = dedupe_entries(store_entries + cache.get("business_experiences", []) + cache.get("technical_experiences", []))
    results = search_entries(entries, args.query, requested_kind=args.kind, limit=args.limit)
    return {
        "status": "success",
        "command": "experience-query",
        "query": args.query,
        "kind": args.kind,
        "total_hits": results["total_hits"],
        "query_profile": results["query_profile"],
        "results": [
            {
                "score": item["score"],
                "reasons": item["reasons"],
                "matched_terms": item["matched_terms"],
                "entry": summarize_experience_entry(item["entry"]),
            }
            for item in results["results"]
        ],
    }, 0


def cmd_client_grade_adjust(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """客户等级动态调整"""
    import subprocess
    
    script_path = Path(__file__).parent / "client_grade_adjust.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,
            encoding='utf-8',
            errors='replace',
        )
        
        output = result.stdout + result.stderr
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "command": "client-grade-adjust",
            "output": output,
            "returncode": result.returncode,
        }, 0 if result.returncode == 0 else 1
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "command": "client-grade-adjust",
            "message": "脚本执行超时（5 分钟）",
        }, 1
    except Exception as e:
        return {
            "status": "error",
            "command": "client-grade-adjust",
            "message": f"执行失败：{e}",
        }, 1


def ensure_cache(force: bool = False) -> dict[str, Any]:
    """获取缓存。优先使用现有缓存，即使不新鲜也比报错好。"""
    if force:
        return build_cache()

    cache = load_cache()
    
    # 如果有缓存，优先使用（即使不新鲜）
    if cache and cache_has_required_payload(cache):
        if not cache_is_fresh(cache):
            # 缓存不新鲜，记录警告但继续使用
            cache_age_hours = cache_age_in_hours(cache)
            if cache_age_hours > 24:
                # 超过 24 小时，提示用户
                pass  # 不阻断，继续使用
        return cache
    
    # 没有缓存时，检查 Excel 是否占用
    if is_workbook_open():
        raise RuntimeError(
            f"Excel 正在占用主表且没有可用缓存，请先关闭 Excel 文件后再重试：{WORKBOOK_PATH}"
        )
    
    # Excel 未占用，重建缓存
    return build_cache()


def is_workbook_open(target_path: Path | None = None) -> bool:
    if pythoncom is None or GetObject is None:
        return False

    resolved_target = (target_path or WORKBOOK_PATH).resolve()
    try:
        pythoncom.CoInitialize()
        excel = GetObject(Class="Excel.Application")
        for wb in excel.Workbooks:
            try:
                if Path(wb.FullName).resolve() == resolved_target:
                    return True
            except Exception:
                continue
    except Exception:
        return False
    return False


def wait_excel_closed(timeout_seconds: int = 60, kill_on_timeout: bool = False) -> None:
    """等待 Excel 关闭主表，最多等待 timeout_seconds 秒。如果 kill_on_timeout=True，超时后直接杀掉 Excel 进程。"""
    if pythoncom is None or DispatchEx is None:
        return  # 无法检查，直接返回

    import time
    start_time = time.time()
    while True:
        if not is_workbook_open():
            return  # 没有运行的 Excel 实例，正常

        elapsed = time.time() - start_time
        if elapsed >= timeout_seconds:
            if kill_on_timeout:
                _kill_excel_process()
                return
            raise RuntimeError(
                f"等待 Excel 关闭超时（{timeout_seconds}秒），请先关闭 Excel 或保存后关闭该文件：{WORKBOOK_PATH}"
            )
        time.sleep(1)


def _kill_excel_process() -> None:
    """强制关闭 Excel 进程。"""
    import subprocess
    result = subprocess.run(["taskkill", "/F", "/IM", "EXCEL.EXE"], capture_output=True)
    # 如果 Excel 已经关闭，不需要报错
    if result.returncode != 0:
        # 检查是否是因为"没有找到进程"
        stderr = result.stderr.decode('gbk', errors='ignore')
        if "没有找到进程" not in stderr and "no running instance" not in stderr.lower():
            raise RuntimeError(f"关闭 Excel 失败：{stderr}")


def build_cache() -> dict[str, Any]:
    if not WORKBOOK_PATH.exists():
        raise FileNotFoundError(f"主表不存在：{WORKBOOK_PATH}")

    # 【优化】先强制关闭 Excel 进程，确保文件未被占用
    _kill_excel_process()
    import time
    time.sleep(1)  # 等待 1 秒确保文件释放

    if pythoncom is None or DispatchEx is None or GetObject is None:
        raise RuntimeError("win32com 不可用，无法读取带密码的 Excel 文件。")

    pythoncom.CoInitialize()
    excel = None
    workbook = None

    try:
        # 直接创建新 Excel 实例打开文件
        excel = DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        # 使用 Open 方法打开文件
        workbook = excel.Workbooks.Open(
            Filename=str(WORKBOOK_PATH),
            UpdateLinks=0,
            ReadOnly=True,
            Password=WORKBOOK_PASSWORD,
        )

        client_sheet = workbook.Worksheets(CLIENT_SHEET_INDEX)
        property_sheet = workbook.Worksheets(PROPERTY_SHEET_INDEX)
        clients = parse_clients(client_sheet)
        properties = parse_properties(property_sheet)
        
        business_experiences = []
        technical_experiences = []
        for i in range(1, workbook.Worksheets.Count + 1):
            ws_name = workbook.Worksheets(i).Name
            if ws_name == BUSINESS_EXPERIENCE_SHEET_NAME:
                business_experiences = parse_business_experiences(workbook.Worksheets(i))
            elif ws_name == TECHNICAL_EXPERIENCE_SHEET_NAME:
                technical_experiences = parse_technical_experiences(workbook.Worksheets(i))

        cache = {
            "generated_at": iso_now(),
            "source": {
                "workbook_path": str(WORKBOOK_PATH),
                "workbook_mtime": workbook_mtime(),
            },
            "clients": clients,
            "properties": properties,
            "business_experiences": business_experiences,
            "technical_experiences": technical_experiences,
        }
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        return cache

    finally:
        if workbook is not None:
            try:
                workbook.Close(SaveChanges=False)
            except Exception:
                pass
        if excel is not None:
            try:
                excel.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def load_cache() -> dict[str, Any] | None:
    if not CACHE_FILE.exists():
        return None
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def cache_has_required_payload(cache: dict[str, Any] | None) -> bool:
    if not isinstance(cache, dict):
        return False
    required_keys = {"clients", "properties", "business_experiences", "technical_experiences"}
    return required_keys.issubset(cache.keys())


def cache_is_fresh(cache: dict[str, Any]) -> bool:
    if not cache_has_required_payload(cache):
        return False
    if not WORKBOOK_PATH.exists():
        return False
    source = cache.get("source", {})
    return source.get("workbook_mtime") == workbook_mtime()


def cache_age_in_hours(cache: dict[str, Any]) -> float:
    """计算缓存生成到现在的小时数"""
    from datetime import datetime
    generated_at = cache.get("generated_at", "")
    if not generated_at:
        return 999.0  # 无生成时间，视为很旧
    try:
        gen_time = datetime.fromisoformat(generated_at)
        age = datetime.now() - gen_time
        return age.total_seconds() / 3600.0
    except Exception:
        return 999.0


def workbook_mtime() -> str:
    return datetime.fromtimestamp(WORKBOOK_PATH.stat().st_mtime).isoformat(timespec="seconds")


def run_export_csv() -> dict[str, Any]:
    if not EXPORT_CSV_VBS.exists():
        return {"status": "missing", "message": "旧版 CSV 导出脚本不存在。"}

    result = subprocess.run(
        ["cscript", "//nologo", str(EXPORT_CSV_VBS)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "status": "success" if result.returncode == 0 else "error",
        "exit_code": result.returncode,
        "stdout": clean_text(result.stdout),
        "stderr": clean_text(result.stderr),
    }


def search_clients(clients: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    query = clean_text(query)
    if not query:
        return []

    q_digits = digits_only(query)
    q_norm = normalize_text(query)
    q_row = int(query) if query.isdigit() else None
    matches: list[dict[str, Any]] = []

    for client in clients:
        score = score_client_match(client, q_row, q_digits, q_norm)
        if score <= 0:
            continue
        matches.append({"score": score, "record": client})

    matches.sort(
        key=lambda item: (
            -item["score"],
            item["record"]["name"],
            item["record"]["row"],
        )
    )
    return matches


def resolve_single_client(clients: list[dict[str, Any]], query: str) -> dict[str, Any]:
    matches = search_clients(clients, query)
    if not matches:
        return {
            "status": "not_found",
            "query": query,
            "message": "没有找到匹配客户。",
            "candidates": [],
        }
    if len(matches) > 1:
        return {
            "status": "ambiguous",
            "query": query,
            "message": "命中多个客户，请使用更精确的姓名、电话或行号。",
            "candidates": [client_brief(item["record"]) for item in matches[:10]],
        }
    return {"status": "success", "query": query, "client": matches[0]["record"]}


def search_properties(properties: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    query = clean_text(getattr(args, "query", None))
    query_norm = normalize_text(query)
    query_digits = digits_only(query)
    district_filter = normalize_text(getattr(args, "district", None))
    community_filter = normalize_text(getattr(args, "community", None))
    limit = getattr(args, "limit", None)

    matches: list[dict[str, Any]] = []
    for record in properties:
        if district_filter and district_filter not in normalize_text(record.get("district")):
            continue
        if community_filter and community_filter not in normalize_text(record.get("community")):
            continue
        if getattr(args, "rooms", None) is not None and record.get("rooms") != args.rooms:
            continue
        if getattr(args, "min_price", None) is not None and number_or_none(record.get("price_wan")) is not None:
            if float(record["price_wan"]) < float(args.min_price):
                continue
        if getattr(args, "max_price", None) is not None and number_or_none(record.get("price_wan")) is not None:
            if float(record["price_wan"]) > float(args.max_price):
                continue
        if getattr(args, "min_sqm", None) is not None and number_or_none(record.get("sqm")) is not None:
            if float(record["sqm"]) < float(args.min_sqm):
                continue
        if getattr(args, "max_sqm", None) is not None and number_or_none(record.get("sqm")) is not None:
            if float(record["sqm"]) > float(args.max_sqm):
                continue
        if getattr(args, "min_score", None) is not None and number_or_none(record.get("score")) is not None:
            if float(record["score"]) < float(args.min_score):
                continue

        score = score_property_match(record, query_norm, query_digits)
        if query and score <= 0:
            continue
        matches.append({"score": score, "record": record})

    matches.sort(
        key=lambda item: (
            -item["score"],
            -(item["record"].get("score") or 0),
            item["record"].get("price_wan") if item["record"].get("price_wan") is not None else 10**9,
            item["record"]["community"],
        )
    )
    return matches[:limit] if limit else matches


def parse_followup_date_from_content(content: str, default_date_str: str) -> date:
    """从跟进内容中智能识别正确的跟进日期"""
    from datetime import timedelta
    
    today = date.today()
    content_lower = clean_text(content).lower()
    
    # 识别"昨天"、"昨晚"、"昨天晚上"等
    if any(kw in content_lower for kw in ['昨天', '昨晚', '昨天晚上', '昨晚']) and '今天' not in content_lower:
        return today - timedelta(days=1)
    
    # 识别"前天"、"前天晚上"等
    if any(kw in content_lower for kw in ['前天', '前晚', '前天晚上']):
        return today - timedelta(days=2)
    
    # 识别"大前天"
    if '大前天' in content_lower:
        return today - timedelta(days=3)
    
    # 识别"今天"、"今晚"、"今天晚上"等
    if any(kw in content_lower for kw in ['今天', '今晚', '今天晚上', '今晚']):
        return today
    
    # 识别"刚才"、"刚刚"、"刚才谈的"等
    if any(kw in content_lower for kw in ['刚才', '刚刚', '刚才谈', '刚刚谈']):
        return today
    
    # 识别"上周"、"上个星期"
    if any(kw in content_lower for kw in ['上周', '上个星期', '上星期']):
        # 返回上周一
        days_since_monday = today.weekday()
        return today - timedelta(days=days_since_monday + 7)
    
    # 识别"这周"、"这个星期"、"本周"
    if any(kw in content_lower for kw in ['这周', '这个星期', '本周', '这星期']):
        # 返回本周一
        days_since_monday = today.weekday()
        return today - timedelta(days=days_since_monday)
    
    # 识别具体日期格式（如 2026-04-03、4 月 3 日等）
    import re
    # 匹配 YYYY-MM-DD 格式
    match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', content)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass
    
    # 匹配 MM 月 DD 日格式
    match = re.search(r'(\d{1,2}) 月 (\d{1,2}) 日?', content)
    if match:
        try:
            month, day = int(match.group(1)), int(match.group(2))
            year = today.year
            return date(year, month, day)
        except ValueError:
            pass
    
    # 识别"晚上"、"下午"、"上午"、"中午"等时间词（默认今天）
    if any(kw in content_lower for kw in ['晚上', '下午', '上午', '中午', '凌晨', '早上']):
        return today
    
    # 不根据"谈判"、"谈了"等词自动推断日期
    # 因为谈判可能是今天、昨天或更早，不能武断判断
    
    # 默认使用传入的日期
    return datetime.strptime(default_date_str, "%Y-%m-%d").date()


def write_followup_via_excel(*, row_number: int, content: str, date_str: str) -> dict[str, Any]:
    if pythoncom is None or DispatchEx is None or GetObject is None:
        raise RuntimeError("win32com 不可用，无法进行安全写入。")

    # 【新增】写入前先保存 Excel，再清理进程，避免文件被占用导致只读
    import subprocess
    import time
    print("写入前保存并关闭 Excel...", flush=True)
    try:
        # 先尝试保存所有打开的 Excel 文件
        existing_excel = None
        try:
            existing_excel = GetObject(Class="Excel.Application")
            saved_count = 0
            for wb in existing_excel.Workbooks:
                if not wb.Saved:
                    wb.Save()
                    saved_count += 1
            if saved_count > 0:
                print(f"已自动保存 {saved_count} 个 Excel 文件", flush=True)
            existing_excel.Quit()
            time.sleep(2)
        except:
            pass  # 如果 Excel 未运行，忽略
        finally:
            if existing_excel:
                try:
                    existing_excel.Quit()
                except:
                    pass
    except:
        pass
    
    # 强制杀掉残留的 Excel 进程
    subprocess.run(["taskkill", "/F", "/IM", "excel.exe"], capture_output=True)
    time.sleep(2)
    print("OK: Excel 已关闭", flush=True)

    # 智能识别日期：从内容中自动判断正确的跟进日期
    target_date = parse_followup_date_from_content(content, date_str)
    content = clean_text(content)
    if not content:
        raise ValueError("跟进内容为空。")

    pythoncom.CoInitialize()
    excel = None
    workbook = None
    created_app = False
    opened_here = False

    try:
        # 【修改】清理后直接启动新的 Excel 实例
        excel = DispatchEx("Excel.Application")
        created_app = True

        excel.DisplayAlerts = False
        workbook = excel.Workbooks.Open(
            Filename=str(WORKBOOK_PATH),
            UpdateLinks=0,
            ReadOnly=False,
            Password=WORKBOOK_PASSWORD,
        )
        opened_here = True

        ws = workbook.Worksheets(CLIENT_SHEET_INDEX)
        date_target = find_or_create_date_column(ws, target_date)
        target_col = date_target["column"]
        existing = clean_text(ws.Cells(row_number, target_col).Value)
        if target_col == FIRST_FOLLOWUP_COLUMN and looks_like_group(existing):
            raise RuntimeError("首个跟进列仍占用组别标记，拒绝覆盖，请改用更晚日期。")
        if existing and existing != content:
            content = f"{existing}\n{content}"
            action = "appended"
        elif existing == content:
            action = "unchanged"
        else:
            action = "written"
        ws.Cells(row_number, target_col).Value = content
        workbook.Save()

        # 【新增】写入完成后打开 Excel 并定位到写入位置
        excel.Visible = True
        ws.Activate()
        workbook.Activate()
        cell = ws.Cells(row_number, target_col)
        cell.Select()
        excel.ActiveWindow.ScrollRow = row_number
        excel.ActiveWindow.ScrollColumn = target_col
        print(f"已打开 Excel 并定位到第 {row_number} 行，第 {target_col} 列（日期 {target_date.isoformat()}）", flush=True)

        # 【修改】不关闭 Excel 和 workbook，保持打开状态让用户查看
        # 将 workbook 和 excel 设为 None，避免 finally 中关闭
        workbook = None
        excel = None

        return {
            "row": row_number,
            "column": target_col,
            "date": target_date.isoformat(),
            "content": content,
            "action": action,
            "created_new_date_column": date_target["created_new_date_column"],
        }
    finally:
        # 【修改】只有当 workbook/excel 不为 None 时才关闭
        if workbook is not None:
            try:
                workbook.Close(SaveChanges=False)
            except Exception:
                pass
        if excel is not None and created_app:
            try:
                excel.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def find_open_workbook(excel: Any, workbook_path: Path) -> Any:
    target = str(workbook_path).lower()
    try:
        for candidate in excel.Workbooks:
            try:
                if str(candidate.FullName).lower() == target:
                    return candidate
            except Exception:
                continue
    except (AttributeError, TypeError):
        # Workbooks 属性不可用时，返回 None 强制重新打开
        pass
    return None


def find_or_create_date_column(ws: Any, target_date: date) -> dict[str, Any]:
    last_col = ws.Cells(CLIENT_HEADER_ROW, ws.Columns.Count).End(XL_TO_LEFT).Column
    for col in range(FIRST_FOLLOWUP_COLUMN, last_col + 1):
        header_date = excel_date_to_iso(ws.Cells(CLIENT_HEADER_ROW, col).Value)
        if header_date == target_date.isoformat():
            return {"column": col, "created_new_date_column": False}

    new_col = last_col + 1
    # 计算星期几
    weekday_map = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期日",
    }
    weekday = weekday_map[target_date.weekday()]
    # 格式：2026-04-04 星期六
    header_text = f"{target_date.isoformat()} {weekday}"
    header_cell = ws.Cells(CLIENT_HEADER_ROW, new_col)
    # 【关键修复】写入日期序列号（整数），不写入时间
    # 单元格显示：2026-04-13 星期一（自定义格式）
    # 编辑栏显示：2026/4/13（不带时间）
    # Excel 日期序列号：从 1899-12-30 开始的天数
    from datetime import datetime
    base_date = datetime(1899, 12, 30)
    target_dt = datetime(target_date.year, target_date.month, target_date.day)
    days_since_base = (target_dt - base_date).days
    header_cell.Value = days_since_base  # 写入整数（日期序列号）
    header_cell.NumberFormat = "yyyy-mm-dd aaaa"  # 单元格自定义格式
    return {"column": new_col, "created_new_date_column": True}


def preview_followup_target(date_str: str) -> dict[str, Any]:
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    import win32com.client
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = excel.Workbooks.Open(str(WORKBOOK_PATH), Password="000", ReadOnly=True)
    try:
        ws = wb.Worksheets(CLIENT_SHEET_INDEX)
        last_col = ws.UsedRange.Columns.Count
        for col in range(FIRST_FOLLOWUP_COLUMN, last_col + 1):
            header_val = ws.Cells(CLIENT_HEADER_ROW, col).Value
            header_date = excel_date_to_iso(header_val)
            if header_date == target_date.isoformat():
                return {
                    "date": target_date.isoformat(),
                    "column": col,
                    "created_new_date_column": False,
                }
        return {
            "date": target_date.isoformat(),
            "column": last_col + 1,
            "created_new_date_column": True,
        }
    finally:
        wb.Close()
        excel.Quit()


def update_client_fields_via_excel(row_number: int, updates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if pythoncom is None or DispatchEx is None or GetObject is None:
        raise RuntimeError("win32com 不可用，无法进行安全写入。")

    pythoncom.CoInitialize()
    excel = None
    workbook = None
    created_app = False
    opened_here = False

    try:
        try:
            excel = GetObject(Class="Excel.Application")
        except Exception:
            excel = DispatchEx("Excel.Application")
            created_app = True

        excel.DisplayAlerts = False
        workbook = find_open_workbook(excel, WORKBOOK_PATH)
        if workbook is None:
            workbook = excel.Workbooks.Open(
                Filename=str(WORKBOOK_PATH),
                UpdateLinks=0,
                ReadOnly=False,
                Password=WORKBOOK_PASSWORD,
            )
            opened_here = True

        ws = workbook.Worksheets(CLIENT_SHEET_INDEX)
        results: list[dict[str, Any]] = []
        for update in updates:
            column = update["column"]
            old_value = clean_text(ws.Cells(row_number, column).Value)
            new_value = build_updated_cell_value(old_value, update)
            ws.Cells(row_number, column).Value = new_value
            results.append(
                {
                    "field": update["field"],
                    "column": column,
                    "old_value": old_value,
                    "new_value": clean_text(new_value),
                }
            )

        workbook.Save()
        return results
    finally:
        if workbook is not None and opened_here:
            try:
                workbook.Close(SaveChanges=False)
            except Exception:
                pass
        if excel is not None and created_app:
            try:
                excel.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def preview_experience_excel_sync(entry: dict[str, Any]) -> dict[str, Any]:
    if entry.get("kind") == "technical":
        payload = build_technical_excel_payload(entry)
        return {
            "sheet": TECHNICAL_EXPERIENCE_SHEET_NAME,
            "row": preview_next_sheet_row(TECHNICAL_EXPERIENCE_SHEET_NAME),
            "columns": {
                "A": "next sequence",
                "B": date.today().isoformat(),
                "C": payload["scene"],
                "D": payload["t_label"],
                "E": payload["command"],
                "F": payload["notes"],
                "G": payload["success"],
            },
        }

    content = build_business_excel_content(entry)
    return {
        "sheet": BUSINESS_EXPERIENCE_SHEET_NAME,
        "row": preview_next_sheet_row(BUSINESS_EXPERIENCE_SHEET_NAME),
        "columns": {
            "A": "next sequence",
            "B": date.today().isoformat(),
            "C": content,
            "D": entry.get("tags", {}).get("state", ""),
            "E": entry.get("tags", {}).get("challenge", ""),
            "F": entry.get("tags", {}).get("signal", ""),
        },
    }


def sync_experience_entry_to_excel(entry: dict[str, Any]) -> dict[str, Any]:
    if pythoncom is None or DispatchEx is None or GetObject is None:
        return {"status": "error", "message": "win32com 不可用，无法写入经验表。"}

    pythoncom.CoInitialize()
    excel = None
    workbook = None
    created_app = False
    opened_here = False

    try:
        try:
            excel = GetObject(Class="Excel.Application")
        except Exception:
            excel = DispatchEx("Excel.Application")
            created_app = True

        excel.DisplayAlerts = False
        workbook = find_open_workbook(excel, WORKBOOK_PATH)
        if workbook is None:
            workbook = excel.Workbooks.Open(
                Filename=str(WORKBOOK_PATH),
                UpdateLinks=0,
                ReadOnly=False,
                Password=WORKBOOK_PASSWORD,
            )
            opened_here = True

        if entry.get("kind") == "technical":
            ws = get_named_sheet(workbook, TECHNICAL_EXPERIENCE_SHEET_NAME)
            if ws is None:
                return {"status": "error", "message": f"未找到工作表 {TECHNICAL_EXPERIENCE_SHEET_NAME}。"}
            row_number = int(ws.UsedRange.Rows.Count) + 1
            payload = build_technical_excel_payload(entry)
            ws.Cells(row_number, 1).Value = row_number - 1
            ws.Cells(row_number, 2).Value = date.today().isoformat()
            ws.Cells(row_number, 3).Value = payload["scene"]
            ws.Cells(row_number, 4).Value = payload["t_label"]
            ws.Cells(row_number, 5).Value = payload["command"]
            ws.Cells(row_number, 6).Value = payload["notes"]
            ws.Cells(row_number, 7).Value = payload["success"]
            workbook.Save()
            return {"status": "success", "sheet": TECHNICAL_EXPERIENCE_SHEET_NAME, "row": row_number}

        ws = get_named_sheet(workbook, BUSINESS_EXPERIENCE_SHEET_NAME)
        if ws is None:
            return {"status": "error", "message": f"未找到工作表 {BUSINESS_EXPERIENCE_SHEET_NAME}。"}
        row_number = int(ws.UsedRange.Rows.Count) + 1
        ws.Cells(row_number, 1).Value = row_number - 1
        ws.Cells(row_number, 2).Value = date.today().isoformat()
        ws.Cells(row_number, 3).Value = build_business_excel_content(entry)
        ws.Cells(row_number, 4).Value = entry.get("tags", {}).get("state", "")
        ws.Cells(row_number, 5).Value = entry.get("tags", {}).get("challenge", "")
        ws.Cells(row_number, 6).Value = entry.get("tags", {}).get("signal", "")
        workbook.Save()
        return {"status": "success", "sheet": BUSINESS_EXPERIENCE_SHEET_NAME, "row": row_number}
    except Exception as exc:
        return {"status": "error", "message": f"写入经验表失败：{exc}"}
    finally:
        if workbook is not None and opened_here:
            try:
                workbook.Close(SaveChanges=False)
            except Exception:
                pass
        if excel is not None and created_app:
            try:
                excel.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def get_named_sheet(workbook: Any, sheet_name: str) -> Any:
    for sheet in workbook.Worksheets:
        try:
            if str(sheet.Name) == sheet_name:
                return sheet
        except Exception:
            continue
    return None


def preview_next_sheet_row(sheet_name: str) -> int | None:
    import win32com.client
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = excel.Workbooks.Open(str(WORKBOOK_PATH), Password="000", ReadOnly=True)
    try:
        if sheet_name not in [ws.Name for ws in wb.Worksheets]:
            return None
        ws = wb.Worksheets(sheet_name)
        return ws.UsedRange.Rows.Count + 1
    finally:
        wb.Close()
        excel.Quit()


def build_updated_cell_value(old_value: str, update: dict[str, Any]) -> Any:
    mode = update.get("mode", "replace")
    if mode == "append":
        appended = clean_text(update["value"])
        if not old_value:
            return prepare_excel_value(update["field"], appended)
        if appended and appended in old_value:
            return prepare_excel_value(update["field"], old_value)
        return prepare_excel_value(update["field"], f"{old_value}\n{appended}")
    return prepare_excel_value(update["field"], update["value"])


def parse_client_updates(items: list[str], client: dict[str, Any]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for item in items:
        if "=" not in item:
            raise ValueError(f"字段更新格式错误：{item}")
        raw_field, raw_value = item.split("=", 1)
        field = canonicalize_client_field(raw_field)
        if field is None:
            raise ValueError(f"不支持更新字段：{raw_field}")
        column = CLIENT_FIELD_COLUMNS[field]
        current_value = client.get(client_field_to_cache_key(field), "")
        updates.append(
            {
                "field": field,
                "column": column,
                "old_value": current_value,
                "value": clean_text(raw_value),
                "mode": "replace",
            }
        )
    return updates


def canonicalize_client_field(field: str) -> str | None:
    key = normalize_text(field)
    for candidate in CLIENT_FIELD_COLUMNS:
        if normalize_text(candidate) == key:
            return candidate
    for candidate, aliases in CLIENT_FIELD_ALIASES.items():
        if any(normalize_text(alias) == key for alias in aliases):
            return candidate
    return None


def client_field_to_cache_key(field: str) -> str:
    aliases = {
        "summary": "client_summary",
        "analysis": "client_summary",
        "status": "decode",
        "decision": "decision_speed",
        "info": "info_style",
        "interact": "interaction_style",
        "idea": "ideal_phrase",
        "areas": "notes",
    }
    return aliases.get(field, field)


def prepare_excel_value(field: str, value: str) -> Any:
    if field in {"budget"}:
        number = maybe_number(value)
        if isinstance(number, (int, float)):
            return number
    if field in {"rooms"}:
        room = room_token_to_int(clean_text(value).replace("房", ""))
        if room is not None:
            return room
    return value


def analyze_followup_content(client: dict[str, Any], content: str, properties: list[dict[str, Any]]) -> dict[str, Any]:
    property_map = {record["house_id"]: record for record in properties if record.get("house_id")}
    mentioned_house_ids = extract_house_ids(content)
    previous_house_ids = set(client.get("recommended_house_ids", []))
    mentioned_properties = [property_map[house_id] for house_id in mentioned_house_ids if house_id in property_map]

    suggestions: list[dict[str, Any]] = []
    current_budget = number_or_none(client.get("budget"))
    explicit_budget = extract_budget_signal(content)
    property_budget = infer_budget_from_properties(mentioned_properties, current_budget)
    suggested_budget = explicit_budget or property_budget
    if suggested_budget is not None and current_budget is not None and abs(suggested_budget - current_budget) >= 50:
        suggestions.append(
            {
                "field": "budget",
                "current_value": current_budget,
                "suggested_value": suggested_budget,
                "reason": build_budget_reason(content, mentioned_properties, current_budget, suggested_budget),
            }
        )

    suggested_rooms = infer_room_signal(content, mentioned_properties)
    current_rooms = parse_room_count(str(client.get("rooms", "")))
    if suggested_rooms is not None and current_rooms is not None and suggested_rooms != current_rooms:
        suggestions.append(
            {
                "field": "rooms",
                "current_value": current_rooms,
                "suggested_value": suggested_rooms,
                "reason": "本次跟进中出现了与当前客户户型记录不一致的偏好信号，建议确认是否需要改房型。",
            }
        )

    return {
        "mentioned_house_ids": mentioned_house_ids,
        "already_recommended_ids": [house_id for house_id in mentioned_house_ids if house_id in previous_house_ids],
        "new_house_ids": [house_id for house_id in mentioned_house_ids if house_id not in previous_house_ids],
        "mentioned_properties": [property_brief(record) for record in mentioned_properties],
        "update_suggestions": suggestions,
    }


def analyze_client_triage(client: dict[str, Any]) -> dict[str, Any]:
    score = 0
    reasons: list[str] = []
    grade = clean_text(client.get("grade")).upper()
    grade_scores = {"A": 36, "B": 28, "C": 18, "D": 10, "E": 4}
    score += grade_scores.get(grade, 0)
    if grade in grade_scores:
        reasons.append(f"{grade} 级客户基础优先级更高")

    days_since = days_since_iso(client.get("last_followup_date"))
    if days_since is None:
        score += 30
        reasons.append("还没有历史跟进记录")
    else:
        if days_since >= 30:
            score += 40
            reasons.append(f"距离上次跟进已 {days_since} 天")
        elif days_since >= 14:
            score += 28
            reasons.append(f"距离上次跟进已 {days_since} 天")
        elif days_since >= 7:
            score += 16
            reasons.append(f"距离上次跟进已 {days_since} 天")
        elif days_since <= 2:
            score -= 12
            reasons.append(f"最近 {days_since} 天刚跟进过")

    decode = clean_text(client.get("decode"))
    if decode in {"迷", "解"}:
        score += 8
        reasons.append(f"当前客户状态为“{decode}”")

    recent_signal = recent_followup_signal(client.get("followups", []), days_since)
    score += recent_signal["score"]
    reasons.extend(recent_signal["reasons"])

    # 趁热判定：2 天内有互动信号
    is_re_hot = recent_signal["score"] > 0 and days_since is not None and days_since <= 2
    if is_re_hot:
        reasons.append("趁热客户（2 天内有互动）")

    # 防遗忘保底判定
    is_forget_protection = False
    forget_threshold = {"B": 7, "C": 14, "D": 14, "E": 14}.get(grade, 999)
    if days_since is not None and days_since > forget_threshold:
        is_forget_protection = True
        reasons.append(f"防遗忘保底（{grade}级>{forget_threshold}天未跟）")

    # A 级每天必跟，或趁热，或防遗忘保底 → 强制进入 follow_now
    bucket = "follow_now"
    if grade == "A":
        bucket = "follow_now"  # A 级每天必跟
    elif is_re_hot or is_forget_protection:
        bucket = "follow_now"  # 趁热或保底
    elif score < 35:
        bucket = "low_signal"
    elif score < 55:
        bucket = "can_wait"

    return {
        "score": score,
        "bucket": bucket,
        "days_since_last_followup": days_since,
        "reasons": reasons[:6],
        "is_re_hot": is_re_hot,
        "is_forget_protection": is_forget_protection,
    }


def recent_followup_signal(followups: list[dict[str, Any]], days_since_last_followup: int | None) -> dict[str, Any]:
    if not followups:
        return {"score": 0, "reasons": []}
    if days_since_last_followup is not None and days_since_last_followup > 45:
        return {"score": 0, "reasons": []}

    recent = followups[-3:]
    score = 0
    reasons: list[str] = []
    text = "\n".join(item.get("content", "") for item in recent)

    if any(keyword in text for keyword in ["有回复", "回复", "愿意", "可以约", "约", "主动联系"]):
        score += 12
        reasons.append("最近跟进里有回复或互动信号")
    if any(keyword in text for keyword in ["有带看", "带看", "看房", "面谈"]):
        score += 12
        reasons.append("最近已有带看或看房动作")
    if any(keyword in text for keyword in ["没回复", "未回复", "不回复", "拉黑", "不考虑"]):
        score -= 8
        reasons.append("最近跟进里出现弱互动或负反馈")

    return {"score": score, "reasons": reasons}


def triage_brief(item: dict[str, Any]) -> dict[str, Any]:
    client = item["client"]
    triage = item["triage"]
    return {
        "row": client.get("row"),
        "name": client.get("name"),
        "phone": client.get("phone"),
        "grade": client.get("grade"),
        "budget": client.get("budget"),
        "district": client.get("district"),
        "last_followup_date": client.get("last_followup_date"),
        "score": triage.get("score"),
        "days_since_last_followup": triage.get("days_since_last_followup"),
        "reasons": triage.get("reasons"),
    }


def daily_brief_item(item: dict[str, Any]) -> dict[str, Any]:
    client = item["client"]
    triage = item["triage"]
    latest = latest_followup_entry(client)
    return {
        "row": client.get("row"),
        "name": client.get("name"),
        "phone": client.get("phone"),
        "grade": client.get("grade"),
        "budget": client.get("budget"),
        "district": client.get("district"),
        "score": triage.get("score"),
        "why_selected": triage.get("reasons", []),
        "client_snapshot": {
            "summary": excerpt_text(client.get("client_summary"), 120),
            "need": excerpt_text(client.get("need"), 80),
            "pain": excerpt_text(client.get("pain"), 80),
            "notes": excerpt_text(client.get("notes"), 100),
        },
        "last_followup": {
            "date": latest.get("date"),
            "content": excerpt_text(latest.get("content"), 120),
        },
        "followup_suggestion": suggest_followup_action(client, triage, latest),
    }


def latest_followup_entry(client: dict[str, Any]) -> dict[str, Any]:
    followups = client.get("followups", [])
    return followups[-1] if followups else {}


def excerpt_text(text: Any, limit: int) -> str:
    cleaned = clean_text(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."


def suggest_followup_action(client: dict[str, Any], triage: dict[str, Any], latest: dict[str, Any]) -> dict[str, str]:
    """根据客户具体情况生成个性化跟进建议。"""
    days_since = triage.get("days_since_last_followup")
    grade = clean_text(client.get("grade")).upper()
    
    # 获取客户具体情况
    client_summary = clean_text(client.get("client_summary", ""))
    need = clean_text(client.get("need", ""))
    pain = clean_text(client.get("pain", ""))
    notes = clean_text(client.get("notes", ""))
    
    # 获取最近 3 次跟进内容
    followups = client.get("followups", [])
    recent_followups = followups[-3:] if len(followups) >= 3 else followups
    recent_text = "\n".join(clean_text(fw.get("content", "")) for fw in recent_followups)
    latest_text = clean_text(latest.get("content", ""))
    
    # 分析客户状态
    is_sold = "已卖" in client_summary or "卖掉" in client_summary
    is_waiting = "观望" in client_summary or "缓缓" in client_summary or "不着急" in client_summary
    is_comparing = "比价" in client_summary or "对比" in client_summary or "犹豫" in client_summary
    has_viewed = "带看" in recent_text or "看房" in recent_text
    has_price_concern = "贵了" in recent_text or "价格" in recent_text or "太贵" in recent_text
    has_family_concern = "老婆" in recent_text or "老公" in recent_text or "家人" in recent_text or "小孩" in recent_text
    has_layout_concern = "户型" in recent_text or "楼层" in recent_text or "朝向" in recent_text
    has_location_concern = "地段" in recent_text or "位置" in recent_text or "板块" in recent_text or "地铁" in recent_text
    
    # 从未跟进过
    if not latest_text or days_since is None:
        return {
            "goal": "首次联系，建立信任并补齐信息。",
            "suggestion": f"电话优先，确认客户是否仍在看房。重点了解：家庭结构（{need.split('，')[0] if '，' in need else need[:20]}）、真实预算（{client.get('budget', '?')}万）、工作区域、购房urgency。暂不推房源。",
        }
    
    # 有带看记录 → 重点问卡点
    if has_viewed:
        if has_price_concern:
            return {
                "goal": "解决价格卡点，确认预算边界。",
                "suggestion": f"上次带看后客户觉得价格贵了。先问心理价位上限，再确认是总价压力还是单价认知差异。如果预算确实不够，主动调整推荐区间；如果是认知问题，准备近期成交案例佐证。",
            }
        if has_family_concern:
            return {
                "goal": "推动家庭内部决策统一。",
                "suggestion": f"客户家人对上次带看有意见（{pain if pain else '具体原因待确认'}）。建议约面谈，邀请关键决策人一起看房，现场解答疑虑。单独发房源效果有限。",
            }
        if has_layout_concern:
            return {
                "goal": "精准匹配户型需求。",
                "suggestion": f"客户对户型/楼层有明确要求。先问清楚最在意的 3 个点（如采光、通透、安静），再筛选房源。不要泛泛推荐，避免消耗信任。",
            }
        return {
            "goal": "围绕上次带看后的卡点推进。",
            "suggestion": f"不要直接再发房源，先问上次看过后最犹豫的点是什么（价格/楼层/采光/家人意见/地段），再决定推哪一类房子。",
        }
    
    # 长期未跟进（>30 天）→ 激活
    if days_since is not None and days_since >= 30:
        if is_sold:
            return {
                "goal": "客户已卖房，资金到位，urgency 较高。",
                "suggestion": f"客户已卖掉房子，现在是有资金无房源状态。直接问：'您房子卖掉了，现在看房更方便了，最近有看到合适的吗？'优先推荐符合{need[:30]}的房源，urgency 较高。",
            }
        if is_waiting:
            return {
                "goal": "观望型客户，用市场动态激活。",
                "suggestion": f"客户之前说缓缓/不着急。用近期成交数据或新挂牌房源试探：'最近 XX 小区有新出房源，性价比不错，要不要看看？'回复再继续，不勉强。",
            }
        return {
            "goal": "重新激活沉默客户。",
            "suggestion": f"先用简短问候切入（'最近还在看房吗？'），确认需求是否变化（预算/区域/户型）。客户给出积极信号后再推匹配房源。",
        }
    
    # A 级客户 → 高频跟进
    if grade == "A":
        if is_comparing:
            return {
                "goal": "A 级比价客户，帮助决策。",
                "suggestion": f"A 级客户在对比多个房源。整理 2-3 套最优选项的对比表（价格/户型/楼层/优缺点），帮客户理清思路。主动问：'您最在意哪一点？我帮您重点筛选。'",
            }
        return {
            "goal": "A 级客户每天必跟，保持热度。",
            "suggestion": f"基于客户当前预算{client.get('budget', '?')}万、区域{client.get('district', '?')}和需求（{need[:30]}），准备 1-2 套精准房源。明确问出最大决策阻碍（价格/户型/家人意见/其他）。",
        }
    
    # B 级趁热（2 天内有互动）→ 趁热打铁
    if days_since is not None and days_since <= 2 and grade == "B":
        return {
            "goal": "趁热打铁，推动到下一步。",
            "suggestion": f"客户最近有互动信号。基于{need[:30]}准备 1-2 套房源，主动邀约看房：'这周 X 有空吗？我帮您安排看看。'不要只发链接。",
        }
    
    # B/C 级超期 → 防遗忘保底
    if days_since is not None and ((grade == "B" and days_since > 7) or (grade == "C" and days_since > 14)):
        return {
            "goal": "超期客户，低压力重启对话。",
            "suggestion": f"客户{days_since}天未跟进。用轻松话题开场：'最近 XX 小区有新出房源，感觉符合您的需求，要不要看看？'客户回复后再深入，避免一上来就推房源。",
        }
    
    # 有明确痛点 → 针对性解决
    if pain:
        if "停车" in pain:
            return {
                "goal": "解决停车痛点。",
                "suggestion": f"客户明确说停车是痛点。优先筛选带车位或停车方便的小区（如{notes.split('；')[0] if '；' in notes else '意向小区'}），推荐时强调车位情况。",
            }
        if "位置" in pain or "地段" in pain:
            return {
                "goal": "解决地段痛点。",
                "suggestion": f"客户对位置有顾虑。先问清楚地段要求的核心原因（上班通勤/孩子上学/生活便利），再针对性推荐。不要推荐偏远房源。",
            }
        if "总价" in pain:
            return {
                "goal": "解决预算痛点。",
                "suggestion": f"客户觉得总价超预算。问清楚上限是多少，再筛选。如果确实买不到匹配的，建议调整需求（房龄/面积/区域）。",
            }
    
    # 默认情况 → 基于需求推荐
    return {
        "goal": "延续最近沟通，推动决策。",
        "suggestion": f"客户关注{client.get('district', '该区域')}，预算{client.get('budget', '?')}万，需求{need[:20]}。准备 1-2 套匹配房源，主动问：'您最在意哪一点？我帮您重点筛选。'",
    }


def match_properties_for_client(
    *,
    client: dict[str, Any],
    properties: list[dict[str, Any]],
    limit: int,
    include_recommended: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    recommended_ids = set(client.get("recommended_house_ids", []))
    matches: list[dict[str, Any]] = []
    excluded: list[str] = []
    preferences = build_client_preferences_summary(client)

    for record in properties:
        house_id = record.get("house_id")
        if house_id and house_id in recommended_ids and not include_recommended:
            excluded.append(house_id)
            continue

        score, reasons = score_property_for_client(record, client, preferences)
        if score <= 0:
            continue
        matches.append(
            {
                "score": score,
                "reasons": reasons,
                "already_recommended": house_id in recommended_ids if house_id else False,
                "property": property_brief(record),
            }
        )

    matches.sort(
        key=lambda item: (
            -item["score"],
            -(item["property"].get("score") or 0),
            item["property"].get("price_wan") if item["property"].get("price_wan") is not None else 10**9,
        )
    )
    return matches[:limit], excluded


def recommend_properties_for_client(
    *,
    client: dict[str, Any],
    properties: list[dict[str, Any]],
    candidate_limit: int,
    final_limit: int,
    include_recommended: bool,
) -> dict[str, Any]:
    detail_cache = load_property_detail_cache()
    rough_matches, excluded = match_properties_for_client(
        client=client,
        properties=properties,
        limit=max(candidate_limit, final_limit),
        include_recommended=include_recommended,
    )

    reviewed: list[dict[str, Any]] = []
    for candidate in rough_matches:
        house_id = clean_text(candidate.get("property", {}).get("house_id"))
        detail_payload = fetch_property_detail_payload(house_id, detail_cache=detail_cache)
        reviewed.append(evaluate_property_recommendation(client, candidate, detail_payload))
    save_property_detail_cache(detail_cache)

    reviewed.sort(
        key=lambda item: (
            -item["final_score"],
            -item["rough_score"],
            item["property"].get("price_wan") if item["property"].get("price_wan") is not None else 10**9,
        )
    )

    final_recommendations = choose_final_recommendations(reviewed, final_limit)
    summary = build_recommendation_summary(client, rough_matches, reviewed, final_recommendations)
    return {
        "rough_candidates": rough_matches,
        "reviewed_candidates": reviewed,
        "final_recommendations": final_recommendations,
        "excluded_recommended": excluded,
        "summary": summary,
    }


def build_client_preferences_summary(client: dict[str, Any]) -> dict[str, Any]:
    return {
        "rooms": extract_room_preferences(client),
        "budget": number_or_none(client.get("budget")),
        "districts": extract_preference_tokens(client.get("district")),
        "notes_tokens": extract_preference_tokens(client.get("notes")),
    }


def score_property_for_client(record: dict[str, Any], client: dict[str, Any], preferences: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    budget = preferences.get("budget")
    if budget is not None and isinstance(record.get("price_wan"), (int, float)):
        price = float(record["price_wan"])
        if price <= budget:
            score += 28
            reasons.append("总价在客户当前预算内")
        elif price <= budget + 100:
            score += 16
            reasons.append("总价略高于预算，但仍在可讨论区间")
        elif price > budget + 200:
            score -= 25
            reasons.append("总价明显高于当前预算")

    preferred_rooms = preferences.get("rooms", [])
    property_rooms = record.get("rooms")
    if preferred_rooms and property_rooms is not None:
        if property_rooms in preferred_rooms:
            score += 22
            reasons.append(f"户型符合客户偏好（{property_rooms}房）")
        else:
            score -= 8
            reasons.append(f"户型与当前偏好不一致（房源 {property_rooms} 房）")

    preferred_districts = preferences.get("districts", [])
    district_text = normalize_text(record.get("district"))
    plate_text = normalize_text(record.get("plate"))
    community_text = normalize_text(record.get("community"))
    if preferred_districts:
        if any(token in district_text or token in plate_text for token in preferred_districts):
            score += 20
            reasons.append("区域或板块符合客户常看范围")
        else:
            score -= 6
            reasons.append("区域不在当前主要偏好里")

    notes_tokens = preferences.get("notes_tokens", [])
    if notes_tokens and any(token in community_text or token in plate_text for token in notes_tokens):
        score += 12
        reasons.append("备注里出现过相近小区或板块")

    if isinstance(record.get("score"), (int, float)):
        score += int(float(record["score"]))
        reasons.append("房源分较高")

    return score, reasons[:4]


def evaluate_property_recommendation(
    client: dict[str, Any], candidate: dict[str, Any], detail_payload: dict[str, Any]
) -> dict[str, Any]:
    property_info = candidate["property"]
    detail = extract_property_detail_block(detail_payload)
    detail_snapshot = build_property_detail_snapshot(property_info, detail)

    final_score = int(candidate["score"])
    detail_strengths: list[str] = []
    risks: list[str] = []
    detail_status = clean_text(detail_payload.get("status")) or "error"

    if detail_status != "success" or not detail:
        final_score -= 18
        risks.append("详情页抓取失败，今天不建议把这套房作为正式推荐。")
    else:
        bonus, penalty, detail_strengths, detail_risks = score_property_detail_fit(client, candidate, detail)
        final_score += bonus
        final_score -= penalty
        risks.extend(detail_risks)

    rough_reasons = dedupe_text_list(candidate.get("reasons", []))
    unique_detail_strengths = dedupe_text_list(detail_strengths)
    decision_reasons = dedupe_text_list(unique_detail_strengths + rough_reasons)
    unique_risks = dedupe_text_list(risks)

    return {
        "property": property_info,
        "already_recommended": candidate.get("already_recommended", False),
        "rough_score": int(candidate["score"]),
        "rough_reasons": rough_reasons,
        "final_score": max(0, final_score),
        "detail_status": detail_status,
        "detail_snapshot": detail_snapshot,
        "detail_strengths": unique_detail_strengths[:6],
        "strengths": decision_reasons[:6],
        "risks": unique_risks[:5],
    }


def choose_final_recommendations(reviewed: list[dict[str, Any]], final_limit: int) -> list[dict[str, Any]]:
    reliable = [item for item in reviewed if item.get("detail_status") == "success"]
    if not reliable:
        return []

    top_score = reliable[0]["final_score"]
    minimum_score = max(42, top_score - 18)
    selected = [item for item in reliable if item["final_score"] >= minimum_score][:final_limit]

    if not selected and top_score >= 42:
        selected = reliable[:1]

    final_items: list[dict[str, Any]] = []
    for index, item in enumerate(selected, start=1):
        recommendation_reasons = dedupe_text_list(item.get("detail_strengths", [])[:3] + item.get("rough_reasons", [])[:2])
        final_items.append(
            {
                "rank": index,
                "property": item["property"],
                "rough_score": item["rough_score"],
                "final_score": item["final_score"],
                "why_recommended": recommendation_reasons[:5],
                "risks": item["risks"][:4],
                "detail_snapshot": item["detail_snapshot"],
                "already_recommended": item.get("already_recommended", False),
            }
        )
    return final_items


def build_recommendation_summary(
    client: dict[str, Any],
    rough_matches: list[dict[str, Any]],
    reviewed: list[dict[str, Any]],
    final_recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    if final_recommendations:
        return {
            "client_name": client.get("name"),
            "rough_candidate_count": len(rough_matches),
            "reviewed_count": len(reviewed),
            "recommended_count": len(final_recommendations),
            "recommended_house_ids": [item["property"].get("house_id") for item in final_recommendations],
            "suggested_action": f"今天可以先联系 {client.get('name')}，优先发 {len(final_recommendations)} 套房，并围绕每套房的明确卖点展开沟通。",
        }
    return {
        "client_name": client.get("name"),
        "rough_candidate_count": len(rough_matches),
        "reviewed_count": len(reviewed),
        "recommended_count": 0,
        "recommended_house_ids": [],
        "suggested_action": f"今天可以先联系 {client.get('name')}，但先补信息或确认需求变化，暂时不要硬推房。",
    }


def extract_property_detail_block(detail_payload: dict[str, Any]) -> dict[str, Any]:
    result = detail_payload.get("detail_result")
    if not isinstance(result, dict):
        return {}
    detail = result.get("detail")
    return detail if isinstance(detail, dict) else {}


def build_property_detail_snapshot(property_info: dict[str, Any], detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "house_id": property_info.get("house_id"),
        "community": clean_text(detail.get("title")) or property_info.get("community"),
        "district": clean_text(detail.get("district")) or property_info.get("district"),
        "biz_circle": clean_text(detail.get("bizCircle")),
        "price": clean_text(detail.get("price")) or property_info.get("price_wan"),
        "unit_price": clean_text(detail.get("unitPrice")),
        "area": clean_text(detail.get("area")) or property_info.get("sqm"),
        "floor": clean_text(detail.get("floor")),
        "build_year": clean_text(detail.get("buildYear")),
        "building_type": clean_text(detail.get("buildingType")),
        "tags_excerpt": first_line_or_excerpt(clean_text(detail.get("tags")), 48),
        "follow_excerpt": first_line_or_excerpt(clean_text(detail.get("follow")), 48),
        "url": clean_text(detail.get("url")) or clean_text(detail.get("houseUrl")),
    }


def score_property_detail_fit(
    client: dict[str, Any], candidate: dict[str, Any], detail: dict[str, Any]
) -> tuple[int, int, list[str], list[str]]:
    bonus = 0
    penalty = 0
    strengths: list[str] = []
    risks: list[str] = []

    detail_text = build_detail_text(detail)
    floor_text = clean_text(detail.get("floor"))
    build_year = clean_text(detail.get("buildYear"))
    price_text = clean_text(detail.get("price"))
    unique_value = clean_text(detail.get("uniqueValue"))
    full_five = clean_text(detail.get("fullFive"))
    no_parking = clean_text(detail.get("noParking"))

    client_text = "\n".join(
        [
            clean_text(client.get("client_summary")),
            clean_text(client.get("need")),
            clean_text(client.get("pain")),
            clean_text(client.get("notes")),
            clean_text(client.get("district")),
            clean_text(client.get("rooms")),
        ]
    )

    if "唯一" in unique_value:
        bonus += 6
        strengths.append("详情页显示满五唯一，交易层面更省心。")
    if "满五" in full_five:
        bonus += 5
        strengths.append("详情页显示满五，税费条件更友好。")

    for keyword, reason in [
        ("采光", "详情里明确提到采光或视野，可以作为卖点。"),
        ("视野", "详情里有视野卖点，适合强调居住感受。"),
        ("品质", "小区品质感描述较强，适合改善型客户。"),
        ("得房率", "详情里提到得房率，适合强调空间使用效率。"),
        ("好谈", "详情里有价格好谈信号，便于推动客户继续聊。"),
        ("可谈", "房东端有可谈空间，利于后续推进。"),
        ("降价", "近期有降价或价格变化，可作为新的推荐理由。"),
        ("随时可看", "看房便利度较高，今天联系后容易推进到带看。"),
    ]:
        if keyword in detail_text:
            bonus += 4
            strengths.append(reason)

    if "车位" in client_text:
        if "无车位" in no_parking or "无车位" in detail_text:
            penalty += 12
            risks.append("客户可能在意车位，但这套房当前显示无车位。")
        elif clean_text(detail.get("parkingRatio")) or clean_text(detail.get("parkingFee")):
            bonus += 4
            strengths.append("详情页能看到停车相关信息，便于回应车位顾虑。")

    if "学区" in client_text and ("学校" in detail_text or "学区" in detail_text):
        bonus += 6
        strengths.append("详情页出现学校或学区信息，和客户关注点更贴近。")

    if "地铁" in client_text and "地铁" in detail_text:
        bonus += 5
        strengths.append("详情页出现地铁信息，通勤卖点更明确。")

    if ("高区" in client_text or "高楼层" in client_text) and floor_text.startswith("高"):
        bonus += 4
        strengths.append("楼层信息偏高区，和客户偏好更一致。")

    if "采光" in client_text and "采光" in detail_text:
        bonus += 5
        strengths.append("详情页再次验证了客户在意的采光点。")

    if any(token in client_text for token in ["次新", "新一点", "2000年后"]) and build_year.isdigit():
        if int(build_year) < 2000:
            penalty += 8
            risks.append(f"客户更偏向新一点的房子，但这套建成年代是 {build_year}。")

    budget = number_or_none(client.get("budget"))
    price = candidate.get("property", {}).get("price_wan")
    if budget is not None and isinstance(price, (int, float)):
        if float(price) > budget + 150:
            penalty += 10
            risks.append(f"当前总价 {price} 万，明显超出客户预算 {budget} 万。")
        elif float(price) <= budget:
            bonus += 4
            strengths.append(f"总价仍在客户预算 {budget} 万以内。")

    if candidate.get("already_recommended"):
        if any(token in detail_text for token in ["降价", "可谈", "底价"]):
            penalty += 6
            strengths.append("虽然历史上推过，但这次有新的价格或谈判理由。")
        else:
            penalty += 18
            risks.append("这套房历史上已经推荐过，且暂时没有明确新变化，二次推荐要谨慎。")

    if price_text and not clean_text(detail.get("floor")):
        risks.append("详情页关键信息不完整，推荐时要先核实楼层和条件。")

    return bonus, penalty, dedupe_text_list(strengths), dedupe_text_list(risks)


def build_detail_text(detail: dict[str, Any]) -> str:
    parts = [
        detail.get("title"),
        detail.get("district"),
        detail.get("bizCircle"),
        detail.get("floor"),
        detail.get("area"),
        detail.get("buildingType"),
        detail.get("buildYear"),
        detail.get("uniqueValue"),
        detail.get("fullFive"),
        detail.get("noParking"),
        detail.get("tags"),
        detail.get("follow"),
        detail.get("text"),
    ]
    return "\n".join(clean_text(part) for part in parts if clean_text(part))


def dedupe_text_list(items: list[str]) -> list[str]:
    unique: list[str] = []
    for item in items:
        cleaned = clean_text(item)
        if cleaned and cleaned not in unique:
            unique.append(cleaned)
    return unique


def build_budget_reason(
    content: str,
    mentioned_properties: list[dict[str, Any]],
    current_budget: float,
    suggested_budget: float,
) -> str:
    explicit_budget = extract_budget_signal(content)
    if explicit_budget is not None:
        return f"跟进内容里出现了更接近 {explicit_budget} 万的预算表达，当前基础信息还是 {current_budget} 万。"
    if mentioned_properties:
        prices = [record["price_wan"] for record in mentioned_properties if isinstance(record.get("price_wan"), (int, float))]
        if prices:
            return f"本次跟进涉及的房源价格集中在 {min(prices)}-{max(prices)} 万，明显高于当前预算 {current_budget} 万。"
    return f"本次跟进显示预算信号已偏离当前记录的 {current_budget} 万，建议复核。"


def extract_budget_signal(content: str) -> int | None:
    patterns = [
        r"(?:预算(?:提高到|提到|到|约|大概|变成)?|总价(?:到|约)?|只愿意出|能出到|出到|上调到|提到)\s*([1-9]\d{2,3})(?:\s*万)?",
        r"([1-9]\d{2,3})\s*万以内",
    ]
    values: list[int] = []
    for pattern in patterns:
        for match in re.findall(pattern, content):
            try:
                values.append(int(match))
            except ValueError:
                continue
    return max(values) if values else None


def infer_budget_from_properties(mentioned_properties: list[dict[str, Any]], current_budget: float | None) -> int | None:
    prices = sorted(
        int(record["price_wan"])
        for record in mentioned_properties
        if isinstance(record.get("price_wan"), (int, float))
    )
    if not prices or current_budget is None:
        return None
    if len(prices) >= 2 and min(prices) >= current_budget + 100:
        return max(prices)
    if len(prices) == 1 and prices[0] >= current_budget + 150:
        return prices[0]
    return None


def infer_room_signal(content: str, mentioned_properties: list[dict[str, Any]]) -> int | None:
    explicit_room_values = [
        room_token_to_int(match)
        for match in re.findall(r"([2-6一二三四五六])\s*房", content)
    ]
    explicit_room_values = [value for value in explicit_room_values if value is not None]
    if explicit_room_values:
        if all(value == explicit_room_values[0] for value in explicit_room_values):
            return explicit_room_values[0]
        return None

    property_room_values = [
        int(record["rooms"])
        for record in mentioned_properties
        if record.get("rooms") is not None
    ]
    if not property_room_values:
        return None
    if all(value == property_room_values[0] for value in property_room_values):
        return property_room_values[0]
    return None


def parse_client_update_instruction(client: dict[str, Any], instruction: str) -> dict[str, Any]:
    clauses = [clause.strip() for clause in re.split(r"[，,。；;]+", clean_text(instruction)) if clause.strip()]
    updates: list[dict[str, Any]] = []
    ignored_fields: list[str] = []
    unparsed: list[str] = []

    for clause in clauses:
        parsed = parse_instruction_clause(client, clause)
        if parsed is None:
            if clause not in {"需要", "不用", "不用了", "好的", "可以", "行", "是", "否", "不要"}:
                unparsed.append(clause)
            continue
        if parsed.get("ignore"):
            field = parsed["field"]
            if field not in ignored_fields:
                ignored_fields.append(field)
            continue
        updates.append(parsed)

    deduped_updates: list[dict[str, Any]] = []
    seen_fields: set[tuple[str, str]] = set()
    for update in updates:
        key = (update["field"], update.get("mode", "replace"))
        if key in seen_fields:
            deduped_updates = [item for item in deduped_updates if (item["field"], item.get("mode", "replace")) != key]
        seen_fields.add(key)
        deduped_updates.append(update)

    return {
        "updates": deduped_updates,
        "ignored_fields": ignored_fields,
        "unparsed_clauses": unparsed,
    }


def parse_instruction_clause(client: dict[str, Any], clause: str) -> dict[str, Any] | None:
    field = detect_field_from_clause(clause)
    if field is None:
        return None

    if contains_no_change(clause):
        return {"field": field, "ignore": True}

    if field == "budget":
        value = extract_budget_signal(clause)
        if value is None:
            value = maybe_number(extract_value_after_verb(clause))
        if value is None:
            return None
        return make_client_update_entry(client, field, str(int(value)))

    if field == "rooms":
        room = infer_room_signal(clause, [])
        if room is None:
            extracted = extract_value_after_verb(clause)
            room = room_token_to_int(clean_text(extracted).replace("房", "")) if extracted else None
        if room is None:
            return None
        return make_client_update_entry(client, field, str(room))

    if field in {"notes", "need", "pain", "client_summary"} and contains_append_verb(clause):
        value = extract_value_after_append_verb(clause)
        if not value:
            return None
        return make_client_update_entry(client, field, value, mode="append")

    value = extract_value_after_verb(clause)
    if not value:
        value = extract_value_after_field_alias(clause, field)
    if not value:
        return None
    return make_client_update_entry(client, field, value)


def make_client_update_entry(client: dict[str, Any], field: str, value: str, mode: str = "replace") -> dict[str, Any]:
    return {
        "field": field,
        "column": CLIENT_FIELD_COLUMNS[field],
        "old_value": client.get(client_field_to_cache_key(field), ""),
        "value": clean_text(value),
        "mode": mode,
    }


def detect_field_from_clause(clause: str) -> str | None:
    best_match: tuple[int, int, str] | None = None
    for field, aliases in CLIENT_FIELD_ALIASES.items():
        for alias in aliases:
            index = clause.find(alias)
            if index == -1:
                continue
            candidate = (index, -len(alias), field)
            if best_match is None or candidate < best_match:
                best_match = candidate
    return best_match[2] if best_match else None


def contains_no_change(clause: str) -> bool:
    return any(keyword in clause for keyword in ["不改", "不用改", "先不改", "先不动", "不动", "别动", "不用动"])


def contains_append_verb(clause: str) -> bool:
    return any(keyword in clause for keyword in ["补一句", "补充", "加一句", "加上", "追加"])


def extract_value_after_append_verb(clause: str) -> str:
    for keyword in ["补一句", "补充", "加一句", "加上", "追加"]:
        if keyword in clause:
            return clause.split(keyword, 1)[1].strip(" ：:，,")
    return ""


def extract_value_after_verb(clause: str) -> str:
    for keyword in ["改成", "改为", "改到", "更新为", "调整为", "调整到", "写成", "设为", "设成", "变成"]:
        if keyword in clause:
            return clause.split(keyword, 1)[1].strip(" ：:，,")
    if "是" in clause:
        head, tail = clause.split("是", 1)
        if detect_field_from_clause(head):
            return tail.strip(" ：:，,")
    return ""


def extract_value_after_field_alias(clause: str, field: str) -> str:
    for alias in CLIENT_FIELD_ALIASES.get(field, []):
        if alias in clause:
            remainder = clause.split(alias, 1)[1].strip(" ：:，,")
            if remainder:
                return remainder
    return ""


def room_token_to_int(token: str) -> int | None:
    mapping = {
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
    }
    token = clean_text(token)
    if not token:
        return None
    if token.isdigit():
        return int(token)
    return mapping.get(token)


def client_brief(client: dict[str, Any]) -> dict[str, Any]:
    return {
        "row": client.get("row"),
        "name": client.get("name"),
        "phone": client.get("phone"),
        "grade": client.get("grade"),
        "budget": client.get("budget"),
        "district": client.get("district"),
        "followup_count": client.get("followup_count"),
        "last_followup_date": client.get("last_followup_date"),
    }


def property_brief(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "row": record.get("row"),
        "house_id": record.get("house_id"),
        "district": record.get("district"),
        "plate": record.get("plate"),
        "community": record.get("community"),
        "layout": record.get("layout"),
        "sqm": record.get("sqm"),
        "price_wan": record.get("price_wan"),
        "score": record.get("score"),
        "maintainer": record.get("maintainer"),
    }


def client_without_followups(client: dict[str, Any]) -> dict[str, Any]:
    result = dict(client)
    result.pop("followups", None)
    result.pop("name_aliases", None)
    return result


def summarize_experience_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry.get("id"),
        "kind": entry.get("kind"),
        "status": entry.get("status"),
        "title": entry.get("title"),
        "scene": entry.get("scene"),
        "rule": entry.get("rule"),
        "action": entry.get("action"),
        "boundary": entry.get("boundary"),
        "validation": entry.get("validation"),
        "tags": entry.get("tags", {}),
        "source": entry.get("source", {}),
        "updated_at": entry.get("updated_at"),
    }


def first_line_or_excerpt(text: str, limit: int = 32) -> str:
    cleaned = clean_text(text)
    if not cleaned:
        return ""
    line = re.split(r"[\n。！？!?；;]", cleaned, maxsplit=1)[0].strip()
    return line[:limit].rstrip("，, ")


def extract_experience_keywords(text: str) -> list[str]:
    keywords: list[str] = []
    cleaned = clean_text(text)
    if not cleaned:
        return keywords
    for number in re.findall(r"\d{4,12}", cleaned):
        if number not in keywords:
            keywords.append(number)
    for chunk in re.split(r"[，,。；;：:\n]", cleaned):
        chunk = clean_text(chunk)
        if 2 <= len(chunk) <= 18 and chunk not in keywords:
            keywords.append(chunk)
    return keywords[:12]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("_x000D_", "\n").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def normalize_text(value: Any) -> str:
    text = clean_text(value).lower().replace("\u3000", " ")
    return re.sub(r"[\s,，。；;：:、/\\\-_|【】\[\]（）()]+", "", text)


def digits_only(value: Any) -> str:
    return "".join(re.findall(r"\d+", str(value or "")))


def maybe_number(value: Any) -> int | float | str | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else float(value)
    text = clean_text(value)
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return text
    return int(number) if number.is_integer() else number


def number_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def excel_date_to_iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)):
        if abs(float(value)) > 100000:
            return None
        try:
            base = datetime(1899, 12, 30)
            return (base + timedelta(days=float(value))).date().isoformat()
        except (ValueError, OverflowError, OSError):
            return None
    text = clean_text(value)
    if not text:
        return None
    # 尝试从字符串中提取日期部分（前 10 个字符）
    if len(text) >= 10:
        text = text[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_room_count(layout: str) -> int | None:
    match = re.match(r"(\d+)", clean_text(layout))
    return int(match.group(1)) if match else None


def extract_house_ids(value: Any) -> list[str]:
    ids = re.findall(r"\d{12}", str(value or ""))
    unique: list[str] = []
    seen: set[str] = set()
    for house_id in ids:
        if house_id not in seen:
            seen.add(house_id)
            unique.append(house_id)
    return unique


def extract_first_house_id(value: Any) -> str:
    ids = extract_house_ids(value)
    return ids[0] if ids else ""


def looks_like_group(value: str) -> bool:
    return bool(value and FOLLOWUP_GROUP_RE.fullmatch(value))


def parse_clients(ws: Any) -> list[dict[str, Any]]:
    clients: list[dict[str, Any]] = []
    
    # 支持 win32com 和 openpyxl 两种接口
    try:
        # 🚀 智能边界计算：基于实际内容，而非 Excel 的虚假格式范围
        # 使用 Range 批量读取，避免逐格扫描导致卡死
        
        # 1. 动态计算最大列：读取第 11 行表头，找到最后一个有表头的列
        raw_cols = min(ws.UsedRange.Columns.Count, 1000) # 上限 1000 列，防止无限大
        max_col = raw_cols
        
        try:
            # 批量读取表头 (一次 COM 调用)
            if raw_cols > 1:
                headers = ws.Range(ws.Cells(11, 1), ws.Cells(11, raw_cols)).Value
                if headers:
                    # headers 是 tuple: (val1, val2, ...)
                    if isinstance(headers, tuple):
                        # 从后往前扫描，找到最后一个非空列
                        found_col = False
                        # 至少扫描到 20 列 (FIRST_FOLLOWUP_COLUMN)
                        start_idx = len(headers) - 1
                        end_idx = 19 # index for col 20
                        
                        for i in range(start_idx, end_idx, -1):
                            if headers[i]:
                                max_col = i + 1 # 1-based index
                                found_col = True
                                break
                        if not found_col and raw_cols > 20:
                            max_col = 20 # 没找到动态列，收缩到 20
                    else:
                        max_col = 1
                else:
                    if raw_cols > 20: max_col = 20
            else:
                max_col = raw_cols
        except Exception:
            pass # 批量读取失败，维持原判 (可能稍慢但不会错)

        # 2. 动态计算最大行：读取第 9 列 (Name)，找到最后一个有名字的行
        raw_rows = min(ws.UsedRange.Rows.Count, 2000) # 上限 2000 行
        max_row = raw_rows
        
        if raw_rows >= CLIENT_START_ROW:
            try:
                names = ws.Range(ws.Cells(CLIENT_START_ROW, 9), ws.Cells(raw_rows, 9)).Value
                if names:
                    if isinstance(names, tuple):
                        # names 是 ((val,), (val,))
                        for r in range(len(names)-1, -1, -1):
                            if names[r][0]: # 检查名字
                                max_row = CLIENT_START_ROW + r
                                break
                        else:
                            max_row = CLIENT_START_ROW - 1 # 全空
                    else:
                        if not names: max_row = CLIENT_START_ROW - 1
                else:
                    max_row = CLIENT_START_ROW - 1
            except Exception:
                pass

        get_cell = lambda r, c: ws.Cells(r, c).Value
    except AttributeError:
        max_row = ws.max_row
        max_col = ws.max_column
        get_cell = lambda r, c: ws.cell(r, c).value
    
    for row in range(CLIENT_START_ROW, max_row + 1):
        name = clean_text(get_cell(row, 9))
        if not name:
            continue

        # 新增：扫描“建议”和“检查”列
        ai_checks = {}
        ai_suggestions = {}
        # 遍历所有可能的列（从 1 到 max_col）
        for c in range(1, max_col + 1):
            header_val = get_cell(CLIENT_HEADER_ROW, c)
            if not header_val:
                continue
            header_str = str(header_val).strip()
            # 匹配格式：包含日期（如 2024-05-20）和 关键字，或者 AI- 开头的列
            if "建议" in header_str or "检查" in header_str or header_str.startswith("AI-"):
                # 提取日期部分
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", header_str)
                if date_match:
                    date_str = date_match.group(1)
                    cell_val = clean_text(get_cell(row, c))
                    if cell_val:
                        if "建议" in header_str or header_str.startswith("AI-"):
                            ai_suggestions[date_str] = cell_val
                        elif "检查" in header_str:
                            ai_checks[date_str] = cell_val

        group = None
        first_followup_col = FIRST_FOLLOWUP_COLUMN
        first_followup_value = clean_text(get_cell(row, FIRST_FOLLOWUP_COLUMN))
        if looks_like_group(first_followup_value):
            group = first_followup_value
            first_followup_col += 1

        recommended_house_ids = extract_house_ids(get_cell(row, 5))
        # 只保留包含关键信息的跟进记录（过滤掉无价值的纯推房记录）
        VALUABLE_KEYWORDS = ("有带看", "有回复", "通电话", "解读")
        followups: list[dict[str, Any]] = []
        for col in range(first_followup_col, max_col + 1):
            # 跳过 AI 建议列（标题以 AI- 开头）
            header_val = get_cell(CLIENT_HEADER_ROW, col)
            if header_val and str(header_val).startswith("AI-"):
                continue
            followup_date = excel_date_to_iso(header_val)
            if not followup_date:
                continue
            content = clean_text(get_cell(row, col))
            if not content:
                continue
            if not any(kw in content for kw in VALUABLE_KEYWORDS):
                continue
            followups.append({"date": followup_date, "content": content, "column": col})

        clients.append(
            {
                "row": row,
                "name": name,
                "name_aliases": build_client_aliases(name),
                "phone": digits_only(get_cell(row, 11)),
                "grade": clean_text(get_cell(row, 6)),
                "rooms": clean_text(get_cell(row, 7)),
                "budget": maybe_number(get_cell(row, 8)),
                "district": clean_text(get_cell(row, 10)),
                "decode": clean_text(get_cell(row, 12)),
                "decision_speed": clean_text(get_cell(row, 13)),
                "info_style": clean_text(get_cell(row, 14)),
                "interaction_style": clean_text(get_cell(row, 15)),
                "need": clean_text(get_cell(row, 16)),
                "ideal_phrase": clean_text(get_cell(row, 17)),
                "pain": clean_text(get_cell(row, 18)),
                "notes": clean_text(get_cell(row, 19)),
                "group": group,
                "client_summary": clean_text(get_cell(row, 4)),
                "recommended_house_ids": recommended_house_ids,
                "recommended_house_count": len(recommended_house_ids),
                "followups": followups,
                "followup_count": len(followups),
                "last_followup_date": followups[-1]["date"] if followups else None,
                "ai_checks": ai_checks,
                "ai_suggestions": ai_suggestions,
            }
        )
    return clients


def parse_properties(ws: Any) -> list[dict[str, Any]]:
    properties: list[dict[str, Any]] = []
    
    # 支持 win32com 和 openpyxl 两种接口
    try:
        # 🚀 优化：限制行数/列数，防止卡死
        raw_max_row = ws.UsedRange.Rows.Count
        max_row = min(raw_max_row, 5000) # 房源表可能行数多一点
        raw_max_col = ws.UsedRange.Columns.Count
        max_col = min(raw_max_col, 200)
        get_cell = lambda r, c: ws.Cells(r, c).Value
    except AttributeError:
        raw_max_row = ws.max_row
        max_row = min(raw_max_row, 5000)
        raw_max_col = ws.max_column
        max_col = min(raw_max_col, 200)
        get_cell = lambda r, c: ws.cell(r, c).value
    
    for row in range(PROPERTY_START_ROW, max_row + 1):
        district = clean_text(get_cell(row, 1))
        block_code = clean_text(get_cell(row, 2))
        community_name, hyperlink_url = parse_hyperlink_formula(get_cell(row, 3))
        if not community_name:
            community_name = clean_text(get_cell(row, 3))
        layout = clean_text(get_cell(row, 4))
        sqm = maybe_number(get_cell(row, 5))
        price_wan = maybe_number(get_cell(row, 6))
        unit_price = maybe_number(get_cell(row, 7))
        floor = clean_text(get_cell(row, 8))
        score = maybe_number(get_cell(row, 9))
        list_date = clean_text(get_cell(row, 10))
        maintainer = clean_text(get_cell(row, 11))
        age = clean_text(get_cell(row, 12))
        house_id = clean_text(get_cell(row, 13)) or extract_first_house_id(block_code) or extract_first_house_id(hyperlink_url)
        detail_url = clean_text(get_cell(row, 14)) or hyperlink_url
        plate = clean_text(re.sub(r"\d{12}", "", block_code))

        if not any([district, block_code, community_name, house_id]):
            continue
        if community_name in {"小区", "community"} or layout in {"户型", "layout"}:
            continue

        properties.append(
            {
                "row": row,
                "house_id": house_id,
                "district": district,
                "plate": plate,
                "block_code": block_code,
                "community": community_name,
                "layout": layout,
                "rooms": parse_room_count(layout),
                "sqm": sqm,
                "price_wan": price_wan,
                "unit_price": unit_price,
                "floor": floor,
                "score": score,
                "list_date": list_date,
                "maintainer": maintainer,
                "age": age,
                "detail_url": detail_url,
            }
        )
    return properties


def parse_business_experiences(ws: Any) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    
    # 支持 win32com 和 openpyxl 两种接口
    try:
        max_row = ws.UsedRange.Rows.Count
        get_cell = lambda r, c: ws.Cells(r, c).Value
    except AttributeError:
        max_row = ws.max_row
        get_cell = lambda r, c: ws.cell(r, c).value
    
    for row in range(2, max_row + 1):
        content = clean_text(get_cell(row, 3))
        if not content:
            continue
        entry = {
            "id": f"excel-business-{row}",
            "kind": "business",
            "status": "approved",
            "created_at": excel_date_to_iso(get_cell(row, 2)) or "",
            "updated_at": excel_date_to_iso(get_cell(row, 2)) or "",
            "title": first_line_or_excerpt(content, 28),
            "scene": "",
            "problem": "",
            "rule": content,
            "action": "",
            "boundary": "",
            "validation": "",
            "keywords": extract_experience_keywords(content),
            "tags": {
                "state": clean_text(get_cell(row, 4)).upper(),
                "challenge": clean_text(get_cell(row, 5)).upper(),
                "signal": clean_text(get_cell(row, 6)).upper(),
                "technical": [],
            },
            "source": {
                "type": "excel",
                "sheet": BUSINESS_EXPERIENCE_SHEET_NAME,
                "row": row,
                "text": content,
            },
        }
        entry["signature"] = experience_signature(entry)
        entries.append(entry)
    return entries


def parse_technical_experiences(ws: Any) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    
    # 支持 win32com 和 openpyxl 两种接口
    try:
        max_row = ws.UsedRange.Rows.Count
        get_cell = lambda r, c: ws.Cells(r, c).Value
    except AttributeError:
        max_row = ws.max_row
        get_cell = lambda r, c: ws.cell(r, c).value
    
    for row in range(2, max_row + 1):
        scene = clean_text(get_cell(row, 3))
        command = clean_text(get_cell(row, 5))
        notes = clean_text(get_cell(row, 6))
        success = clean_text(get_cell(row, 7))
        if not any([scene, command, notes, success]):
            continue
        technical_tags = [token for token in re.findall(r"T\d+", clean_text(get_cell(row, 4)).upper())]
        entry = {
            "id": f"excel-technical-{row}",
            "kind": "technical",
            "status": "approved",
            "created_at": excel_date_to_iso(get_cell(row, 2)) or "",
            "updated_at": excel_date_to_iso(get_cell(row, 2)) or "",
            "title": scene or first_line_or_excerpt(notes or command, 28),
            "scene": scene,
            "problem": notes,
            "rule": notes,
            "action": command,
            "boundary": "",
            "validation": success,
            "keywords": extract_experience_keywords(" ".join(item for item in [scene, command, notes, success] if item)),
            "tags": {
                "state": "",
                "challenge": "",
                "signal": "",
                "technical": technical_tags,
            },
            "source": {
                "type": "excel",
                "sheet": TECHNICAL_EXPERIENCE_SHEET_NAME,
                "row": row,
                "text": "\n".join(item for item in [scene, command, notes, success] if item),
            },
        }
        entry["signature"] = experience_signature(entry)
        entries.append(entry)
    return entries


def build_client_aliases(name: str) -> list[str]:
    aliases = {name}
    trimmed = name.strip()
    for suffix in ("微信", "电话", "客户"):
        if trimmed.endswith(suffix):
            aliases.add(trimmed[: -len(suffix)].strip())
    aliases.add(re.sub(r"[（(].*?[）)]", "", trimmed).strip())
    return [alias for alias in aliases if alias]


def extract_room_preferences(client: dict[str, Any]) -> list[int]:
    values: list[int] = []
    for source in [client.get("rooms"), client.get("need"), client.get("notes")]:
        for match in re.findall(r"([2-6一二三四五六])\s*房", str(source or "")):
            room = room_token_to_int(match)
            if room is not None and room not in values:
                values.append(room)
    room_field = clean_text(client.get("rooms"))
    if room_field and not values:
        for token in re.findall(r"[2-6]", room_field):
            room = int(token)
            if room not in values:
                values.append(room)
    return values


def extract_preference_tokens(text: Any) -> list[str]:
    raw = clean_text(text)
    if not raw:
        return []
    tokens: list[str] = []
    for part in re.split(r"[，,；;、/\s]+", raw):
        token = normalize_text(part)
        if len(token) < 2:
            continue
        if token not in tokens:
            tokens.append(token)
    return tokens[:20]


def days_since_iso(value: Any) -> int | None:
    iso_value = clean_text(value)
    if not iso_value:
        return None
    try:
        target = datetime.strptime(iso_value, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (date.today() - target).days


def parse_hyperlink_formula(value: Any) -> tuple[str, str]:
    text = str(value or "").strip()
    if not text.startswith("=HYPERLINK("):
        return "", ""
    match = HYPERLINK_RE.match(text)
    if not match:
        return "", ""
    return match.group(2).strip(), match.group(1).strip()


def score_client_match(client: dict[str, Any], q_row: int | None, q_digits: str, q_norm: str) -> int:
    if q_row is not None and client["row"] == q_row:
        return 100

    phone = client.get("phone", "")
    aliases = client.get("name_aliases", [])
    alias_norms = [normalize_text(alias) for alias in aliases if alias]

    if q_digits and phone and q_digits == phone:
        return 96
    if q_norm and q_norm in alias_norms:
        return 94
    if q_digits and phone and len(q_digits) >= 4 and phone.endswith(q_digits):
        return 90
    if q_norm and any(q_norm in alias for alias in alias_norms):
        return 82
    if q_digits and phone and len(q_digits) >= 4 and q_digits in phone:
        return 80
    if q_norm and any(is_near_name_match(q_norm, alias) for alias in alias_norms):
        return 74
    if q_norm:
        best_ratio = max((SequenceMatcher(None, q_norm, alias).ratio() for alias in alias_norms), default=0)
        if best_ratio >= 0.82:
            return 70
    return 0


def is_near_name_match(query_norm: str, alias_norm: str) -> bool:
    if not query_norm or not alias_norm:
        return False
    if len(query_norm) != len(alias_norm):
        return False
    if len(query_norm) > 4:
        return False
    if query_norm[0] != alias_norm[0]:
        return False
    return levenshtein_distance(query_norm, alias_norm) == 1


def levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            insertions = previous[j] + 1
            deletions = current[j - 1] + 1
            substitutions = previous[j - 1] + (left_char != right_char)
            current.append(min(insertions, deletions, substitutions))
        previous = current
    return previous[-1]


def score_property_match(record: dict[str, Any], query_norm: str, query_digits: str) -> int:
    if not query_norm and not query_digits:
        return 1

    house_id = record.get("house_id", "")
    fields = [record.get("community", ""), record.get("district", ""), record.get("plate", ""), record.get("block_code", "")]
    haystack = normalize_text(" ".join(str(field or "") for field in fields))

    if query_digits and len(query_digits) == 12 and house_id == query_digits:
        return 100
    if query_norm and query_norm == normalize_text(record.get("community")):
        return 95
    if query_norm and query_norm == normalize_text(record.get("block_code")):
        return 92
    if query_norm and query_norm in haystack:
        return 84
    if query_digits and query_digits in normalize_text(record.get("block_code")):
        return 82
    return 0



def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
