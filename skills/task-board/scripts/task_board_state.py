#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
task_board_state.py - 任务看板状态保存/读取/清除（支持 TodoWrite 格式）

用法：
    python task_board_state.py save <目标> <步骤> <当前> <已完成> <风险> <下一步>
    python task_board_state.py save-todos <JSON文件路径>
    python task_board_state.py load
    python task_board_state.py clear
    python task_board_state.py status

状态文件位置：~/.openclaw/workspace/.task_board_state.json

TodoWrite 格式示例：
{
  "todos": [
    {"content": "读取客户表", "activeForm": "正在读取客户表", "status": "in_progress"},
    {"content": "匹配房源", "activeForm": "正在匹配房源", "status": "pending"}
  ]
}
"""

import json
import sys
import os
import io
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

STATE_FILE = Path.home() / ".openclaw" / "workspace" / ".task_board_state.json"

# 自动压缩配置（参照 claw-code compact_after_turns 模式）
# 针对小上下文窗口模型（如 MiniMax-M2.7 200K）优化
COMPACT_AFTER_TURNS = 6  # 超过6轮后自动压缩历史（原12→6，适配200K窗口）
MAX_HISTORY_ENTRIES = 6  # 压缩后保留最近N条历史（原12→6）

# Token 使用量检测（参照 claw-code estimate_session_tokens）
MAX_CONTEXT_TOKENS = 200000  # MiniMax-M2.7 上下文窗口
SYSTEM_PROMPT_TOKENS = 100000  # 系统提示词约100K tokens
COMPACT_TOKEN_THRESHOLD = 0.6  # 上下文使用率超60%时触发压缩

# 摘要存储文件（与 claw-code compact_session 一致：摘要独立存储）
SUMMARY_FILE = STATE_FILE.with_suffix(".summary.md")


def generate_auto_summary(history: list) -> str:
    """自动生成结构化摘要（参照 claw-code summarize_messages）"""
    if not history:
        return ""
    
    removed_count = len(history)
    completed = sum(1 for h in history if h.get("current") in ("已完成", "完成", "✅"))
    
    lines = [
        "<summary>",
        "任务看板历史压缩摘要:",
        f"- 压缩范围: {removed_count} 条历史记录",
        f"- 已完成步骤: {completed}/{removed_count}",
    ]
    
    # 提取最近的用户请求（参照 claw-code collect_recent_role_summaries）
    recent = history[-3:] if len(history) >= 3 else history
    if recent:
        lines.append("- 最近操作:")
        for h in recent:
            target = h.get("target", "")
            step = h.get("step", "")
            current = h.get("current", "")
            if target:
                lines.append(f"  - [{step}] {target} → {current}" if step else f"  - {target} → {current}")
    
    # 提取待办事项（参照 claw-code infer_pending_work）
    pending = [h for h in history if h.get("next_step") and h.get("current") not in ("已完成", "完成", "✅")]
    if pending:
        lines.append("- 待办事项:")
        for h in pending[-3:]:
            ns = h.get("next_step", "")
            if ns:
                lines.append(f"  - {ns}")
    
    # 提取关键文件（参照 claw-code collect_key_files）
    all_text = " ".join(
        str(h.get(k, "")) for h in history for k in ("target", "current", "completed", "next_step")
    )
    key_files = []
    for token in all_text.split():
        if any(token.endswith(ext) for ext in (".py", ".md", ".json", ".cmd", ".sh", ".txt")):
            key_files.append(token)
    if key_files:
        lines.append(f"- 关键文件: {', '.join(list(set(key_files))[:8])}")
    
    # 当前工作（参照 claw-code infer_current_work）
    last = history[-1]
    if last.get("current"):
        lines.append(f"- 当前工作: {last['current']}")
    
    lines.append("</summary>")
    return "\n".join(lines)


def estimate_token_usage(state: dict) -> dict:
    """估算当前上下文 token 使用量（参照 claw-code estimate_session_tokens）
    
    返回: {"total_tokens": int, "usage_percent": float, "should_compact": bool}
    """
    # 基础开销：系统提示词
    total_tokens = SYSTEM_PROMPT_TOKENS
    
    # SKILL.md 开销
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    if skill_path.exists():
        try:
            skill_content = skill_path.read_text(encoding="utf-8")
            # 粗略估算：1 token ≈ 1.5 字符
            total_tokens += len(skill_content) // 1.5
        except Exception:
            pass
    
    # 历史状态开销
    history = state.get("history", [])
    for h in history:
        for key in ("target", "step", "current", "completed", "risk", "next_step"):
            value = str(h.get(key, ""))
            total_tokens += len(value) // 1.5  # 粗略估算
    
    # 当前状态开销
    for key in ("target", "step", "current", "completed", "risk", "next_step"):
        value = str(state.get(key, ""))
        total_tokens += len(value) // 1.5
    
    # 摘要开销
    summary = state.get("compacted_summary", "")
    if summary:
        total_tokens += len(summary) // 1.5
    
    usage_percent = total_tokens / MAX_CONTEXT_TOKENS if MAX_CONTEXT_TOKENS > 0 else 0
    should_compact = usage_percent >= COMPACT_TOKEN_THRESHOLD
    
    return {
        "total_tokens": int(total_tokens),
        "usage_percent": round(usage_percent * 100, 1),
        "should_compact": should_compact,
        "max_tokens": MAX_CONTEXT_TOKENS,
    }


def compact_history_if_needed(state: dict, summary: str = None) -> dict:
    """自动压缩历史（参照 claw-code compact_session）
    
    与 claw-code 一致的行为:
    1. 超过阈值时触发压缩（按轮数 或 按token使用量）
    2. 生成结构化摘要（用户可提供或自动生成）
    3. 保留最近N条原文 + 摘要
    4. 摘要独立存储，支持二次压缩时合并
    """
    history = state.get("history", [])
    
    # 双阈值检测：轮数 或 token使用量
    token_info = estimate_token_usage(state)
    should_compact = (
        len(history) > COMPACT_AFTER_TURNS or 
        token_info["should_compact"]
    )
    
    if not should_compact:
        return state
    
    # 分离被压缩的历史和保留的历史
    keep_from = max(0, len(history) - MAX_HISTORY_ENTRIES)
    removed = history[:keep_from]
    preserved = history[keep_from:]
    
    # 生成或合并摘要（参照 claw-code merge_compact_summaries）
    existing_summary = state.get("compacted_summary", "")
    if summary:
        # 用户提供摘要，合并旧摘要
        if existing_summary:
            merged = f"{existing_summary}\n\n---\n\n{summary}"
        else:
            merged = summary
    else:
        # 自动生成摘要
        merged = generate_auto_summary(removed)
    
    # 保存摘要到独立文件（参照 claw-code 摘要独立存储）
    if merged:
        try:
            SUMMARY_FILE.write_text(merged, encoding="utf-8")
        except Exception:
            pass  # 摘要写入失败不影响主流程
    
    state["history"] = preserved
    state["compacted_summary"] = merged
    state["compacted_at"] = datetime.now().isoformat()
    state["removed_count"] = len(removed)
    
    return state


def save_state(target: str, step: str, current: str, completed: str, risk: str, next_step: str):
    """保存看板状态（向后兼容旧调用方式）"""
    # 读取现有状态，保留 history
    existing_history = []
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                old_state = json.load(f)
            existing_history = old_state.get("history", [])
        except (json.JSONDecodeError, KeyError):
            existing_history = []
    
    # 将旧状态推入历史
    if STATE_FILE.exists():
        existing_history.append({
            "target": target,
            "step": step,
            "current": current,
            "completed": completed,
            "risk": risk,
            "next_step": next_step,
            "timestamp": datetime.now().isoformat(),
        })
    
    state = {
        "target": target,
        "step": step,
        "current": current,
        "completed": completed,
        "risk": risk,
        "next_step": next_step,
        "timestamp": datetime.now().isoformat(),
        "session_id": os.environ.get("OPENCLAW_SESSION_ID", "unknown"),
        "todos": [],
        "history": existing_history,
    }
    
    # 自动压缩
    state = compact_history_if_needed(state)
    
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    
    return f"✅ 状态已保存: {STATE_FILE} (历史: {len(state['history'])}条)"

def save_todos(json_path: str):
    """从 JSON 文件保存 todos 结构化任务列表"""
    todos_file = Path(json_path)
    if not todos_file.exists():
        return f"❌ JSON 文件不存在: {json_path}"
    
    try:
        with open(todos_file, "r", encoding="utf-8") as f:
            todos_data = json.load(f)
        
        if "todos" not in todos_data:
            return "❌ JSON 文件缺少 todos 字段"
        
        # 读取现有状态或创建新状态
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        else:
            state = {
                "target": "",
                "step": "",
                "current": "",
                "completed": "",
                "risk": "",
                "next_step": "",
                "timestamp": datetime.now().isoformat(),
                "session_id": os.environ.get("OPENCLAW_SESSION_ID", "unknown")
            }
        
        state["todos"] = todos_data["todos"]
        state["timestamp"] = datetime.now().isoformat()
        
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        return f"✅ Todos 已保存: {len(state['todos'])} 个任务"
    
    except json.JSONDecodeError as e:
        return f"❌ JSON 解析失败: {e}"

def load_state():
    """读取看板状态"""
    if not STATE_FILE.exists():
        return "无历史看板状态"
    
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        timestamp = state.get("timestamp", "未知时间")
        target = state.get("target", "未知目标")
        step = state.get("step", "")
        current = state.get("current", "")
        completed = state.get("completed", "")
        risk = state.get("risk", "无")
        next_step = state.get("next_step", "")
        todos = state.get("todos", [])
        
        # 输出续接标记格式
        result = f"[← 会话续接 | 上次目标：{target} | {step} | 上一步：{current} | ⚠️阻塞：{risk}]"
        result += f"\n保存时间：{timestamp}"
        result += f"\n下一步：{next_step}"
        
        # 输出 todos 状态
        if todos:
            result += f"\n\n📋 任务列表 ({len(todos)} 个):"
            for i, todo in enumerate(todos, 1):
                status_icon = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅"
                }.get(todo.get("status", "pending"), "⏳")
                result += f"\n  {i}. {status_icon} {todo.get('content', '未知任务')}"
            
            # 检查是否全部完成
            all_completed = all(t.get("status") == "completed" for t in todos)
            if all_completed:
                result += "\n\n✅ 所有任务已完成，建议执行最终验证"
        
        return result
    except Exception as e:
        return f"读取状态失败：{e}"

def clear_state():
    """清除看板状态"""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
        return "✅ 状态已清除"
    return "无状态文件"

def status_check():
    """检查状态文件是否存在"""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        return json.dumps(state, ensure_ascii=False, indent=2)
    return "无状态文件"

def update_todo_status(todo_index: int, new_status: str):
    """更新单个 todo 的状态"""
    if not STATE_FILE.exists():
        return "❌ 无状态文件"
    
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        todos = state.get("todos", [])
        if not todos:
            return "❌ 无 todos 任务列表"
        
        if todo_index < 0 or todo_index >= len(todos):
            return f"❌ 索引超出范围: {todo_index} (有效范围: 0-{len(todos)-1})"
        
        valid_statuses = ["pending", "in_progress", "completed"]
        if new_status not in valid_statuses:
            return f"❌ 无效状态: {new_status} (有效值: {valid_statuses})"
        
        todos[todo_index]["status"] = new_status
        todos[todo_index]["activeForm"] = todos[todo_index].get("activeForm", todos[todo_index].get("content", ""))
        
        state["timestamp"] = datetime.now().isoformat()
        
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        return f"✅ 任务 {todo_index+1} 状态已更新为: {new_status}"
    
    except Exception as e:
        return f"❌ 更新失败: {e}"

def compact_command(summary: str = None):
    """手动触发压缩（支持用户提供摘要）"""
    if not STATE_FILE.exists():
        return "❌ 无状态文件"
    
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        before = len(state.get("history", []))
        state = compact_history_if_needed(state, summary)
        after = len(state.get("history", []))
        
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        summary_info = ""
        if state.get("compacted_summary"):
            summary_info = f" | 摘要: {len(state['compacted_summary'])}字符"
        
        return f"✅ 压缩完成: {before}条 → {after}条 (保留最近{MAX_HISTORY_ENTRIES}条){summary_info}"
    except Exception as e:
        return f"❌ 压缩失败: {e}"


def load_compacted_summary() -> str:
    """加载压缩摘要（供 load_state 调用）"""
    if SUMMARY_FILE.exists():
        try:
            return SUMMARY_FILE.read_text(encoding="utf-8")
        except Exception:
            pass
    
    # 回退：从状态文件读取
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            return state.get("compacted_summary", "")
        except Exception:
            pass
    
    return ""


def main():
    if len(sys.argv) < 2:
        print("用法：task_board_state.py <save|save-todos|load|clear|status|update-todo|compact|summary|tokens> [参数...]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "save":
        if len(sys.argv) < 8:
            print("用法：task_board_state.py save <目标> <步骤> <当前> <已完成> <风险> <下一步>")
            sys.exit(1)
        result = save_state(
            sys.argv[2], sys.argv[3], sys.argv[4],
            sys.argv[5], sys.argv[6], sys.argv[7]
        )
        print(result)
    
    elif command == "save-todos":
        if len(sys.argv) < 3:
            print("用法：task_board_state.py save-todos <JSON文件路径>")
            sys.exit(1)
        result = save_todos(sys.argv[2])
        print(result)
    
    elif command == "load":
        result = load_state()
        print(result)
    
    elif command == "clear":
        result = clear_state()
        print(result)
    
    elif command == "status":
        result = status_check()
        print(result)
    
    elif command == "update-todo":
        if len(sys.argv) < 4:
            print("用法：task_board_state.py update-todo <索引> <状态>")
            sys.exit(1)
        result = update_todo_status(int(sys.argv[2]), sys.argv[3])
        print(result)
    
    elif command == "compact":
        # 支持可选的摘要参数
        summary = sys.argv[2] if len(sys.argv) > 2 else None
        result = compact_command(summary)
        print(result)
    
    elif command == "summary":
        # 显示压缩摘要
        summary = load_compacted_summary()
        if summary:
            print(summary)
        else:
            print("无压缩摘要")
    
    elif command == "tokens":
        # 显示 token 使用量估算
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        else:
            state = {}
        
        token_info = estimate_token_usage(state)
        print(f"上下文窗口: {token_info['max_tokens']:,} tokens")
        print(f"当前使用: {token_info['total_tokens']:,} tokens ({token_info['usage_percent']}%)")
        print(f"剩余可用: {token_info['max_tokens'] - token_info['total_tokens']:,} tokens")
        if token_info['should_compact']:
            print("⚠️ 已超过压缩阈值，建议执行压缩")
        else:
            print("✅ 上下文使用正常")
    
    else:
        print(f"未知命令：{command}")
        sys.exit(1)

if __name__ == "__main__":
    main()