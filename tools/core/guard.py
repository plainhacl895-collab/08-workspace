from __future__ import annotations

import argparse
import hashlib
import json
import stat
from datetime import datetime
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = WORKSPACE_ROOT / "workspace" / "config" / "protected_core.json"

DEFAULT_PROTECTED_PATHS = [
    "AGENTS.md",
    "BOOTSTRAP.md",
    "CORE_GUARD.md",
    "MEMORY.md",
    "SOUL.md",
    "TEAM.md",
    "TOOLS.md",
    "USER.md",
    "workspace/docs/architecture.md",
    "memory/团团助手系统设计.md",
    "tools/main.py",
    "tools/core/guard.py",
    "tools/RUN_TUANTUAN_qidong.cmd",
    "tools/LOCK_TUANTUAN_CORE.ps1",
    "tools/UNLOCK_TUANTUAN_CORE.ps1",
    "workspace/config/triggers.yaml",
]

DEFAULT_ALLOWED_WRITE_AREAS = [
    "runtime/",
    "temp/",
    "state/",
    "_house_grab_runtime/",
    "_house_grab_logs/",
    "memory/experience/drafts/",
    "memory/experience/approved_store.json",
    "D:/Unique work form/daily_followup.xlsm",
]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_readonly(path: Path) -> bool:
    attributes = getattr(path.stat(), "st_file_attributes", 0)
    if attributes:
        return bool(attributes & stat.FILE_ATTRIBUTE_READONLY)
    return not bool(path.stat().st_mode & stat.S_IWRITE)


def _clear_readonly(path: Path) -> None:
    if path.exists():
        path.chmod(path.stat().st_mode | stat.S_IWRITE)


def _build_manifest(reason: str) -> dict[str, Any]:
    hashes: dict[str, str] = {}
    for relative_path in DEFAULT_PROTECTED_PATHS:
        target = WORKSPACE_ROOT / relative_path
        if not target.exists():
            raise FileNotFoundError(f"missing protected path: {relative_path}")
        hashes[relative_path] = _sha256_file(target)

    return {
        "version": 2,
        "frozen_at": datetime.now().isoformat(timespec="seconds"),
        "workspace_root": str(WORKSPACE_ROOT),
        "reason": reason.strip() or "refresh protected core manifest",
        "protected_paths": DEFAULT_PROTECTED_PATHS,
        "allowed_write_areas": DEFAULT_ALLOWED_WRITE_AREAS,
        "hashes": hashes,
    }


def cmd_core_guard_freeze(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    try:
        manifest = _build_manifest(getattr(args, "reason", ""))
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        _clear_readonly(MANIFEST_PATH)
        MANIFEST_PATH.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {
            "status": "ok",
            "message": "核心保护清单已更新。",
            "manifest_path": str(MANIFEST_PATH),
            "protected_count": len(manifest["protected_paths"]),
        }, 0
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "manifest_path": str(MANIFEST_PATH),
        }, 1


def cmd_core_guard_status(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    if not MANIFEST_PATH.exists():
        return {
            "status": "missing_manifest",
            "message": "核心保护清单不存在，请先执行 core-guard-freeze。",
            "manifest_path": str(MANIFEST_PATH),
            "protected_count": len(DEFAULT_PROTECTED_PATHS),
            "drift": [],
            "unlocked_paths": [],
        }, 1

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "status": "invalid_manifest",
            "message": f"核心保护清单读取失败：{exc}",
            "manifest_path": str(MANIFEST_PATH),
            "protected_count": len(DEFAULT_PROTECTED_PATHS),
            "drift": [],
            "unlocked_paths": [],
        }, 1

    protected_paths = manifest.get("protected_paths", DEFAULT_PROTECTED_PATHS)
    expected_hashes = manifest.get("hashes", {})
    drift: list[dict[str, Any]] = []
    unlocked_paths: list[str] = []

    for relative_path in protected_paths:
        target = WORKSPACE_ROOT / relative_path
        if not target.exists():
            drift.append({"path": relative_path, "issue": "missing"})
            continue

        expected_hash = expected_hashes.get(relative_path)
        actual_hash = _sha256_file(target)
        if expected_hash and actual_hash != expected_hash:
            drift.append(
                {
                    "path": relative_path,
                    "issue": "modified",
                    "expected_sha256": expected_hash,
                    "actual_sha256": actual_hash,
                }
            )

        if not _is_readonly(target):
            unlocked_paths.append(relative_path)

    status = "ok" if not drift else "drift"
    exit_code = 0 if status == "ok" else 1
    return {
        "status": status,
        "message": "核心保护正常。" if status == "ok" else "核心保护存在漂移。",
        "manifest_path": str(MANIFEST_PATH),
        "frozen_at": manifest.get("frozen_at"),
        "reason": manifest.get("reason", ""),
        "protected_count": len(protected_paths),
        "allowed_write_areas": manifest.get("allowed_write_areas", DEFAULT_ALLOWED_WRITE_AREAS),
        "drift": drift,
        "unlocked_paths": unlocked_paths,
    }, exit_code

