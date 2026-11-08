# -*- coding: utf-8 -*-
"""检测小元素是否真的出现在成品图里。

做法：在分镜四角的候选位区域，统计"非背景、非角色"的独立轮廓块。
简单可靠的代理指标：角落区域内的墨线密度（元素有描边）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

import yaml  # noqa: E402


def ink(im: Image.Image, box) -> float:
    x0, y0, x1, y1 = box
    crop = im.crop(box).convert("L").resize((70, 50), Image.BILINEAR)
    px = crop.load()
    dark = sum(1 for y in range(50) for x in range(70) if px[x, y] < 120)
    return dark / (70 * 50)


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
            top_y = 52
            bot_y = 52 + panel_h + 118 + 30
            # 上格：左右两侧整条竖带（元素常驻区）
            a = ink(im, (58, top_y + 40, 340, top_y + 420))
            b = ink(im, (W - 340, top_y + 40, W - 58, top_y + 420))
            c = ink(im, (58, bot_y + 40, 340, bot_y + 420))
            d_ = ink(im, (W - 340, bot_y + 40, W - 58, bot_y + 420))
            best = max(a, b, c, d_)
            rows.append((d.name, i, best, (a, b, c, d_)))

    if not rows:
        print("没有找到产物页面")
        return 1

    n = len(rows)
    avg = sum(r[2] for r in rows) / n
    print(f"检查 {n} 页")
    print(f"角落平均墨线密度 {avg:.4f}")
    low = [r for r in rows if r[2] < 0.10]
    print(f"角落过空的页：{len(low)}")
    for r in low[:12]:
        print("  ", r[0], "p" + str(r[1]), f"{r[2]:.3f}", r[3])
    return 0


if __name__ == "__main__":
    sys.exit(main())
