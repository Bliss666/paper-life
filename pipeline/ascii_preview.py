# -*- coding: utf-8 -*-
"""把头像转成 ASCII 缩略图，用来肉眼确认构图（头/脸/条/背景位置）。"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "_avatar"

RAMP = " .:-=+*#%@"


def ascii_art(im: Image.Image, cols: int = 60) -> str:
    rows = cols * 2 // 3
    small = im.convert("L").resize((cols, rows), Image.LANCZOS)
    px = small.load()
    lines = []
    for y in range(rows):
        line = ""
        for x in range(cols):
            v = px[x, y]
            line += RAMP[min(len(RAMP) - 1, (255 - v) * len(RAMP) // 256)]
        lines.append(line)
    return "\n".join(lines)


def main() -> int:
    for f in sorted(OUT.glob("avatar-*.jpg")):
        im = Image.open(f).convert("RGB")
        print(f"=== {f.name} ===")
        print(ascii_art(im))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
