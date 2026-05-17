# -*- coding: utf-8 -*-
"""辅助工具函数"""

import re
from typing import Any, Optional


def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ""
    return str(text).strip()


def normalize_text(text: str) -> str:
    """标准化文本"""
    text = clean_text(text)
    text = text.replace("\u3000", " ")
    return "".join(text.split()).lower()


def digits_only(text: str) -> str:
    """只保留数字"""
    return "".join(c for c in text if c.isdigit())


def score_client_match(client: dict[str, Any], q_row: Optional[int], q_digits: str, q_norm: str) -> int:
    """计算客户匹配分数"""
    score = 0
    
    # 行号匹配
    if q_row is not None and client.get("row") == q_row:
        return 100
    
    # 电话匹配
    client_phone = digits_only(str(client.get("phone", "")))
    if client_phone and q_digits:
        if q_digits in client_phone or client_phone in q_digits:
            score += 50
    
    # 姓名匹配
    client_name = normalize_text(str(client.get("name", "")))
    if client_name and q_norm:
        if q_norm in client_name or client_name in q_norm:
            score += 30
    
    return score


def analyze_followup_content(client: dict[str, Any], content: str, properties: list[dict[str, Any]]) -> dict[str, Any]:
    """分析跟进内容"""
    insights = {
        "mentioned_house_ids": [],
        "already_recommended_ids": [],
        "new_house_ids": [],
        "mentioned_properties": [],
        "update_suggestions": [],
    }
    
    # 提取房源 ID
    house_ids = re.findall(r'107\d{9}', content)
    insights["mentioned_house_ids"] = house_ids
    
    return insights
