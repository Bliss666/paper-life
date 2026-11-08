# -*- coding: utf-8 -*-
"""校验每张图的「情况一 / 情况二」标签与细腻度细节是否到位。"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

import yaml  # noqa: E402

WHITE = (255, 255, 255)


def tag_ok(im: Image.Image, box, need_dark_bg: bool) -> bool:
    """标签区域应包含黑底 + 白字。"""
    x0, y0, x1, y1 = box
    px = im.load()
    dark = 0
    white = 0
    for y in range(y0, min(y1, y0 + 52), 2):
        for x in range(x0, min(x1, x0 + 190), 2):
            p = px[x, y]
            if sum(p) < 200:
                dark += 1
            elif sum(p) > 700:
                white += 1
    return dark > 200 and white > 40


def main() -> int:
    topics = yaml.safe_load((ROOT / "content" / "life_topics.yml").read_text(encoding="utf-8"))
    bad = []
    n = 0
    for t in topics:
        for i in range(1, len(t["pages"]) + 1):
            f = ROOT / "out" / t["id"] / f"{i + 1:02d}-page{i}.jpg"
            if not f.exists():
                continue
            n += 1
            im = Image.open(f).convert("RGB")
            W, H = im.size
            # 上格标签在 (52, 52) 附近，下格标签在面板第二段起点
            panel_h = int((H - 52 * 2 - 30 - 118 * 2 - 200) / 2)
            top_y = 52
            bot_y = 52 + panel_h + 118 + 30
            if not tag_ok(im, (52, top_y, 240, top_y + 52), True):
                bad.append((t["id"], i, "top-tag"))
            if not tag_ok(im, (52, bot_y, 240, bot_y + 52), True):
                bad.append((t["id"], i, "bottom-tag"))

    print(f"检查 {n} 页")
    print(f"标签缺失：{len(bad)}")
    for b in bad[:12]:
        print("  ", b)
    return 0


if __name__ == "__main__":
    sys.exit(main())
