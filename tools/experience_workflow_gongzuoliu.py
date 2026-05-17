# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from difflib import SequenceMatcher
from datetime import datetime
from pathlib import Path
from typing import Any


BUSINESS_TAG_RULES = {
    "state": {
        "S1": ["刚接触", "第一次", "初次", "新客", "刚加", "刚认识"],
        "S2": ["初步接触", "了解中", "还在看", "随便看看", "不着急"],
        "S3": ["带看", "看房", "实地看", "约看", "陪看", "复看"],
        "S4": ["谈判", "谈价格", "出价", "议价", "签约", "成交"],
        "S5": ["跟进中", "持续跟进", "定期联系", "保持联系", "继续推进"],
        "S6": ["意向强烈", "想买", "准备买", "要定了", "确定要"],
        "S7": ["休眠", "暂停", "不买了", "放弃", "搁置", "冷却"],
    },
    "challenge": {
        "C1": ["无需求", "不需要", "不买房", "暂时不买", "没需求"],
        "C2": ["需求不清", "不知道", "不清楚", "没想好", "不确定"],
        "C3": ["不信任", "怀疑", "防备", "怕被忽悠", "怕骗", "不相信中介"],
        "C4": ["竞品对比", "别家", "其他中介", "对比", "比较"],
        "C5": ["决策困难", "犹豫", "纠结", "难决定", "拿不定"],
        "C6": ["信息验证", "查证", "核实", "确认", "验证"],
        "C7": ["信息不全", "不了解", "信息少", "资料缺"],
        "C8": ["预算", "钱", "资金", "贷款", "首付", "费用", "贵", "返价"],
        "C9": ["客户选择", "精力分配", "优先级", "放一放", "投入产出"],
    },
    "signal": {
        "B1": ["不回复", "不回消息", "不接电话", "拉黑", "拒接"],
        "B2": ["敷衍", "随便", "看看再说", "再想想", "考虑考虑"],
        "B3": ["消极", "冷淡", "没兴趣", "不积极", "被动"],
        "B4": ["从不回复", "没反应", "石沉大海"],
        "B5": ["浏览", "看了", "点击", "关注", "收藏"],
        "B6": ["低意愿", "不想买", "没意向", "意愿低"],
        "B8": ["防御", "防备心", "敏感", "谨慎", "小心"],
        "B9": ["信任建立", "信任", "认可", "放心", "靠谱"],
        "B10": ["竞争", "有人谈", "有人买", "抢手", "多人看"],
        "B13": ["带看", "复看", "二看"],
        "B14": ["感动", "感谢", "谢谢", "辛苦", "认可服务"],
        "B15": ["出价", "报价", "还价"],
        "B16": ["成交", "买了", "定了", "签约", "过户"],
    },
}

TECHNICAL_TAG_RULES = {
    "T1": ["读取", "查询", "获取", "打开", "加载", "导入"],
    "T2": ["写入", "更新", "修改", "保存", "添加", "删除"],
    "T3": ["excel", "表格", "csv", "xlsm", "xls"],
    "T4": ["超时", "卡住", "失败", "错误", "报错", "异常", "进程", "kill"],
    "T5": ["脚本", "代码", "程序", "运行", "执行", "python", "vbs", "cmd"],
    "T6": ["文件", "路径", "目录", "文件夹", "复制", "移动"],
}

TECHNICAL_KEYWORDS = [
    "脚本",
    "代码",
    "excel",
    "表格",
    "文件",
    "路径",
    "进程",
    "超时",
    "报错",
    "python",
    "vbs",
    "csv",
    "cmd",
]

EXPERIENCE_FIELD_ALIASES = {
    "title": ["标题", "题目"],
    "scene": ["场景", "场景描述"],
    "problem": ["问题", "误判", "错误点", "坑点"],
    "rule": ["规则", "结论", "原则", "判断", "经验结论"],
    "action": ["动作", "做法", "建议动作", "处理方式", "下一步", "解决方法", "建议"],
    "boundary": ["边界", "适用边界", "不适用边界", "例外", "注意事项", "提醒"],
    "validation": ["验证", "成功标志", "预期结果", "验收标准"],
    "keywords": ["关键词", "关键字"],
}

