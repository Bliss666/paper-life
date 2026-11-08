# -*- coding: utf-8 -*-
"""细腻度检查：统计画面上的层次数量（不同色阶的个数）与边缘细节。

细腻的画面 = 更多的中间色阶、更丰富的描边层级。
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

import yaml  # noqa: E402


def analyze(im: Image.Image, box) -> tuple[int, int, float]:
    """返回 (色阶数, 边缘点数, 平均局部对比)。"""
    crop = im.crop(box).convert("L")
    w, h = crop.size
    px = crop.load()
    # 色阶（量化到 32 级）
    levels = set()
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            levels.add(px[x, y] // 8)
    # 边缘点（相邻像素差大）
    edges = 0
    n = 0
    tot_contrast = 0.0
    for y in range(1, h - 1, 3):
        for x in range(1, w - 1, 3):
            g = px[x, y]
            lap = abs(4 * g - px[x - 1, y] - px[x + 1, y] - px[x, y - 1] - px[x, y + 1])
            n += 1
            tot_contrast += lap
            if lap > 40:
                edges += 1
    return len(levels), edges, tot_contrast / max(1, n)


def main() -> int:
    rows = []
    for d in sorted((ROOT / "out").glob("*/")):
        img_dir = d / "images"
        files = sorted(img_dir.glob("*-page*.jpg")) if img_dir.exists() \
            else sorted(d.glob("*-page*.jpg"))
        for f in files:
            m = re.search(r"page(\d+)", f.name)
            i = int(m.group(1)) if m else 0
            im = Image.open(f).convert("RGB")
            W, H = im.size
            panel_h = int((H - 52 * 2 - 30 - 118 * 2 - 200) / 2)
            bot_y = 52 + panel_h + 118 + 30
            lv, ed, ct = analyze(im, (56, 60, W - 56, bot_y - 10))
            rows.append((d.name, i, lv, ed, ct))

    if not rows:
        print("没有找到产物页面")
        return 1

    n = len(rows)
    print(f"检查 {n} 页")
    print(f"平均色阶数   {sum(r[2] for r in rows) / n:.1f} / 32")
    print(f"平均边缘点数 {sum(r[3] for r in rows) / n:.0f}")
    print(f"平均局部对比 {sum(r[4] for r in rows) / n:.1f}")
    low = sorted(rows, key=lambda r: r[3])[:8]
    print("\n细节最少的页：")
    for r in low:
        print(f"  {r[0]:<10} p{r[1]}  色阶{r[2]:>3}  边缘{r[3]:>5}  对比{r[4]:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
