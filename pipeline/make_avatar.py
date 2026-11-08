# -*- coding: utf-8 -*-
"""生成微信视频号头像 —— 《纸上人生》动漫风格。

设计要点（针对"头像会被缩到很小"这个现实）：
  · 大头构图，脸占画面 55% 以上，缩到 40px 还能认出表情
  · 暖橙渐变底 + 白色聚光圆 + 冲击线，保证小尺寸下的对比度
  · 所有元素收在中心圆内（微信头像按圆裁切），四角不放关键信息
  · 底部漫画黑条写账号名「纸上人生」，下面一行小字 ThinkNote

用法：
    python pipeline/make_avatar.py            # 输出 3 个变体 + 预览图
    python pipeline/make_avatar.py --pick A   # 只看某个变体
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from actor import (OUTLINE, HAIR, HAIR_HI, draw_face, draw_hair,  # noqa: E402
                   _hair_strands, _mix_outline, _light_soft, shade, tint)
from panels import fb, fr  # noqa: E402

SIZE = 1080
ASSETS = ROOT / "assets"
OUT = ROOT / "out" / "_avatar"

# 头像安全区：微信按圆裁切，中心 (540,540)，半径 490
SAFE_R = 490


# ── 工具 ────────────────────────────────────────────────
def _mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def _vgrad(im, top, bot):
    d = ImageDraw.Draw(im)
    for y in range(im.height):
        t = y / max(1, im.height - 1)
        d.line([(0, y), (im.width, y)],
               fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))


def _halftone(im, seed=3, alpha=42):
    """漫画网点，覆盖在上层做质感。"""
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    step = 17
    for yy in range(0, im.height + step, step):
        for xx in range(0, im.width + step, step):
            r = rnd.uniform(1.6, 3.4)
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(70, 56, 44, alpha))
    return Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")


def _speed_lines(im, cx, cy, color=(255, 255, 255), alpha=70, count=54, seed=11):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    maxr = int(math.hypot(*im.size) * 0.62)
    for i in range(count):
        a = (i / count) * math.tau + rnd.uniform(-0.04, 0.04)
        r0 = maxr * rnd.uniform(0.26, 0.40)
        d.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                (cx + math.cos(a) * maxr, cy + math.sin(a) * maxr)],
               fill=color + (alpha,), width=rnd.choice((4, 6, 9, 13)))
    return Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")


def _burst(d, cx, cy, r, fill=(255, 255, 255), outline=(34, 30, 28), n=20, seed=5):
    """漫画集中爆炸框（背景）。"""
    rnd = random.Random(seed)
    pts = []
    for i in range(n * 2):
        a = math.pi * i / n - math.pi / 2
        k = 1.0 if i % 2 == 0 else rnd.uniform(0.80, 0.90)
        pts.append((cx + math.cos(a) * r * k, cy + math.sin(a) * r * k * 0.96))
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=outline, width=7, joint="curve")


def _sparkle(d, cx, cy, r, fill=(255, 248, 210), outline=(224, 176, 52)):
    d.polygon([(cx, cy - r), (cx + r * 0.20, cy - r * 0.20), (cx + r, cy),
               (cx + r * 0.20, cy + r * 0.20), (cx, cy + r),
               (cx - r * 0.20, cy + r * 0.20), (cx - r, cy),
               (cx - r * 0.20, cy - r * 0.20)], fill=fill, outline=outline, width=4)


def _bulb(d, cx, cy, s):
    """小灯泡道具。"""
    d.ellipse([cx - 46 * s, cy - 66 * s, cx + 46 * s, cy + 26 * s],
              fill=(255, 240, 150), outline=OUTLINE, width=6)
    d.rectangle([cx - 17 * s, cy + 22 * s, cx + 17 * s, cy + 52 * s],
                fill=(190, 190, 200), outline=OUTLINE, width=5)
    for i in range(3):
        d.line([(cx - 15 * s, cy + 30 * s + i * 10 * s), (cx + 15 * s, cy + 30 * s + i * 10 * s)],
               fill=OUTLINE, width=3)
    d.ellipse([cx - 26 * s, cy - 46 * s, cx - 4 * s, cy - 26 * s], fill=(255, 255, 255))


def _book(d, cx, cy, s):
    """小书本道具。"""
    d.polygon([(cx - 54 * s, cy - 44 * s), (cx, cy - 54 * s), (cx + 54 * s, cy - 44 * s),
               (cx + 54 * s, cy + 6 * s), (cx, cy - 4 * s), (cx - 54 * s, cy + 6 * s)],
              fill=(255, 252, 242), outline=OUTLINE, width=6)
    d.line([(cx, cy - 54 * s), (cx, cy - 4 * s)], fill=OUTLINE, width=5)


def _clock(d, cx, cy, s):
    """小闹钟道具。"""
    d.ellipse([cx - 46 * s, cy - 50 * s, cx + 46 * s, cy + 42 * s],
              fill=(255, 250, 238), outline=OUTLINE, width=6)
    d.line([(cx, cy - 4 * s), (cx, cy - 30 * s)], fill=OUTLINE, width=6)
    d.line([(cx, cy - 4 * s), (cx + 20 * s, cy + 8 * s)], fill=OUTLINE, width=5)
    d.ellipse([cx - 56 * s, cy - 60 * s, cx - 26 * s, cy - 34 * s], fill=(206, 130, 110), outline=OUTLINE, width=4)
    d.ellipse([cx + 26 * s, cy - 60 * s, cx + 56 * s, cy - 34 * s], fill=(206, 130, 110), outline=OUTLINE, width=4)


def _notebook(d, cx, cy, s):
    """小笔记本道具。"""
    d.polygon([(cx - 46 * s, cy - 40 * s), (cx + 46 * s, cy - 48 * s),
               (cx + 46 * s, cy + 4 * s), (cx - 46 * s, cy + 12 * s)],
              fill=(255, 253, 246), outline=OUTLINE, width=6)
    for i in range(3):
        d.line([(cx - 30 * s, cy - 26 * s + i * 14 * s), (cx + 26 * s, cy - 30 * s + i * 14 * s)],
               fill=(160, 150, 138), width=4)


def _exclaim(d, cx, cy, s):
    """漫画惊叹号标牌。"""
    w = int(96 * s)
    h = int(190 * s)
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2],
                        radius=int(22 * s), fill=(255, 214, 66), outline=OUTLINE, width=7)
    f = fb(int(140 * s))
    tw = d.textlength("!", font=f)
    d.text((cx - tw / 2, cy - h * 0.34), "!", fill=(214, 62, 44), font=f,
           stroke_width=max(3, int(11 * s)), stroke_fill=OUTLINE)


# ── 大头角色 ────────────────────────────────────────────
def draw_bust(d, cx, head_cy, r, *, mood="think", hair="short",
              shirt=(96, 138, 186), skin=(253, 222, 188), look=0):
    """头像用的半身像：肩 + 脖 + 大头。"""
    lw = max(5, int(r * 0.075))

    # 肩膀（圆厚躯干）
    d.ellipse([cx - r * 1.62, head_cy + r * 1.02, cx + r * 1.62, head_cy + r * 3.6],
              fill=shirt, outline=OUTLINE, width=lw)
    # 暗部
    d.chord([cx - r * 1.62, head_cy + r * 1.02, cx + r * 1.62, head_cy + r * 3.6],
            15, 95, fill=shade(shirt, 0.78))
    # 领口
    d.polygon([(cx - r * 0.30, head_cy + r * 1.10), (cx + r * 0.30, head_cy + r * 1.10),
               (cx, head_cy + r * 1.62)], fill=skin, outline=OUTLINE, width=max(3, int(lw * 0.75)))
    # 脖子
    d.rectangle([cx - r * 0.30, head_cy + r * 0.62, cx + r * 0.30, head_cy + r * 1.24],
                fill=shade(skin, 0.90), outline=OUTLINE, width=lw)

    # 头
    d.ellipse([cx - r, head_cy - r, cx + r, head_cy + r], fill=skin, outline=OUTLINE, width=lw)
    # 耳朵
    d.ellipse([cx - r * 1.10, head_cy - r * 0.02, cx - r * 0.84, head_cy + r * 0.32],
              fill=skin, outline=OUTLINE, width=max(3, int(lw * 0.8)))
    d.ellipse([cx + r * 0.84, head_cy - r * 0.02, cx + r * 1.10, head_cy + r * 0.32],
              fill=skin, outline=OUTLINE, width=max(3, int(lw * 0.8)))

    # 头发
    draw_hair(d, cx, head_cy, r, hair)
    _hair_strands(d, cx, head_cy, r, hair)

    # 五官
    eye_y = head_cy + r * 0.12
    draw_face(d, cx, eye_y, r, mood, look)

    # 鼻尖
    if mood != "sleep":
        d.line([(cx, eye_y + r * 0.22), (cx + r * 0.06, eye_y + r * 0.30)],
               fill=_mix_outline(skin), width=max(2, int(lw * 0.42)))
    # 腮红
    if mood in ("happy", "joy", "smug", "cry", "rage"):
        blush = (240, 148, 138) if mood != "rage" else (238, 120, 108)
        for sgn in (-1, 1):
            bx = cx + sgn * r * 0.64
            by = eye_y + r * 0.34
            for k in range(3):
                rr = r * (0.14 + k * 0.05)
                d.ellipse([bx - rr, by - rr * 0.62, bx + rr, by + rr * 0.62],
                          fill=blush if k == 0 else _light_soft(blush))

    # 漫画符号
    if mood == "think":
        f = fb(int(r * 0.70))
        d.text((cx + r * 0.90, head_cy - r * 1.30), "?", fill=(70, 62, 56), font=f)
    elif mood in ("rage", "angry"):
        for ang in (-30, 30):
            a = math.radians(ang)
            bx = cx + r * 1.28 + math.cos(a) * r * 0.16
            by = head_cy - r * 0.98 + math.sin(a) * r * 0.16
            d.line([(bx - r * 0.11, by - r * 0.11), (bx + r * 0.11, by + r * 0.11)],
                   fill=(214, 66, 58), width=max(4, int(r * 0.055)))
    elif mood in ("tired", "cold", "calm"):
        sx, sy = cx - r * 1.08, head_cy + r * 0.34
        d.ellipse([sx - r * 0.075, sy - r * 0.11, sx + r * 0.075, sy + r * 0.09],
                  fill=(140, 200, 238), outline=OUTLINE, width=max(3, int(r * 0.030)))
        d.polygon([(sx - r * 0.075, sy - r * 0.02), (sx + r * 0.075, sy - r * 0.02),
                   (sx, sy - r * 0.18)], fill=(140, 200, 238))


# ── 品牌条 ──────────────────────────────────────────────
def draw_brand_bar(d, name="纸上人生", sub="ThinkNote · thinknote.pro"):
    """底部漫画黑条 + 副标题。

    宽度按安全圆计算：条所在 y 处的圆弧宽度必须容得下整条，
    否则微信圆裁切会把两端切掉。
    """
    cx = SIZE // 2
    cy = SIZE // 2
    by = 726          # 条顶
    bh = 116
    bar_cy = by + bh // 2
    # 该高度上安全圆允许的最大半宽
    max_half = int(math.sqrt(max(0.0, SAFE_R ** 2 - (bar_cy - cy) ** 2))) - 26
    bw = min(660, max_half * 2)
    bx = cx - bw // 2

    # 硬投影
    d.rectangle([bx + 9, by + 9, bx + bw + 9, by + bh + 9], fill=(96, 62, 40))
    # 黑底
    d.rectangle([bx, by, bx + bw, by + bh], fill=(34, 30, 28))
    # 顶部色条
    d.rectangle([bx, by, bx + bw, by + 9], fill=(255, 214, 66))
    # 账号名
    f = fb(78)
    tw = d.textlength(name, font=f)
    d.text((cx - tw / 2, by + 14), name, fill=(255, 255, 255), font=f)
    # 副标题
    fs = fr(26)
    ts = d.textlength(sub, font=fs)
    d.text((cx - ts / 2, by + 96), sub, fill=(186, 176, 164), font=fs)


def draw_logo(d):
    """ThinkNote logo（右下角小尺寸）。"""
    p = ASSETS / "ThinkNote-logo.png"
    if not p.exists():
        return
    lg = Image.open(p).convert("RGBA").resize((64, 64), Image.LANCZOS)
    return lg


# ── 变体 ────────────────────────────────────────────────
VARIANTS = {
    "A": {
        "name": "纸上人生",
        "mood": "think",
        "hair": "short",
        "shirt": (96, 138, 186),
        "sky": ((255, 214, 96), (250, 138, 66)),
        "spot": (255, 252, 236),
        "props": [("bulb", 0.205, 0.28), ("book", 0.795, 0.31)],
        "exclaim": False,
    },
    "B": {
        "name": "纸上人生",
        "mood": "joy",
        "hair": "bun",
        "shirt": (226, 96, 92),
        "sky": ((255, 196, 84), (246, 118, 92)),
        "spot": (255, 250, 224),
        "props": [("clock", 0.195, 0.29), ("notebook", 0.805, 0.32)],
        "exclaim": True,
    },
    "C": {
        "name": "纸上人生",
        "mood": "smug",
        "hair": "middle",
        "shirt": (112, 168, 132),
        "sky": ((255, 220, 120), (246, 158, 78)),
        "spot": (255, 253, 240),
        "props": [("notebook", 0.205, 0.29), ("clock", 0.795, 0.28)],
        "exclaim": False,
    },
}

PROP_FN = {"bulb": _bulb, "book": _book, "clock": _clock, "notebook": _notebook}


def render(variant: dict, size: int = SIZE) -> Image.Image:
    im = Image.new("RGB", (size, size))
    _vgrad(im, *variant["sky"])

    cx = size // 2
    cy = size // 2
    k = size / SIZE

    # 放射速度线
    im = _speed_lines(im, cx, int(cy * 0.86), alpha=72, count=58, seed=13)
    d = ImageDraw.Draw(im)

    # 白色聚光圆 + 冲击框
    r_spot = int(size * 0.345)
    _burst(d, cx, int(size * 0.41), r_spot, fill=variant["spot"], n=22, seed=7)
    d.ellipse([cx - r_spot * 0.90, int(size * 0.41) - r_spot * 0.90,
               cx + r_spot * 0.90, int(size * 0.41) + r_spot * 0.90],
              fill=variant["spot"], outline=(34, 30, 28), width=max(4, int(7 * k)))
    # 聚光圆内的浅网点
    im = _halftone(im, seed=9, alpha=26)
    d = ImageDraw.Draw(im)

    # 角色
    head_cy = int(size * 0.405)
    head_r = int(size * 0.235)
    draw_bust(d, cx, head_cy, head_r,
              mood=variant["mood"], hair=variant["hair"], shirt=variant["shirt"])

    # 小道具
    for name, fx, fy in variant["props"]:
        fn = PROP_FN.get(name)
        if fn:
            fn(d, int(size * fx), int(size * fy), 1.05 * k)

    # 漫画符号
    if variant["exclaim"]:
        _exclaim(d, int(size * 0.790), int(size * 0.190), 1.0 * k)
    else:
        _sparkle(d, int(size * 0.790), int(size * 0.200), 44 * k)
        _sparkle(d, int(size * 0.190), int(size * 0.185), 30 * k)

    # 品牌条
    if size == SIZE:
        draw_brand_bar(d, variant["name"])
    else:
        # 缩略版也画个简版条
        bw, bh = int(600 * k), int(116 * k)
        bx = (size - bw) // 2
        by = int(726 * k)
        d.rectangle([bx, by, bx + bw, by + bh], fill=(34, 30, 28))
        d.rectangle([bx, by, bx + bw, by + max(2, int(9 * k))], fill=(255, 214, 66))
        f = fb(max(10, int(78 * k)))
        tw = d.textlength(variant["name"], font=f)
        d.text(((size - tw) / 2, by + 14 * k), variant["name"], fill=(255, 255, 255), font=f)

    # logo（放在安全圆内，靠近左下）
    lg = draw_logo(d)
    if lg:
        lx = cx - int(size * 0.30)
        ly = int(size * 0.615)
        im.paste(lg, (lx, ly), lg)

    # 圆角（微信本身会裁圆，这里给个方图）
    return im


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    only = None
    if "--pick" in sys.argv:
        only = sys.argv[sys.argv.index("--pick") + 1].upper()

    made = []
    for key, v in VARIANTS.items():
        if only and key != only:
            continue
        im = render(v)
        p = OUT / f"avatar-{key}.jpg"
        im.save(p, "JPEG", quality=95)
        made.append((key, p))
        print(f"  {key} → {p}")

    # 预览图（三个变体并排 + 缩略尺寸模拟）
    if len(made) > 1:
        sheet = Image.new("RGB", (1080, 420), (246, 243, 234))
        sd = ImageDraw.Draw(sheet)
        f = fb(26)
        for i, (key, p) in enumerate(made):
            a = Image.open(p).convert("RGB")
            big = a.resize((400, 400), Image.LANCZOS)
            sheet.paste(big, (20 + i * 415, 10))
            # 小尺寸模拟（微信列表里就那么大）
            small = a.resize((64, 64), Image.LANCZOS)
            sheet.paste(small, (20 + i * 415 + 340, 20))
            sd.text((20 + i * 415, 12), key, fill=(40, 34, 30), font=f)
        sheet.save(OUT / "_preview.jpg", "JPEG", quality=95)
        print(f"  预览 → {OUT / '_preview.jpg'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
