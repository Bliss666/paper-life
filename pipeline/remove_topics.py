# -*- coding: utf-8 -*-
"""从 content/topics.yml 中删除指定 id 的选题条目。

用法：python pipeline/remove_topics.py ai-004 ai-005 ai-006 ai-007
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YML = ROOT / "content" / "topics.yml"


def main(ids: list[str]) -> int:
    text = YML.read_text(encoding="utf-8")
    lines = text.split("\n")
    out: list[str] = []
    skip = False
    removed: list[str] = []

    for ln in lines:
        if ln.startswith("- id:"):
            tid = ln.split(":", 1)[1].strip()
            skip = tid in ids
            if skip:
                removed.append(tid)
                continue
        if skip:
            # 条目内部，跳过；遇到下一个 "- id:" 或空行+新条目时结束
            if ln.startswith("- id:"):
                skip = False
            else:
                continue
        out.append(ln)

    YML.write_text("\n".join(out), encoding="utf-8")
    print(f"已删除：{removed}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
