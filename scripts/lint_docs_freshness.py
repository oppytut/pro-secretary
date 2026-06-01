"""Lint that README + ARCHITECTURE.md stay in sync with filesystem.

Catches docs-rot before it ships. Specifically:

1. ARCHITECTURE.md tree of telegram-bot/watchdogs/*.py must match filesystem.
2. ARCHITECTURE.md tree of telegram-bot/infra/*.py must match filesystem.
3. README "## features shipped" count must match feature table row count.

Exit 0 = clean, exit 1 = docs drift.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _list_module_files(rel_dir: str) -> list[str]:
    d = ROOT / rel_dir
    if not d.is_dir():
        return []
    return sorted(
        p.name
        for p in d.iterdir()
        if p.is_file() and p.suffix == ".py" and p.name != "__init__.py"
    )


def _extract_tree_block(arch_text: str, header: str) -> list[str]:
    pattern = rf"[├└]── {header}/[^\n]*\n((?:(?:│|\s)\s*[├└][^\n]+\n)+)"
    m = re.search(pattern, arch_text)
    if not m:
        return []
    block = m.group(1)
    files: list[str] = []
    for line in block.split("\n"):
        nm = re.search(r"([a-z_][a-z_0-9]*\.py)", line)
        if nm:
            files.append(nm.group(1))
    return sorted(files)


def _arch_check_dir(arch_text: str, rel_dir: str, header: str) -> list[str]:
    fs = _list_module_files(rel_dir)
    docs = _extract_tree_block(arch_text, header)
    errors: list[str] = []
    fs_set = set(fs)
    docs_set = set(docs)
    missing_in_docs = fs_set - docs_set
    extra_in_docs = docs_set - fs_set
    if missing_in_docs:
        errors.append(
            f"ARCHITECTURE.md {rel_dir}: missing in docs: {sorted(missing_in_docs)}"
        )
    if extra_in_docs:
        errors.append(
            f"ARCHITECTURE.md {rel_dir}: extra in docs (not on disk): {sorted(extra_in_docs)}"
        )
    return errors


def _readme_check_feature_count(readme_text: str) -> list[str]:
    status_match = re.search(r"(\d+)\s+features?\s+shipped", readme_text, re.IGNORECASE)
    if not status_match:
        return ["README.md: cannot find 'N features shipped' status line"]
    declared = int(status_match.group(1))

    table_match = re.search(
        r"###\s+Shipped Features\s*\n+\|\s*#\s*\|.+?\n((?:\|.+?\n)+)",
        readme_text,
        re.DOTALL,
    )
    if not table_match:
        return ["README.md: cannot find Shipped Features table"]
    rows = [r for r in table_match.group(1).strip().split("\n") if r.strip()]
    actual = sum(1 for r in rows if not re.match(r"^\|\s*-+\s*\|", r))

    if declared != actual:
        return [
            f"README.md: declares '{declared} features shipped' but table has {actual} rows"
        ]
    return []


def main() -> int:
    arch_path = ROOT / "ARCHITECTURE.md"
    readme_path = ROOT / "README.md"

    if not arch_path.exists():
        print("ARCHITECTURE.md not found", file=sys.stderr)
        return 1
    if not readme_path.exists():
        print("README.md not found", file=sys.stderr)
        return 1

    arch_text = arch_path.read_text()
    readme_text = readme_path.read_text()

    errors: list[str] = []
    errors.extend(_arch_check_dir(arch_text, "telegram-bot/infra", "infra"))
    errors.extend(_arch_check_dir(arch_text, "telegram-bot/watchdogs", "watchdogs"))
    errors.extend(_readme_check_feature_count(readme_text))

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print("OK: docs in sync with filesystem")
    print(f"  - ARCHITECTURE.md infra/ matches {len(_list_module_files('telegram-bot/infra'))} files")
    print(f"  - ARCHITECTURE.md watchdogs/ matches {len(_list_module_files('telegram-bot/watchdogs'))} files")
    print("  - README.md feature count matches table")
    return 0


if __name__ == "__main__":
    sys.exit(main())
