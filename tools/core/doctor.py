from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
HOME_ROOT = WORKSPACE_ROOT.parent
SELF_PATH = Path(__file__).resolve()

TEXT_SUFFIXES = {".md", ".py", ".ps1", ".cmd", ".yaml", ".yml", ".json"}
SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    "runtime",
    "_house_grab_runtime",
    "_house_grab_logs",
    "_house_grab_backups",
    "state",
    "memory",
}
MOJIBAKE_MARKERS = [
    "\ufffd",
    "锟",
    "鈥",
    "馃",
    "鉁",
    "銆",
    "鍥㈠洟",
    "浣犲",
]
LEGACY_PATH_MARKERS = [
    r"D:\OpenClaw\Workspaces\main",
    "RUN_TUANTUAN.cmd",
]
POWERSHELL_TEXT_CMDS = ("Get-Content", "Set-Content", "Add-Content", "Out-File")
PYTHON_OPEN_RE = re.compile(r"(?<![\w.])open\(")
PYTHON_PATH_IO_RE = re.compile(r"\.(read_text|write_text)\(")
LEGACY_IGNORE_LINE_MARKERS = ("old", "retired", "deprecated", "旧", "退役", "不再")
LEGACY_IGNORE_HEADINGS = ("do not use", "retired", "warning")


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _iter_active_files() -> list[Path]:
    files: list[Path] = []

    design_doc = _first_existing(
        [
            WORKSPACE_ROOT / "memory" / "团团助手系统设计.md",
            *sorted((WORKSPACE_ROOT / "memory").glob("*系统设计*.md")),
        ]
    )

    explicit_files = [
        WORKSPACE_ROOT / "AGENTS.md",
        WORKSPACE_ROOT / "BOOTSTRAP.md",
        WORKSPACE_ROOT / "SOUL.md",
        WORKSPACE_ROOT / "TOOLS.md",
        WORKSPACE_ROOT / "CORE_GUARD.md",
        WORKSPACE_ROOT / "EXEC_RULES.md",
        WORKSPACE_ROOT / "workspace" / "docs" / "architecture.md",
        WORKSPACE_ROOT / "workspace" / "config" / "triggers.yaml",
        WORKSPACE_ROOT / "workspace" / "config" / "protected_core.json",
        WORKSPACE_ROOT / "skills" / "real-estate-analyst" / "SKILL.md",
        HOME_ROOT / "config" / "agent-system-config.yaml",
    ]

    if design_doc is not None:
        explicit_files.append(design_doc)

    for path in explicit_files:
        if path.exists():
            files.append(path)

    scan_roots = [
        WORKSPACE_ROOT / "tools",
        WORKSPACE_ROOT / "scripts",
        WORKSPACE_ROOT / "workspace" / "docs",
        WORKSPACE_ROOT / "workspace" / "config",
    ]

    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            if path.name.endswith(".bak"):
                continue
            files.append(path)

    unique: dict[str, Path] = {}
    for path in files:
        unique[str(path.resolve())] = path
    return sorted(unique.values())


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE_ROOT))
    except ValueError:
        try:
            return str(path.relative_to(HOME_ROOT))
        except ValueError:
            return str(path)


def _add_finding(
    findings: list[dict[str, Any]],
    path: Path,
    lineno: int,
    category: str,
    issue: str,
    snippet: str,
) -> None:
    findings.append(
        {
            "path": _relative_path(path),
            "line": lineno,
            "category": category,
            "issue": issue,
            "snippet": snippet[:180],
        }
    )


def _scan_mojibake(path: Path, findings: list[dict[str, Any]]) -> None:
    text = _read_text(path)
    for lineno, line in enumerate(text.splitlines(), start=1):
        for marker in MOJIBAKE_MARKERS:
            if marker in line:
                _add_finding(
                    findings,
                    path,
                    lineno,
                    "encoding",
                    f"Suspicious mojibake marker found: {marker!r}",
                    line.strip(),
                )
                break


def _scan_legacy_paths(path: Path, findings: list[dict[str, Any]]) -> None:
    text = _read_text(path)
    current_heading = ""
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            current_heading = stripped.lstrip("#").strip().lower()
        for marker in LEGACY_PATH_MARKERS:
            if marker in line:
                lower_line = line.lower()
                if any(token in lower_line for token in LEGACY_IGNORE_LINE_MARKERS):
                    break
                if any(token in current_heading for token in LEGACY_IGNORE_HEADINGS):
                    break
                _add_finding(
                    findings,
                    path,
                    lineno,
                    "legacy_path",
                    f"Legacy path or entrypoint marker found: {marker}",
                    line.strip(),
                )
                break


def _scan_powershell_encoding(path: Path, findings: list[dict[str, Any]]) -> None:
    if path.suffix.lower() != ".ps1":
        return

    text = _read_text(path)
    for lineno, line in enumerate(text.splitlines(), start=1):
        compact = line.strip()
        if not compact or compact.startswith("#"):
            continue
        if not any(cmd in compact for cmd in POWERSHELL_TEXT_CMDS):
            continue
        if "-Encoding" in compact:
            continue
        _add_finding(
            findings,
            path,
            lineno,
            "encoding_rule",
            "PowerShell text I/O without explicit -Encoding.",
            compact,
        )


def _scan_python_encoding(path: Path, findings: list[dict[str, Any]]) -> None:
    if path.suffix.lower() != ".py":
        return

    lines = _read_text(path).splitlines()
    for index, line in enumerate(lines):
        compact = line.strip()
        if not compact or compact.startswith("#"):
            continue
        if not (PYTHON_OPEN_RE.search(compact) or PYTHON_PATH_IO_RE.search(compact)):
            continue
        window = " ".join(part.strip() for part in lines[index : index + 4])
        if "encoding=" in window:
            continue
        if "rb" in compact or "wb" in compact or "ab" in compact:
            continue
        _add_finding(
            findings,
            path,
            index + 1,
            "encoding_rule",
            "Python text I/O without explicit encoding.",
            compact,
        )


def _run_doctor() -> tuple[dict[str, Any], int]:
    findings: list[dict[str, Any]] = []
    files = _iter_active_files()

    for path in files:
        if path.resolve() == SELF_PATH:
            continue
        _scan_mojibake(path, findings)
        _scan_legacy_paths(path, findings)
        _scan_powershell_encoding(path, findings)
        _scan_python_encoding(path, findings)

    encoding_count = sum(1 for item in findings if item["category"] == "encoding")
    legacy_count = sum(1 for item in findings if item["category"] == "legacy_path")
    rule_count = sum(1 for item in findings if item["category"] == "encoding_rule")

    if findings:
        return (
            {
                "status": "warn",
                "message": "Potential encoding or legacy structure issues found.",
                "scanned_file_count": len(files),
                "encoding_issue_count": encoding_count,
                "legacy_path_issue_count": legacy_count,
                "encoding_rule_issue_count": rule_count,
                "findings": findings[:80],
            },
            1,
        )

    return (
        {
            "status": "ok",
            "message": "No active-file mojibake, legacy entrypoint, or missing encoding rule found.",
            "scanned_file_count": len(files),
            "encoding_issue_count": 0,
            "legacy_path_issue_count": 0,
            "encoding_rule_issue_count": 0,
            "findings": [],
        },
        0,
    )


def cmd_doctor(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    del args
    return _run_doctor()


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan active OpenClaw files for encoding drift.")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args()
    payload, code = _run_doctor()
    dump_kwargs: dict[str, Any] = {"ensure_ascii": True}
    if args.pretty:
        dump_kwargs["indent"] = 2
    sys.stdout.write(json.dumps(payload, **dump_kwargs) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
