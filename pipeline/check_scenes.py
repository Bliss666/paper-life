# -*- coding: utf-8 -*-
"""检查自动背景场景匹配结果。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

import yaml  # noqa: E402
from backdrops import pick_scene  # noqa: E402

topics = yaml.safe_load((ROOT / "content" / "life_topics.yml").read_text(encoding="utf-8"))
from collections import Counter  # noqa: E402

cnt = Counter()
lines = []
for t in topics:
    for p in t["pages"]:
        a = pick_scene(p["top"], "office")
        b = pick_scene(p["bottom"], "office")
        cnt[a] += 1
        cnt[b] += 1
        lines.append(f"{t['id']:<10} {a:<11} <-> {b:<11} | {p['top'][:16]} || {p['bottom'][:16]}")

lines.append("")
lines.append("分布：")
for name, n in cnt.most_common():
    lines.append(f"  {name:<12} {n}")

(ROOT / "out" / "_scene_check.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))