#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "feishu"
TARGETS = [
    ROOT / "skills" / "feishu" / "SKILL.md",
]


def main() -> int:
    if not SKILL_DIR.exists():
        raise SystemExit("skills/feishu directory not found")

    skill_file = SKILL_DIR / "SKILL.md"
    if not skill_file.exists():
        raise SystemExit("skills/feishu/SKILL.md not found")

    print(json.dumps(
        {
            "ok": True,
            "message": "The /feishu skill wrapper is present in the repository. If the host runtime supports workspace skill discovery, reopening or refreshing the workspace should make /feishu available without modifying official source code.",
            "skill_path": str(skill_file),
            "targets": [str(p) for p in TARGETS],
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
