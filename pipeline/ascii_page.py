# -*- coding: utf-8 -*-
"""把渲染出的页面转成 ASCII 缩略图，用来快速确认构图是否正常。

用法：
    python pipeline/ascii_page.py out/sk-03/02-page1.jpg
    python pipeline/ascii_page.py out/sk-03/02-page1.jpg --cols 80
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

RAMP = " .:-=+*#%@"


def ascii_art(im: Image.Image, cols: int = 72) -> str:
    rows = cols * 2 // 3
    small = im.convert("L").resize((cols, rows), Image.LANCZOS)
    px = small.load()
    lines = []
    for y in range(rows):
        line = "".join(RAMP[min(len(RAMP) - 1, (255 - px[x, y]) * len(RAMP) // 256)]
                       for x in range(cols))
        lines.append(line)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--cols", type=int, default=72)
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"找不到 {p}")
        return 1
    im = Image.open(p).convert("RGB")
    print(f"=== {p.name}  {im.size} ===")
    print(ascii_art(im, args.cols))
    return 0


if __name__ == "__main__":
    sys.exit(main())
