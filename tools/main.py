#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""团团助手主入口 - 统一调度"""

import argparse
import json
import sys

# 导入各功能模块
from followup.write import cmd_write_followup
from followup.update import cmd_update_followup
from client.search import cmd_client_search
from client.search import cmd_client_context
from client.update import cmd_client_update
from client.update import cmd_client_update_from_text
from client.triage import cmd_client_triage
from client.daily_brief import cmd_client_daily_brief
from client.grade import cmd_client_grade_adjust
from property.search import cmd_property_search
from property.search import cmd_property_detail
from property.match import cmd_client_match_properties
from property.recommend import cmd_client_recommend_properties
from property.match_with_details import cmd_client_recommend_with_details
from experience.draft import cmd_experience_draft
from experience.draft import cmd_experience_draft_list
from experience.revise import cmd_experience_draft_revise
from experience.approve import cmd_experience_approve
from experience.query import cmd_experience_query
from core.doctor import cmd_doctor
from core.refresh import cmd_refresh
from core.guard import cmd_core_guard_status
from core.guard import cmd_core_guard_freeze


# 导入 hooks 模块
from core.hooks import run_pre_hook, run_post_hook


def main():
    parser = argparse.ArgumentParser(description="团团助手")
    subparsers = parser.add_subparsers(dest="command")
    
    # === 跟进相关 ===
    write_parser = subparsers.add_parser("write-followup", help="写入跟进记录")
    write_parser.add_argument("--query", required=True, help="客户查询")
    write_parser.add_argument("--date", required=True, help="日期")
    write_parser.add_argument("--content", required=True, help="内容")
    write_parser.add_argument("--dry-run", action="store_true", help="预览")
    write_parser.add_argument("--confirmed", action="store_true", help="用户已确认，允许执行破坏性操作")
    write_parser.set_defaults(handler=cmd_write_followup)
    
    update_parser = subparsers.add_parser("update-followup", help="更新跟进记录")
    update_parser.add_argument("--query", required=True, help="客户查询")
    update_parser.add_argument("--date", required=True, help="日期")
    update_parser.add_argument("--instruction", required=True, help="修改指令")
    update_parser.add_argument("--confirmed", action="store_true", help="用户已确认，允许执行破坏性操作")
    update_parser.set_defaults(handler=cmd_update_followup)
    
    # === 客户相关 ===
    search_parser = subparsers.add_parser("client-search", help="客户搜索")
    search_parser.add_argument("--query", required=True, help="查询")
    search_parser.set_defaults(handler=cmd_client_search)
    
    context_parser = subparsers.add_parser("client-context", help="客户详情")
    context_parser.add_argument("--query", required=True, help="查询")
    context_parser.set_defaults(handler=cmd_client_context)
    
    update_parser = subparsers.add_parser("client-update", help="客户更新")
    update_parser.add_argument("--query", required=True, help="查询")
    update_parser.add_argument("--set", action="append", help="设置字段 (key=value)")
    update_parser.add_argument("--dry-run", action="store_true", help="预览")
    update_parser.add_argument("--confirmed", action="store_true", help="用户已确认，允许执行破坏性操作")
    update_parser.set_defaults(handler=cmd_client_update)
    
    update_text_parser = subparsers.add_parser("client-update-from-text", help="客户更新从文本")
    update_text_parser.add_argument("--query", required=True, help="查询")
    update_text_parser.add_argument("--instruction", required=True, help="修改指令")
    update_text_parser.add_argument("--dry-run", action="store_true", help="预览")
    update_text_parser.add_argument("--confirmed", action="store_true", help="用户已确认，允许执行破坏性操作")
    update_text_parser.set_defaults(handler=cmd_client_update_from_text)
    
    triage_parser = subparsers.add_parser("client-triage", help="客户分诊")
    triage_parser.add_argument("--limit", type=int, default=10, help="数量限制")
    triage_parser.set_defaults(handler=cmd_client_triage)
    
    brief_parser = subparsers.add_parser("client-daily-brief", help="客户每日简报")
    brief_parser.add_argument("--limit", type=int, default=8, help="优先数量")
    brief_parser.add_argument("--wait-limit", type=int, default=10, help="可等待数量")
    brief_parser.set_defaults(handler=cmd_client_daily_brief)
    
    grade_parser = subparsers.add_parser("client-grade-adjust", help="客户分级调整")
    grade_parser.add_argument("--query", required=True, help="查询")
    grade_parser.add_argument("--new-grade", required=True, help="新等级")
    grade_parser.add_argument("--confirmed", action="store_true", help="用户已确认，允许执行破坏性操作")
    grade_parser.set_defaults(handler=cmd_client_grade_adjust)
    
    # === 房源相关 ===
    prop_search_parser = subparsers.add_parser("property-search", help="房源搜索")
    prop_search_parser.add_argument("--query", required=True, help="查询")
    prop_search_parser.set_defaults(handler=cmd_property_search)
    
    prop_detail_parser = subparsers.add_parser("property-detail", help="房源详情")
    prop_detail_parser.add_argument("--house-id", required=True, help="房源编号")
    prop_detail_parser.set_defaults(handler=cmd_property_detail)
    
    match_parser = subparsers.add_parser("client-match-properties", help="客户房源匹配")
    match_parser.add_argument("--query", required=True, help="客户查询")
    match_parser.add_argument("--limit", type=int, default=10, help="数量限制")
    match_parser.add_argument("--include-recommended", action="store_true", help="包含推荐")
    match_parser.add_argument("--weights", help="自定义权重 JSON，如 '{\"price\": 0.6, \"room\": 0.4}'")
    match_parser.set_defaults(handler=cmd_client_match_properties)
    
    recommend_parser = subparsers.add_parser("client-recommend-properties", help="客户房源推荐")
    recommend_parser.add_argument("--query", required=True, help="客户查询")
    recommend_parser.add_argument("--candidate-limit", type=int, default=5, help="粗筛数量")
    recommend_parser.add_argument("--final-limit", type=int, default=3, help="精选数量")
    recommend_parser.add_argument("--include-recommended", action="store_true", help="包含推荐")
    recommend_parser.add_argument("--weights", help="自定义权重 JSON")
    recommend_parser.set_defaults(handler=cmd_client_recommend_properties)
    
    detail_parser = subparsers.add_parser("client-recommend-with-details", help="客户房源精准推荐（含详情页+硬性要求排除）")
    detail_parser.add_argument("--query", required=True, help="客户查询")
    detail_parser.add_argument("--candidate-limit", type=int, default=10, help="粗筛候选数量")
    detail_parser.add_argument("--final-limit", type=int, default=5, help="最终推荐数量")
    detail_parser.add_argument("--weights", help="自定义权重 JSON")
    detail_parser.set_defaults(handler=cmd_client_recommend_with_details)
    
    # === 经验相关 ===
    draft_parser = subparsers.add_parser("experience-draft", help="经验草稿")
    draft_parser.add_argument("--text", required=True, help="内容")
    draft_parser.add_argument("--kind", help="类型")
    draft_parser.add_argument("--title", help="标题")
    draft_parser.add_argument("--tag", action="append", help="标签")
    draft_parser.set_defaults(handler=cmd_experience_draft)
    
    draft_list_parser = subparsers.add_parser("experience-draft-list", help="经验草稿列表")
    draft_list_parser.add_argument("--status", help="状态")
    draft_list_parser.add_argument("--kind", help="类型")
    draft_list_parser.add_argument("--limit", type=int, default=10, help="数量")
    draft_list_parser.set_defaults(handler=cmd_experience_draft_list)
    
    draft_revise_parser = subparsers.add_parser("experience-draft-revise", help="经验草稿修改")
    draft_revise_parser.add_argument("--draft-id", required=True, help="草稿 ID")
    draft_revise_parser.add_argument("--instruction", required=True, help="修改指令")
    draft_revise_parser.set_defaults(handler=cmd_experience_draft_revise)
    
    approve_parser = subparsers.add_parser("experience-approve", help="经验批准")
    approve_parser.add_argument("--draft-id", required=True, help="草稿 ID")
    approve_parser.add_argument("--review", help="审阅意见")
    approve_parser.add_argument("--confirmed", action="store_true", help="用户已确认，允许执行破坏性操作")
    approve_parser.set_defaults(handler=cmd_experience_approve)
    
    query_parser = subparsers.add_parser("experience-query", help="经验查询")
    query_parser.add_argument("--query", required=True, help="查询")
    query_parser.add_argument("--kind", help="类型")
    query_parser.add_argument("--limit", type=int, default=10, help="数量")
    query_parser.set_defaults(handler=cmd_experience_query)
    
    # === 核心相关 ===
    doctor_parser = subparsers.add_parser("doctor", help="健康检查")
    doctor_parser.set_defaults(handler=cmd_doctor)
    
    refresh_parser = subparsers.add_parser("refresh", help="刷新缓存")
    refresh_parser.add_argument("--sync-csv", action="store_true", help="同步 CSV")
    refresh_parser.set_defaults(handler=cmd_refresh)
    
    guard_status_parser = subparsers.add_parser("core-guard-status", help="核心保护状态")
    guard_status_parser.set_defaults(handler=cmd_core_guard_status)
    
    guard_freeze_parser = subparsers.add_parser("core-guard-freeze", help="核心保护冻结")
    guard_freeze_parser.set_defaults(handler=cmd_core_guard_freeze)
    
    args = parser.parse_args()
    
    if hasattr(args, 'handler'):
        command = getattr(args, 'command', 'unknown')
        
        # === PreToolUse Hook ===
        pre_result = run_pre_hook(command, args)
        if pre_result.get('denied'):
            print(json.dumps({
                "status": "hook_denied",
                "message": pre_result.get('message'),
                "command": command,
                "hint": "这是破坏性操作，需要用户确认后才能执行"
            }, ensure_ascii=False, indent=2))
            sys.exit(2)
        
        try:
            result, exit_code = args.handler(args)
            
            # === PostToolUse Hook ===
            result = run_post_hook(command, args, result)
            
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(exit_code)
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": str(e),
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
