# -*- coding: utf-8 -*-
"""经验草稿功能"""

import argparse
from typing import Any

import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from utils.cache import ensure_cache


def cmd_experience_draft(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """经验草稿"""
    return {
        "status": "success",
        "message": "经验草稿功能",
    }, 0


def cmd_experience_draft_list(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """经验草稿列表"""
    return {
        "status": "success",
        "drafts": [],
    }, 0
