# -*- coding: utf-8 -*-
"""经验批准功能"""

import argparse
from typing import Any

import sys
sys.path.insert(0, str(__file__.rsplit('\\', 2)[0]))


def cmd_experience_approve(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    """经验批准"""
    return {
        "status": "success",
        "message": "经验批准功能",
    }, 0