NO_CHANGE_KEYWORDS = ["不改", "不用改", "先不改", "先不动", "不动", "别动", "不用动"]
APPEND_KEYWORDS = ["补一句", "补充", "加一句", "加上", "追加"]
REPLACE_KEYWORDS = ["改成", "改为", "改到", "更新为", "调整为", "调整到", "写成", "设为", "设成", "变成"]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("_x000D_", "\n").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def normalize_text(value: Any) -> str:
    text = clean_text(value).lower().replace("\u3000", " ")
    return re.sub(r"[\s,，。；;:：、\\/_|\-\[\]【】()（）]+", "", text)


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def experience_root(workspace_root: Path) -> Path:
    return workspace_root / "memory" / "experience"


def experience_drafts_dir(workspace_root: Path) -> Path:
    return experience_root(workspace_root) / "drafts"


def experience_store_file(workspace_root: Path) -> Path:
    return experience_root(workspace_root) / "approved_store.json"


def ensure_experience_dirs(workspace_root: Path) -> dict[str, Path]:
    root = experience_root(workspace_root)
    drafts = experience_drafts_dir(workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    drafts.mkdir(parents=True, exist_ok=True)
    return {"root": root, "drafts": drafts, "store": experience_store_file(workspace_root)}


def infer_experience_kind(*, text: str, question: str = "", feedback: str = "", requested_kind: str = "auto") -> tuple[str, str]:
    requested_kind = clean_text(requested_kind).lower() or "auto"
    if requested_kind in {"business", "technical"}:
        return requested_kind, "kind was explicitly provided"

    haystack = normalize_text("\n".join(part for part in [question, feedback, text] if clean_text(part)))
    if any(keyword in haystack for keyword in [normalize_text(item) for item in TECHNICAL_KEYWORDS]):
        return "technical", "detected technical keywords in source text"
    return "business", "defaulted to business because no technical keywords were detected"


def infer_business_tags(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {"state": "", "challenge": "", "signal": "", "matches": {"state": [], "challenge": [], "signal": []}}
    lowered = clean_text(text).lower()
    for group_name, mapping in BUSINESS_TAG_RULES.items():
        for tag, keywords in mapping.items():
            matched = next((keyword for keyword in keywords if keyword.lower() in lowered), None)
            if matched is None:
                continue
            if not result[group_name]:
                result[group_name] = tag
            result["matches"][group_name].append({"tag": tag, "keyword": matched})
    return result


def infer_technical_tags(text: str) -> dict[str, Any]:
    lowered = clean_text(text).lower()
    tags: list[str] = []
    matches: list[dict[str, str]] = []
    for tag, keywords in TECHNICAL_TAG_RULES.items():
        matched = next((keyword for keyword in keywords if keyword.lower() in lowered), None)
        if matched is None:
            continue
        tags.append(tag)
        matches.append({"tag": tag, "keyword": matched})
    if not tags:
        tags = ["T6"]
        matches.append({"tag": "T6", "keyword": "fallback"})
    return {"technical": tags, "matches": matches}


def parse_tag_tokens(values: list[str] | None) -> list[str]:
    tokens: list[str] = []
    for raw in values or []:
        for token in re.findall(r"[SCBT]\d+", clean_text(raw).upper()):
            if token not in tokens:
                tokens.append(token)
    return tokens


def apply_tag_overrides(kind: str, tags: dict[str, Any], explicit_tokens: list[str]) -> dict[str, Any]:
    if not explicit_tokens:
        return tags

    updated = json.loads(json.dumps(tags, ensure_ascii=False))
    if kind == "business":
        for token in explicit_tokens:
            if token.startswith("S"):
                updated["state"] = token
            elif token.startswith("C"):
                updated["challenge"] = token
            elif token.startswith("B"):
                updated["signal"] = token
    else:
        technical = list(updated.get("technical", []))
        for token in explicit_tokens:
            if token.startswith("T") and token not in technical:
                technical.append(token)
        updated["technical"] = technical or updated.get("technical", [])
    return updated


def first_sentence(text: str, limit: int = 32) -> str:
    cleaned = clean_text(text)
    if not cleaned:
        return ""
    sentence = re.split(r"[。！？!?；;\n]", cleaned, maxsplit=1)[0].strip()
    return sentence[:limit].rstrip("，, ")


def unique_preserve_order(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = clean_text(item)
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def extract_keywords(text: str) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []
    keywords: list[str] = []
    for token in re.findall(r"\d{4,12}", cleaned):
        keywords.append(token)
    for token in re.findall(r"[A-Za-z][A-Za-z0-9._:/\\-]{1,30}", cleaned):
        keywords.append(token)
    for phrase in re.split(r"[，,。；;：:\n]", cleaned):
        phrase = clean_text(phrase)
        if 2 <= len(phrase) <= 18:
            keywords.append(phrase)
    return unique_preserve_order(keywords)[:12]


def derive_title(kind: str, text: str, question: str, feedback: str, tags: dict[str, Any]) -> str:
    seed = first_sentence(feedback or text or question, 28)
    if seed:
        return seed
    if kind == "technical":
        technical = "/".join(tags.get("technical", [])[:2])
        return f"技术经验 {technical}".strip()
    pieces = [tags.get("state"), tags.get("challenge"), tags.get("signal")]
    compact = " ".join(piece for piece in pieces if piece)
    return f"业务经验 {compact}".strip()


def derive_scene(kind: str, text: str, question: str) -> str:
    if question:
        return clean_text(question)
    return first_sentence(text, 60)


def extract_sentence_with_keywords(text: str, keywords: list[str]) -> str:
    for sentence in re.split(r"[。！？!?；;\n]", clean_text(text)):
        candidate = sentence.strip()
        if candidate and any(keyword in candidate for keyword in keywords):
            return candidate
    return ""


def derive_rule(text: str, feedback: str, kind: str) -> str:
    candidate = extract_sentence_with_keywords(text, ["必须", "不要", "应该", "先", "再", "不能", "改用", "只允许"])
    if candidate:
        return candidate
    if feedback:
        return clean_text(feedback)
    return first_sentence(text, 120)


def derive_action(text: str, kind: str) -> str:
    candidate = extract_sentence_with_keywords(text, ["先", "再", "改用", "调用", "停止", "确认", "写入", "查询", "返回", "刷新"])
    if candidate:
        return candidate
    return first_sentence(text, 120)


def derive_boundary(text: str) -> str:
    candidate = extract_sentence_with_keywords(text, ["如果", "只有", "除非", "否则", "谨慎", "不要", "不能", "例外"])
    if candidate:
        return candidate
    return ""


def derive_validation(text: str) -> str:
    candidate = extract_sentence_with_keywords(text, ["成功", "看到", "输出", "更新", "返回", "写入", "无报错"])
    return candidate


def new_draft_id(kind: str, text: str) -> str:
    digest = hashlib.sha1(clean_text(text).encode("utf-8")).hexdigest()[:6]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    prefix = "biz" if kind == "business" else "tech"
    return f"{prefix}-{stamp}-{digest}"


def build_experience_draft(
    *,
    text: str,
    question: str = "",
    feedback: str = "",
    requested_kind: str = "auto",
    title: str = "",
    explicit_tags: list[str] | None = None,
) -> dict[str, Any]:
    base_text = clean_text(text)
    if not base_text:
        raise ValueError("经验原文不能为空。")

    kind, kind_reason = infer_experience_kind(text=base_text, question=question, feedback=feedback, requested_kind=requested_kind)
    combined = "\n".join(part for part in [question, feedback, base_text] if clean_text(part))
    if kind == "technical":
        tags = infer_technical_tags(combined)
    else:
        tags = infer_business_tags(combined)
    tags = apply_tag_overrides(kind, tags, parse_tag_tokens(explicit_tags))

    draft = {
        "id": new_draft_id(kind, combined),
        "kind": kind,
        "status": "draft",
        "created_at": iso_now(),
        "updated_at": iso_now(),
        "title": clean_text(title) or derive_title(kind, base_text, question, feedback, tags),
        "scene": derive_scene(kind, base_text, question),
        "problem": clean_text(feedback) or first_sentence(base_text, 160),
        "rule": derive_rule(base_text, feedback, kind),
        "action": derive_action(base_text, kind),
        "boundary": derive_boundary(base_text),
        "validation": derive_validation(base_text) if kind == "technical" else "",
        "keywords": extract_keywords(combined),
        "tags": tags,
        "source": {
            "text": base_text,
            "question": clean_text(question),
            "feedback": clean_text(feedback),
            "mode": "natural_language",
        },
        "review": {
            "status": "pending_user_review",
            "checklist": [
                "确认标签是否准确",
                "确认规则是否值得长期复用",
                "确认动作是否足够具体",
                "确认边界是否需要补充",
            ],
        },
        "inference": {
            "kind_reason": kind_reason,
        },
    }
    draft["signature"] = experience_signature(draft)
    return draft


def draft_path(workspace_root: Path, draft_id: str) -> Path:
    return experience_drafts_dir(workspace_root) / f"{draft_id}.json"


def save_experience_draft(workspace_root: Path, draft: dict[str, Any]) -> Path:
    ensure_experience_dirs(workspace_root)
    draft["updated_at"] = iso_now()
    draft["signature"] = experience_signature(draft)
    path = draft_path(workspace_root, draft["id"])
    path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_experience_draft(workspace_root: Path, draft_id: str) -> dict[str, Any] | None:
    path = draft_path(workspace_root, draft_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def list_experience_drafts(workspace_root: Path, *, status: str | None = None, kind: str | None = None) -> list[dict[str, Any]]:
    ensure_experience_dirs(workspace_root)
    drafts: list[dict[str, Any]] = []
    for path in sorted(experience_drafts_dir(workspace_root).glob("*.json"), reverse=True):
        try:
            draft = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if status and clean_text(draft.get("status")).lower() != status.lower():
            continue
        if kind and clean_text(draft.get("kind")).lower() != kind.lower():
            continue
        drafts.append(draft)
    drafts.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return drafts


def load_experience_store(workspace_root: Path) -> dict[str, Any]:
    ensure_experience_dirs(workspace_root)
    path = experience_store_file(workspace_root)
    if not path.exists():
        return {"version": 1, "updated_at": "", "entries": []}
    try:
        store = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "updated_at": "", "entries": []}
    store.setdefault("version", 1)
    store.setdefault("updated_at", "")
    store.setdefault("entries", [])
    return store


def save_experience_store(workspace_root: Path, store: dict[str, Any]) -> Path:
    ensure_experience_dirs(workspace_root)
    store["updated_at"] = iso_now()
    path = experience_store_file(workspace_root)
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_approved_entry(draft: dict[str, Any], review_note: str = "") -> dict[str, Any]:
    entry = json.loads(json.dumps(draft, ensure_ascii=False))
    entry["status"] = "approved"
    entry.setdefault("review", {})
    entry["review"].update(
        {
            "status": "approved",
            "approved_at": iso_now(),
            "review_note": clean_text(review_note),
            "approved_by": "user",
        }
    )
    entry["updated_at"] = iso_now()
    entry["signature"] = experience_signature(entry)
    return entry


def upsert_approved_entry(workspace_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    store = load_experience_store(workspace_root)
    entries = store.get("entries", [])
    replaced = False
    for index, current in enumerate(entries):
        if current.get("id") == entry.get("id"):
            entries[index] = entry
            replaced = True
            break
    if not replaced:
        entries.append(entry)
    store["entries"] = entries
    save_experience_store(workspace_root, store)
    return store


def summarize_draft(draft: dict[str, Any]) -> dict[str, Any]:
    tags = draft.get("tags", {})
    return {
        "id": draft.get("id"),
        "kind": draft.get("kind"),
        "status": draft.get("status"),
        "title": draft.get("title"),
        "updated_at": draft.get("updated_at"),
        "scene": draft.get("scene"),
        "tags": {
            "state": tags.get("state", ""),
            "challenge": tags.get("challenge", ""),
            "signal": tags.get("signal", ""),
            "technical": tags.get("technical", []),
        },
    }


def detect_field_from_clause(clause: str) -> str | None:
    best_match: tuple[int, int, str] | None = None
    for field, aliases in EXPERIENCE_FIELD_ALIASES.items():
        for alias in aliases:
            index = clause.find(alias)
            if index == -1:
                continue
            candidate = (index, -len(alias), field)
            if best_match is None or candidate < best_match:
                best_match = candidate
    return best_match[2] if best_match else None


def contains_no_change(clause: str) -> bool:
    return any(keyword in clause for keyword in NO_CHANGE_KEYWORDS)


def contains_append_verb(clause: str) -> bool:
    return any(keyword in clause for keyword in APPEND_KEYWORDS)


def extract_value_after_append_verb(clause: str) -> str:
    for keyword in APPEND_KEYWORDS:
        if keyword in clause:
            return clause.split(keyword, 1)[1].strip(" ，,。；;")
    return ""


def extract_value_after_replace_verb(clause: str) -> str:
    for keyword in REPLACE_KEYWORDS:
        if keyword in clause:
            return clause.split(keyword, 1)[1].strip(" ，,。；;")
    if "是" in clause:
        head, tail = clause.split("是", 1)
        if detect_field_from_clause(head):
            return tail.strip(" ，,。；;")
    return ""


def parse_keyword_values(text: str) -> list[str]:
    values = []
    for chunk in re.split(r"[，,。；;、\s]+", clean_text(text)):
        chunk = clean_text(chunk)
        if chunk:
            values.append(chunk)
    return unique_preserve_order(values)


def merge_tag_update(current_tags: dict[str, Any], tag_tokens: list[str], *, mode: str) -> dict[str, Any]:
    updated = json.loads(json.dumps(current_tags, ensure_ascii=False))
    if mode == "replace":
        updated["state"] = ""
        updated["challenge"] = ""
        updated["signal"] = ""
        updated["technical"] = []

    for token in tag_tokens:
        if token.startswith("S"):
            updated["state"] = token
        elif token.startswith("C"):
            updated["challenge"] = token
        elif token.startswith("B"):
            updated["signal"] = token
        elif token.startswith("T"):
            technical = list(updated.get("technical", []))
            if token not in technical:
                technical.append(token)
            updated["technical"] = technical
    return updated


def parse_draft_revision_instruction(draft: dict[str, Any], instruction: str) -> dict[str, Any]:
    clauses = [item.strip() for item in re.split(r"[，,。；;\n]+", clean_text(instruction)) if item.strip()]
    changes: list[dict[str, Any]] = []
    ignored_fields: list[str] = []
    unparsed: list[str] = []

    for clause in clauses:
        tag_tokens = parse_tag_tokens([clause])
        if "标签" in clause and tag_tokens:
            mode = "append" if contains_append_verb(clause) else "replace"
            changes.append({"field": "tags", "mode": mode, "value": tag_tokens})
            continue

        field = detect_field_from_clause(clause)
        if field is None:
            if clause not in {"需要", "不用", "好的", "可以", "行", "是", "否", "不要"}:
                unparsed.append(clause)
            continue

        if contains_no_change(clause):
            if field not in ignored_fields:
                ignored_fields.append(field)
            continue

        if field == "keywords":
            value = extract_value_after_append_verb(clause) if contains_append_verb(clause) else extract_value_after_replace_verb(clause)
            if not value:
                unparsed.append(clause)
                continue
            mode = "append" if contains_append_verb(clause) else "replace"
            changes.append({"field": field, "mode": mode, "value": parse_keyword_values(value)})
            continue

        if contains_append_verb(clause):
            value = extract_value_after_append_verb(clause)
            if not value:
                unparsed.append(clause)
                continue
            changes.append({"field": field, "mode": "append", "value": value})
            continue

        value = extract_value_after_replace_verb(clause)
        if not value:
            unparsed.append(clause)
            continue
        changes.append({"field": field, "mode": "replace", "value": value})

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for change in changes:
        key = (change["field"], change["mode"])
        if key in seen:
            deduped = [item for item in deduped if (item["field"], item["mode"]) != key]
        seen.add(key)
        deduped.append(change)

    return {
        "changes": deduped,
        "ignored_fields": ignored_fields,
        "unparsed_clauses": unparsed,
    }


def apply_draft_revision(draft: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(draft, ensure_ascii=False))
    for change in plan.get("changes", []):
        field = change["field"]
        mode = change["mode"]
        value = change["value"]

        if field == "tags":
            updated["tags"] = merge_tag_update(updated.get("tags", {}), value, mode=mode)
            continue

        if field == "keywords":
            existing = list(updated.get("keywords", []))
            if mode == "replace":
                updated["keywords"] = unique_preserve_order(value)
            else:
                updated["keywords"] = unique_preserve_order(existing + value)
            continue

        old_value = clean_text(updated.get(field))
        if mode == "append":
            if not old_value:
                updated[field] = clean_text(value)
            elif clean_text(value) in old_value:
                updated[field] = old_value
            else:
                updated[field] = f"{old_value}\n{clean_text(value)}"
        else:
            updated[field] = clean_text(value)

    updated["updated_at"] = iso_now()
    updated["signature"] = experience_signature(updated)
    return updated


def build_business_excel_content(entry: dict[str, Any]) -> str:
    parts: list[str] = []
    for candidate in [entry.get("rule"), entry.get("problem"), entry.get("source", {}).get("text")]:
        value = clean_text(candidate)
        if value and value not in parts:
            parts.append(value)
            break
    action = clean_text(entry.get("action"))
    boundary = clean_text(entry.get("boundary"))
    if action:
        parts.append(f"动作：{action}")
    if boundary:
        parts.append(f"边界：{boundary}")
    return " ".join(parts).strip()


def build_technical_excel_payload(entry: dict[str, Any]) -> dict[str, str]:
    notes_parts = [
        clean_text(entry.get("problem")),
        clean_text(entry.get("rule")),
        clean_text(entry.get("boundary")),
    ]
    notes = " | ".join(part for part in notes_parts if part)
    return {
        "scene": clean_text(entry.get("scene")) or clean_text(entry.get("title")),
        "t_label": " ".join(entry.get("tags", {}).get("technical", [])),
        "command": clean_text(entry.get("action")) or clean_text(entry.get("rule")),
        "notes": notes,
        "success": clean_text(entry.get("validation")) or clean_text(entry.get("title")),
    }


def experience_signature(entry: dict[str, Any]) -> str:
    kind = clean_text(entry.get("kind"))
    if kind == "technical":
        payload = build_technical_excel_payload(entry)
        basis = "|".join([kind, payload["scene"], payload["t_label"], payload["command"], payload["notes"], payload["success"]])
    else:
        basis = "|".join(
            [
                kind,
                clean_text(entry.get("title")),
                build_business_excel_content(entry),
                clean_text(entry.get("tags", {}).get("state")),
                clean_text(entry.get("tags", {}).get("challenge")),
                clean_text(entry.get("tags", {}).get("signal")),
            ]
        )
    return hashlib.sha1(normalize_text(basis).encode("utf-8")).hexdigest()


def entry_search_text(entry: dict[str, Any]) -> str:
    pieces = [
        entry.get("title"),
        entry.get("scene"),
        entry.get("problem"),
        entry.get("rule"),
        entry.get("action"),
        entry.get("boundary"),
        entry.get("validation"),
        " ".join(entry.get("keywords", [])),
        entry.get("source", {}).get("text"),
    ]
    tags = entry.get("tags", {})
    pieces.extend([tags.get("state"), tags.get("challenge"), tags.get("signal"), " ".join(tags.get("technical", []))])
    return "\n".join(clean_text(item) for item in pieces if clean_text(item))


def infer_query_profile(query: str, requested_kind: str = "auto") -> dict[str, Any]:
    kind, kind_reason = infer_experience_kind(text=query, requested_kind=requested_kind)
    if kind == "technical":
        tags = infer_technical_tags(query)
    else:
        tags = infer_business_tags(query)
    query_terms = extract_keywords(query)
    normalized_terms = [normalize_text(term) for term in query_terms if normalize_text(term)]
    normalized_query = normalize_text(query)
    if normalized_query and normalized_query not in normalized_terms:
        normalized_terms.append(normalized_query)
    return {
        "kind": kind,
        "kind_reason": kind_reason,
        "tags": tags,
        "query_terms": query_terms,
        "normalized_terms": normalized_terms,
        "normalized_query": normalized_query,
    }


def score_entry_against_query(entry: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    score = 0

    if clean_text(entry.get("kind")) == profile["kind"]:
        score += 18
        reasons.append("类型匹配")

    entry_tags = entry.get("tags", {})
    profile_tags = profile.get("tags", {})

    if profile["kind"] == "business":
        for field, label in [("state", "S"), ("challenge", "C"), ("signal", "B")]:
            current = clean_text(entry_tags.get(field))
            target = clean_text(profile_tags.get(field))
            if current and target and current == target:
                score += 26
                reasons.append(f"{label} 标签匹配")
    else:
        current_technical = set(entry_tags.get("technical", []))
        for token in profile_tags.get("technical", []):
            if token in current_technical:
                score += 22
                reasons.append(f"{token} 标签匹配")

    search_text = normalize_text(entry_search_text(entry))
    matched_terms: list[str] = []
    for term, normalized in zip(profile.get("query_terms", []), profile.get("normalized_terms", []), strict=False):
        if not normalized:
            continue
        if normalized in search_text and term not in matched_terms:
            matched_terms.append(term)
            score += min(10, 4 + len(term))
    if matched_terms:
        reasons.append(f"关键词命中: {', '.join(matched_terms[:4])}")

    normalized_query = profile.get("normalized_query", "")
    if normalized_query and search_text:
        ratio = SequenceMatcher(None, normalized_query, search_text[: max(len(normalized_query) * 3, 1)]).ratio()
        score += int(ratio * 20)

    return {
        "score": score,
        "reasons": reasons[:4],
        "matched_terms": matched_terms[:8],
    }


def dedupe_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        signature = entry.get("signature") or experience_signature(entry)
        if signature in seen:
            continue
        seen.add(signature)
        result.append(entry)
    return result


def search_entries(entries: list[dict[str, Any]], query: str, *, requested_kind: str = "auto", limit: int = 5) -> dict[str, Any]:
    profile = infer_query_profile(query, requested_kind=requested_kind)
    deduped = dedupe_entries(entries)
    scored: list[dict[str, Any]] = []
    for entry in deduped:
        scored_item = score_entry_against_query(entry, profile)
        if scored_item["score"] <= 0:
            continue
        scored.append({"entry": entry, "score": scored_item["score"], "reasons": scored_item["reasons"], "matched_terms": scored_item["matched_terms"]})

    scored.sort(key=lambda item: (-item["score"], item["entry"].get("updated_at", ""), item["entry"].get("title", "")))
    return {
        "query_profile": profile,
        "results": scored[:limit],
        "total_hits": len(scored),
    }

