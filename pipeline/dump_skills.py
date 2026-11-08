# -*- coding: utf-8 -*-
"""导出技巧池为纯文本，方便人工逐条审校（不修改任何文件）。"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
data = yaml.safe_load((ROOT / "content" / "skills.yml").read_text(encoding="utf-8"))
out = ROOT / "out" / "_skills_dump.txt"

lines = []
for cat in ["生活", "学习", "工作", "沟通", "数码"]:
    lines.append(f"\n===== {cat} =====")
    for s in data["skills"]:
        if s.get("cat") == cat:
            lines.append(f"{s['id']} | {s['top']} || {s['bottom']}")
out.write_text("\n".join(lines), encoding="utf-8")
print(f"-> {out}  ({len(data['skills'])} 条)")
