# -*- coding: utf-8 -*-
"""检查最终成品图的分镜上部是否饱满。

判据：把分镜上部区域量化成 12x8 网格，看有多少格"有内容"
（与该格背景色的差异足够大）。格子占比越高，画面越满。
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

import yaml  # noqa: E402

COLS, ROWS = 12, 8


def grid_fill(im: Image.Image, box) -> float:
    x0, y0, x1, y1 = box
    crop = im.crop(box)
    w, h = crop.size
    filled = 0
    for r in range(ROWS):
        for c in range(COLS):
            cell = crop.crop((c * w // COLS, r * h // ROWS,
                              (c + 1) * w // COLS, (r + 1) * h // ROWS)).resize((6, 6), Image.BILINEAR)
            px = cell.load()
            # 取这个格子的中位色（代表背景）与最偏离的颜色
            colors = [px[x, y] for y in range(6) for x in range(6)]
            colors.sort(key=lambda p: p[0] + p[1] + p[2])
            med = colors[len(colors) // 2]
            dev = max(abs(p[0] - med[0]) + abs(p[1] - med[1]) + abs(p[2] - med[2]) for p in colors)
            if dev > 60:
                filled += 1
    return filled / (COLS * ROWS)


def main() -> int:
    topics = yaml.safe_load((ROOT / "content" / "life_topics.yml").read_text(encoding="utf-8"))
    rows = []
    for t in topics:
        for i, p in enumerate(t["pages"], 1):
            f = ROOT / "out" / t["id"] / f"{i + 1:02d}-page{i}.jpg"
            if not f.exists():
                continue
            im = Image.open(f).convert("RGB")
            W, H = im.size
            # 上格主体区（避开字幕框）
            top = grid_fill(im, (56, 60, W - 56, 430))
            bot = grid_fill(im, (56, H // 2 + 40, W - 56, H - 260))
            rows.append((t["id"], i, p.get("top_backdrop"), p.get("bottom_backdrop"), top, bot))

    avg_t = sum(r[4] for r in rows) / len(rows)
    avg_b = sum(r[5] for r in rows) / len(rows)
    print(f"检查 {len(rows)} 页")
    print(f"上格平均饱满度 {avg_t:.3f}   下格平均饱满度 {avg_b:.3f}")
    thin = [r for r in rows if r[4] < 0.30 or r[5] < 0.30]
    print(f"偏空的页：{len(thin)}")
    for r in thin:
        print("  ", r)

    # 按场景统计，找出仍然偏空的场景
    per = {}
    for r in rows:
        for bd, val in ((r[2], r[4]), (r[3], r[5])):
            per.setdefault(bd, []).append(val)
    print("\n按场景的平均饱满度：")
    for k, v in sorted(per.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
        print(f"  {k:<12} {sum(v) / len(v):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
