# -*- coding: utf-8 -*-
"""刷新缓存功能"""

import argparse
from typing import Any

import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))

from utils.cache import build_cache


def cmd_refresh(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """刷新缓存"""
    try:
        cache = build_cache()
        return {
            "status": "ok",
            "command": "refresh",
            "cache_generated_at": cache.get("generated_at"),
            "client_count": len(cache.get("clients", [])),
            "property_count": len(cache.get("properties", [])),
        }, 0
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }, 1
