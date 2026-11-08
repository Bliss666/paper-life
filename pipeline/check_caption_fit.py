# -*- coding: utf-8 -*-
"""检查字幕文案在框里会不会溢出 / 换行太多。

字幕框：面板宽度减去内边距，正文字号 42。中文按字号等宽估算。
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from PIL import ImageFont  # noqa: E402

W = 1080
M = 52
CAP_H = 118
SIZE = 42
PAD = int(24 * (SIZE / 42))


def font():
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc"):
        if Path(p).exists():
            return ImageFont.truetype(p, SIZE)
    return ImageFont.load_default()


def main() -> int:
    data = yaml.safe_load((ROOT / "content" / "skills.yml").read_text(encoding="utf-8"))
    f = font()
    max_w = W - M * 2 - PAD * 2
    print(f"字幕框可用宽度 {max_w}px  字号 {SIZE}\n")

    over = []
    lines_over = []
    for s in data["skills"]:
        for key in ("top", "bottom"):
            text = s[key].replace("*", "")
            w = f.getlength(text)
            # 估算行数（贪心按字号切）
            lines = 1
            cur = 0.0
            for ch in text:
                cw = f.getlength(ch)
                if cur + cw > max_w:
                    lines += 1
                    cur = cw
                else:
                    cur += cw
            if w > max_w * 1.35:
                over.append((s["id"], key, round(w), round(max_w), lines))
            if lines > 2:
                lines_over.append((s["id"], key, lines, round(w)))

    print(f"宽度明显超出的：{len(over)}")
    for row in over[:12]:
        print("   ", row)
    print(f"\n超过两行的：{len(lines_over)}")
    for row in lines_over[:12]:
        print("   ", row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
