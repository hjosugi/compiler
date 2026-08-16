#!/usr/bin/env python3
"""Check local Markdown links and stale pre-refactor path names."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
STALE = (
    "compiler-backend-atlas/",
    "toy-llvm-language/",
    "compendium/",
    "compiler-backend-compendium",
)


def markdown_files() -> list[Path]:
    roots = [ROOT / "README.md", ROOT / "CHANGELOG.md", ROOT / "CONTRIBUTING.md"]
    for directory in ("docs", "tutorial", "labs", "benchmarks"):
        roots.extend(sorted((ROOT / directory).rglob("*.md")))
    return [path for path in roots if path.exists()]


def local_target(raw: str) -> str | None:
    raw = raw.strip()
    if raw.startswith("<") and ">" in raw:
        raw = raw[1 : raw.index(">")]
    else:
        raw = raw.split(maxsplit=1)[0]
    if raw.startswith(("http://", "https://", "mailto:", "#")):
        return None
    return unquote(raw.split("#", 1)[0])


def main() -> int:
    errors: list[str] = []
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)
        for stale in STALE:
            if stale in text:
                errors.append(f"{relative}: stale path {stale!r}")
        for match in LINK.finditer(text):
            target = local_target(match.group(1))
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"{relative}: link escapes repository: {target}")
                continue
            if not resolved.exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{relative}:{line}: missing link target: {target}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"PASS: {len(markdown_files())} Markdown files have valid local links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
