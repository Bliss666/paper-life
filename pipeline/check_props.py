# -*- coding: utf-8 -*-
"""检查小元素是否真的画进了分镜，以及和文案的对应关系。"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

import yaml  # noqa: E402
from backdrops import PROPS, pick_props  # noqa: E402


def main() -> int:
    topics = yaml.safe_load((ROOT / "content" / "life_topics.yml").read_text(encoding="utf-8"))
    n = 0
    empty = 0
    cnt = Counter()
    for t in topics:
        for i, p in enumerate(t["pages"], 1):
            top = pick_props(p["top"])
            bot = pick_props(p["bottom"])
            n += 1
            if not top and not bot:
                empty += 1
            for x in top + bot:
                cnt[x] += 1
    print(f"检查 {n} 页")
    print(f"无小元素的页：{empty}")
    print(f"用到 {len(cnt)} 种小元素")
    print(cnt.most_common())
    print(f"\n元素库总数：{len(PROPS)}")
    unused = [k for k in PROPS if k not in cnt]
    print(f"未被用到：{len(unused)} -> {unused}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
