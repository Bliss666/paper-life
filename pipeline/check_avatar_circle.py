# -*- coding: utf-8 -*-
"""模拟微信圆裁切，验证关键元素（脸、品牌条、logo）没有被切掉。"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "_avatar"
SIZE = 1080
SAFE_R = 490


def circle(im: Image.Image, size: int) -> Image.Image:
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255)
    src = im.convert("RGBA").resize((size, size), Image.LANCZOS)
    out.paste(src, (0, 0), m)
    return out


def main() -> int:
    files = sorted(p for p in OUT.glob("avatar-*.jpg") if "-circle" not in p.stem)
    for f in files:
        im = Image.open(f).convert("RGB")
        c = circle(im, 400)
        cpx = c.load()
        cx = cy = 200
        r = 200

        # 品牌条文字在裁切圆内还剩多少
        # 品牌条 y 726~842（1080 坐标系），换算到 400
        bar_top = int(726 / SIZE * 400)
        bar_bot = int(842 / SIZE * 400)
        half_at_bar = math.sqrt(max(0.0, r * r - ((bar_top + bar_bot) / 2 - cy) ** 2))
        keep = sum(1 for y in range(bar_top, bar_bot)
                   for x in range(int(cx - half_at_bar), int(cx + half_at_bar))
                   if sum(cpx[x, y][:3]) < 200)
        # 脸部墨色
        face = sum(1 for y in range(int(100), int(180)) for x in range(int(120), int(280))
                   if sum(cpx[x, y][:3]) < 600)
        # 头发（最上方）
        hair = sum(1 for y in range(int(10), int(70)) for x in range(int(80), int(320))
                   if sum(cpx[x, y][:3]) < 600)
        # 整圆内容覆盖率
        cover = sum(1 for y in range(0, 400, 2) for x in range(0, 400, 2)
                    if cpx[x, y][3] > 0)
        print(f"{f.stem[-1]}: 圆内品牌条墨色 {keep:>6}  脸部墨色 {face:>5}  "
              f"顶部头发 {hair:>5}  圆内覆盖率 {cover / (200 * 200):.3f}")
        c.convert("RGB").save(OUT / f"{f.stem}-circle.jpg", "JPEG", quality=95)

    # 拼一个「微信列表模拟」预览
    sheet = Image.new("RGB", (1080, 460), (247, 247, 247))
    sd = ImageDraw.Draw(sheet)
    from panels import fb  # noqa: E402
    f = fb(26)
    for i, fp in enumerate(files):
        a = Image.open(fp).convert("RGB")
        cc = circle(a, 120)
        sheet.paste(cc, (40 + i * 350, 40), cc)
        sd.text((40 + i * 350, 175), fp.stem[-1] + "  (120px 圆)", fill=(40, 40, 40), font=f)
        # 列表小尺寸
        small = circle(a, 48)
        sheet.paste(small, (40 + i * 350 + 150, 60), small)
        sd.text((40 + i * 350 + 130, 190), "48px", fill=(150, 150, 150), font=f)
    sheet.save(OUT / "_wechat_preview.jpg", "JPEG", quality=95)
    print(f"\n微信模拟预览 → {OUT / '_wechat_preview.jpg'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
