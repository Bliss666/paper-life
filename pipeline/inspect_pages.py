# -*- coding: utf-8 -*-
"""查看指定页面的背景场景与小元素匹配情况。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

import yaml  # noqa: E402
from backdrops import pick_props  # noqa: E402

TARGET = {("tip-001", 2), ("tip-001", 5), ("life-002", 4), ("life-002", 5),
          ("life-003", 1), ("life-003", 3)}

topics = yaml.safe_load((ROOT / "content" / "life_topics.yml").read_text(encoding="utf-8"))
for t in topics:
    for i, p in enumerate(t["pages"], 1):
        if (t["id"], i) in TARGET:
            print(f"{t['id']} p{i} | 场景 {p.get('top_backdrop')} / {p.get('bottom_backdrop')}")
            print(f"   上: {p['top']}")
            print(f"      -> {pick_props(p['top'])}")
            print(f"   下: {p['bottom']}")
            print(f"      -> {pick_props(p['bottom'])}")
