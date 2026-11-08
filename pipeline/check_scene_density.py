# -*- coding: utf-8 -*-
"""测量场景在「角色头部区域（画面上部）」的墨线覆盖度。

透明图层要先合成到白底上，否则 convert('L') 会把透明区当成黑色。
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from backdrops import SCENES  # noqa: E402

W, H = 976, 560


def ink_top(fn) -> tuple[float, float]:
    """返回 (上部墨线覆盖率, 整体墨线覆盖率)。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fn(d, W, H, {
        "far": (205, 214, 228), "mid": (172, 182, 196), "near": (140, 150, 165),
        "ink": (40, 34, 30), "glow": (255, 248, 214),
    })
    im = Image.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, 255)), layer).convert("L")
    px = im.load()
    tot = ntot = top = ntop = 0
    for y in range(0, H, 3):
        for x in range(0, W, 3):
            hit = px[x, y] < 130
            ntot += 1
            tot += hit
            if y < H * 0.45:
                ntop += 1
                top += hit
    return top / max(1, ntop), tot / max(1, ntot)


def main() -> int:
    stats = defaultdict(list)
    for name, fn in SCENES.items():
        try:
            stats[name].append(ink_top(fn))
        except Exception as exc:  # noqa: BLE001
            print(f"  !! {name}: {exc!r}")
    rows = []
    for k, v in stats.items():
        tp = sum(a for a, _ in v) / len(v)
        ov = sum(b for _, b in v) / len(v)
        rows.append((tp, ov, k))
    rows.sort()
    print("场景上部墨线覆盖率 / 整体墨线覆盖率：")
    for tp, ov, k in rows:
        flag = "  <-- 上部线条太少" if tp < 0.02 else ""
        print(f"  {k:<12} 上 {tp:.4f}   全 {ov:.4f}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
