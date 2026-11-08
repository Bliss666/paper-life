# -*- coding: utf-8 -*-
"""原创角色库 v3 —— 动漫赛璐璐风格。

造型语言（自建，不参考任何现成 IP）：
  · 大头小身，赛璐璐平涂 + 一层暗部，不做渐变
  · 大眼睛：瞳孔 + 双高光 + 上眼睑粗线（动漫眼的标准结构）
  · 动漫发型：尖角块面 + 高光条
  · 表情靠眉眼嘴的形状切换，配合漫画符号（汗滴 / 怒气 / 问号）
  · 轮廓用深色描边，线宽统一

配色：衣服是纯色块（这是动漫感的关键），暗部用同色压深。
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import ImageFont

OUTLINE = (46, 38, 34)
INK = (38, 33, 28)

_FONT_CACHE: dict[int, ImageFont.FreeTypeFont] = {}


def _font(size: int, bold: bool = True):
    global _FONT_CACHE
    key = (size, bold)
    if key not in _FONT_CACHE:
        p = Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc")
        if not p.exists():
            p = Path("C:/Windows/Fonts/msyhbd.ttc")
        _FONT_CACHE[key] = ImageFont.truetype(str(p), size)
    return _FONT_CACHE[key]


def shade(c, k=0.76):
    """压暗做暗部。"""
    return tuple(max(0, min(255, int(v * k))) for v in c)


def tint(c, k=1.18):
    """提亮做高光。"""
    return tuple(max(0, min(255, int(v * k))) for v in c)


def _mix_outline(c, k=0.72):
    """把颜色往描边色方向压暗一点点（用于鼻线等极淡细节）。"""
    return tuple(int(a * k + b * (1 - k)) for a, b in zip(c, OUTLINE))


def _light_soft(c, k=1.0):
    """更淡的腮红（第二层，制造渐变感）。"""
    return tuple(min(255, int(v + (255 - v) * 0.45 * k)) for v in c)


# ── 动漫眼 ──────────────────────────────────────────────
def anime_eye(draw, x, y, w, h, mood="neutral", look=0, flip=1):
    """动漫眼：大椭圆 + 虹膜 + 双高光。x,y = 眼中心。"""
    ow, oh = w, h
    # 眼白
    draw.ellipse([x - ow / 2, y - oh / 2, x + ow / 2, y + oh / 2], fill=(255, 255, 255))
    # 虹膜（大，占满）
    ir = min(ow, oh) * 0.44
    ix = x + look * ow * 0.16
    draw.ellipse([ix - ir, y - ir, ix + ir, y + ir], fill=(74, 132, 214))
    draw.ellipse([ix - ir, y - ir, ix + ir, y + ir * 0.35], fill=(112, 176, 238))
    # 虹膜放射纹（细腻度）
    for i in range(6):
        a = math.tau * i / 6 + 0.3
        d2 = ir * 0.88
        draw.line([(ix + math.cos(a) * ir * 0.34, y + math.sin(a) * ir * 0.34),
                   (ix + math.cos(a) * d2, y + math.sin(a) * d2)],
                  fill=(58, 110, 186), width=1)
    # 瞳孔
    draw.ellipse([ix - ir * 0.44, y - ir * 0.56, ix + ir * 0.44, y + ir * 0.56], fill=(30, 30, 44))
    # 高光：上主光 + 下小光
    draw.ellipse([ix - ir * 0.52, y - ir * 0.62, ix - ir * 0.06, y - ir * 0.16], fill=(255, 255, 255))
    draw.ellipse([ix + ir * 0.10, y + ir * 0.18, ix + ir * 0.36, y + ir * 0.46], fill=(255, 255, 255))
    # 上眼睑（粗线，压住虹膜上沿）
    lw = max(2, int(h * 0.17))
    draw.arc([x - ow / 2, y - oh / 2, x + ow / 2, y + oh / 2], 180, 360, fill=OUTLINE, width=lw)
    # 睫毛（细腻度：外眼角一小撮）
    draw.line([(x + ow / 2 - 1, y - oh * 0.28), (x + ow / 2 + ow * 0.13, y - oh * 0.42)],
              fill=OUTLINE, width=max(2, int(h * 0.09)))
    # 下眼睑（细）
    draw.arc([x - ow / 2, y - oh / 2, x + ow / 2, y + oh / 2], 20, 160, fill=OUTLINE, width=max(1, int(h * 0.07)))


def draw_face(draw, cx, cy, r, mood="neutral", look=0):
    """动漫五官。cy = 眼睛高度，r = 头半径。"""
    ex = r * 0.40
    ew = r * 0.40
    eh = r * 0.46

    # 眉毛
    lw = max(3, int(r * 0.10))
    if mood in ("sad", "cry"):
        for sgn in (-1, 1):
            x = cx + sgn * ex
            draw.line([(x - ew * 0.62, cy - eh * 0.86), (x + ew * 0.62, cy - eh * 1.10)], fill=HAIR, width=lw)
    elif mood in ("rage", "angry"):
        draw.line([(cx - ex - ew * 0.6, cy - eh * 0.80), (cx - ex + ew * 0.62, cy - eh * 1.18)], fill=HAIR, width=lw)
        draw.line([(cx + ex - ew * 0.62, cy - eh * 1.18), (cx + ex + ew * 0.6, cy - eh * 0.80)], fill=HAIR, width=lw)
    elif mood in ("think", "smug"):
        draw.line([(cx - ex - ew * 0.6, cy - eh * 1.02), (cx - ex + ew * 0.6, cy - eh * 0.90)], fill=HAIR, width=lw)
        draw.line([(cx + ex - ew * 0.6, cy - eh * 0.90), (cx + ex + ew * 0.6, cy - eh * 1.02)], fill=HAIR, width=lw)
    elif mood == "happy":
        for sgn in (-1, 1):
            x = cx + sgn * ex
            draw.arc([x - ew * 0.62, cy - eh * 1.5, x + ew * 0.62, cy - eh * 0.2], 190, 350, fill=HAIR, width=lw)

    # 眼睛
    if mood in ("happy", "joy"):
        for sgn in (-1, 1):
            x = cx + sgn * ex
            draw.arc([x - ew * 0.62, cy - eh * 0.55, x + ew * 0.62, cy + eh * 0.55], 190, 350, fill=OUTLINE, width=max(3, int(r * 0.10)))
    elif mood in ("tired", "sleep"):
        for sgn in (-1, 1):
            x = cx + sgn * ex
            draw.line([(x - ew * 0.55, cy), (x + ew * 0.55, cy)], fill=OUTLINE, width=max(3, int(r * 0.09)))
    elif mood in ("cold", "calm", "flat"):
        for sgn in (-1, 1):
            x = cx + sgn * ex
            draw.ellipse([x - ew * 0.40, cy - eh * 0.44, x + ew * 0.40, cy + eh * 0.44], fill=OUTLINE)
            draw.ellipse([x - ew * 0.40 + look * ew * 0.12, cy - eh * 0.44, x + ew * 0.40 + look * ew * 0.12, cy + eh * 0.44], fill=(255, 255, 255))
    elif mood == "cry":
        for sgn in (-1, 1):
            x = cx + sgn * ex
            anime_eye(draw, x, cy, ew, eh, mood, look)
        draw.ellipse([cx - ex - ew * 0.42, cy + eh * 0.42, cx - ex + ew * 0.10, cy + eh * 1.30], fill=(126, 192, 238))
    else:
        for sgn in (-1, 1):
            x = cx + sgn * ex
            anime_eye(draw, x, cy, ew, eh, mood, look)

    # 嘴（动漫嘴：小圆/小三角/弧线）
    my = cy + r * 0.50
    if mood in ("happy", "joy"):
        draw.arc([cx - r * 0.26, my - r * 0.24, cx + r * 0.26, my + r * 0.30], 10, 170, fill=OUTLINE, width=max(2, int(r * 0.075)))
        if mood == "joy":
            draw.pieslice([cx - r * 0.20, my - r * 0.02, cx + r * 0.20, my + r * 0.34], 0, 180, fill=(196, 88, 92))
    elif mood in ("sad", "cry"):
        draw.arc([cx - r * 0.22, my - r * 0.04, cx + r * 0.22, my + r * 0.38], 200, 340, fill=OUTLINE, width=max(2, int(r * 0.075)))
    elif mood in ("rage", "angry"):
        draw.rectangle([cx - r * 0.16, my - r * 0.06, cx + r * 0.16, my + r * 0.24], fill=(150, 66, 62), outline=OUTLINE, width=max(2, int(r * 0.06)))
    elif mood in ("tired", "sleep"):
        draw.ellipse([cx - r * 0.09, my - r * 0.02, cx + r * 0.09, my + r * 0.16], outline=OUTLINE, width=max(2, int(r * 0.06)))
    elif mood in ("cold", "flat", "calm"):
        draw.line([(cx - r * 0.16, my), (cx + r * 0.16, my)], fill=OUTLINE, width=max(2, int(r * 0.07)))
    elif mood == "think":
        draw.line([(cx - r * 0.12, my + r * 0.04), (cx + r * 0.16, my - r * 0.06)], fill=OUTLINE, width=max(2, int(r * 0.07)))
    elif mood == "smug":
        draw.arc([cx - r * 0.22, my - r * 0.16, cx + r * 0.22, my + r * 0.16], 12, 160, fill=OUTLINE, width=max(2, int(r * 0.07)))
    else:
        draw.line([(cx - r * 0.13, my), (cx + r * 0.13, my)], fill=OUTLINE, width=max(2, int(r * 0.07)))


# ── 动漫发型 ────────────────────────────────────────────
HAIR = (62, 48, 92)      # 紫棕，动漫常用发色
HAIR_HI = (126, 104, 168)


def _hair_strands(draw, cx, cy, r, style="short"):
    """发丝细节：几根细发丝线，让头发不那么"块面感"。"""
    if style == "bald":
        return
    col = _mix_outline(HAIR_HI, 0.55)
    if style in ("short", "middle", "bun", "pony"):
        for k, (ox, oy, ln, ang) in enumerate((
            (-0.55, -0.72, 0.42, 0.55),
            (-0.18, -0.82, 0.50, 0.30),
            (0.24, -0.78, 0.44, 0.20),
            (0.56, -0.62, 0.36, -0.15),
        )):
            x0 = cx + ox * r
            y0 = cy + oy * r
            draw.line([(x0, y0),
                       (x0 + math.sin(ang) * ln * r * 0.7, y0 + ln * r * 0.55)],
                      fill=col, width=max(1, int(r * 0.035)))
    elif style == "curly":
        for k in range(6):
            a = math.pi + k * (math.pi / 5)
            x0 = cx + math.cos(a) * r * 0.72
            y0 = cy + math.sin(a) * r * 0.72
            draw.arc([x0 - r * 0.24, y0 - r * 0.24, x0 + r * 0.24, y0 + r * 0.24],
                     0, 260, fill=col, width=max(1, int(r * 0.035)))
    elif style == "long":
        for k, ox in enumerate((-0.70, -0.36, 0.30, 0.64)):
            x0 = cx + ox * r
            y0 = cy - r * 0.20
            draw.line([(x0, y0), (x0 + ox * r * 0.30, y0 + r * 0.95)],
                      fill=col, width=max(1, int(r * 0.035)))


def draw_hair(draw, cx, cy, r, style="short"):
    """块面动漫发：尖角 + 高光条。"""
    if style == "bald":
        return
    if style == "short":
        # 主体块面
        draw.chord([cx - r * 1.06, cy - r * 1.16, cx + r * 1.06, cy + r * 0.42], 180, 360, fill=HAIR)
        # 侧发
        draw.polygon([(cx - r * 1.06, cy - r * 0.30), (cx - r * 0.72, cy - r * 0.42),
                      (cx - r * 0.78, cy + r * 0.34), (cx - r * 1.10, cy + r * 0.10)], fill=HAIR)
        draw.polygon([(cx + r * 1.06, cy - r * 0.30), (cx + r * 0.72, cy - r * 0.42),
                      (cx + r * 0.78, cy + r * 0.34), (cx + r * 1.10, cy + r * 0.10)], fill=HAIR)
        # 刘海尖角
        draw.polygon([(cx - r * 1.02, cy - r * 0.22), (cx - r * 0.30, cy - r * 0.46),
                      (cx + r * 0.16, cy - r * 0.20), (cx - r * 0.55, cy - r * 0.02)], fill=HAIR)
        # 高光条
        draw.polygon([(cx - r * 0.50, cy - r * 1.02), (cx + r * 0.16, cy - r * 1.08),
                      (cx + r * 0.02, cy - r * 0.86), (cx - r * 0.56, cy - r * 0.80)], fill=HAIR_HI)
    elif style == "bun":
        draw.chord([cx - r * 1.06, cy - r * 1.16, cx + r * 1.06, cy + r * 0.42], 180, 360, fill=HAIR)
        draw.ellipse([cx - r * 0.40, cy - r * 1.54, cx + r * 0.40, cy - r * 0.76], fill=HAIR)
        draw.polygon([(cx - r * 1.02, cy - r * 0.22), (cx - r * 0.24, cy - r * 0.50),
                      (cx + r * 0.20, cy - r * 0.18), (cx - r * 0.60, cy - r * 0.02)], fill=HAIR)
        draw.polygon([(cx - r * 0.44, cy - r * 1.04), (cx + r * 0.18, cy - r * 1.10),
                      (cx + r * 0.04, cy - r * 0.88), (cx - r * 0.50, cy - r * 0.82)], fill=HAIR_HI)
    elif style == "middle":
        draw.chord([cx - r * 1.08, cy - r * 1.18, cx + r * 1.08, cy + r * 0.38], 180, 360, fill=HAIR)
        draw.polygon([(cx - r * 0.06, cy - r * 1.18), (cx + r * 0.10, cy - r * 1.18),
                      (cx + r * 0.08, cy - r * 0.42), (cx - r * 0.04, cy - r * 0.42)], fill=(253, 222, 188))
        draw.polygon([(cx - r * 1.02, cy - r * 0.24), (cx - r * 0.34, cy - r * 0.48),
                      (cx - r * 0.10, cy - r * 0.10), (cx - r * 0.72, cy - r * 0.10)], fill=HAIR)
        draw.polygon([(cx - r * 0.40, cy - r * 1.04), (cx + r * 0.22, cy - r * 1.10),
                      (cx + r * 0.06, cy - r * 0.88), (cx - r * 0.46, cy - r * 0.82)], fill=HAIR_HI)
    elif style == "curly":
        for i in range(8):
            a = math.pi + i * (math.pi / 7)
            hx = cx + math.cos(a) * r * 0.94
            hy = cy + math.sin(a) * r * 0.94
            draw.ellipse([hx - r * 0.34, hy - r * 0.34, hx + r * 0.34, hy + r * 0.34], fill=HAIR)
        draw.chord([cx - r * 1.02, cy - r * 1.06, cx + r * 1.02, cy + r * 0.30], 180, 360, fill=HAIR)
        draw.polygon([(cx - r * 0.96, cy - r * 0.24), (cx - r * 0.30, cy - r * 0.46),
                      (cx + r * 0.14, cy - r * 0.18), (cx - r * 0.62, cy - r * 0.00)], fill=HAIR)
    elif style == "pony":
        draw.chord([cx - r * 1.06, cy - r * 1.16, cx + r * 1.06, cy + r * 0.42], 180, 360, fill=HAIR)
        draw.polygon([(cx + r * 0.74, cy - r * 0.42), (cx + r * 1.36, cy - r * 0.10),
                      (cx + r * 1.24, cy + r * 0.94), (cx + r * 0.82, cy + r * 0.60)], fill=HAIR)
        draw.polygon([(cx - r * 1.00, cy - r * 0.22), (cx - r * 0.28, cy - r * 0.48),
                      (cx + r * 0.18, cy - r * 0.16), (cx - r * 0.58, cy - r * 0.00)], fill=HAIR)
        draw.polygon([(cx - r * 0.44, cy - r * 1.04), (cx + r * 0.18, cy - r * 1.10),
                      (cx + r * 0.04, cy - r * 0.88), (cx - r * 0.50, cy - r * 0.82)], fill=HAIR_HI)
    elif style == "long":
        draw.chord([cx - r * 1.08, cy - r * 1.18, cx + r * 1.08, cy + r * 0.40], 180, 360, fill=HAIR)
        draw.polygon([(cx - r * 1.08, cy - r * 0.40), (cx - r * 0.72, cy - r * 0.52),
                      (cx - r * 0.80, cy + r * 1.40), (cx - r * 1.20, cy + r * 1.10)], fill=HAIR)
        draw.polygon([(cx + r * 1.08, cy - r * 0.40), (cx + r * 0.72, cy - r * 0.52),
                      (cx + r * 0.80, cy + r * 1.40), (cx + r * 1.20, cy + r * 1.10)], fill=HAIR)
        draw.polygon([(cx - r * 1.00, cy - r * 0.22), (cx - r * 0.30, cy - r * 0.48),
                      (cx + r * 0.18, cy - r - r * 0.16), (cx - r * 0.60, cy - r * 0.00)], fill=HAIR)
        draw.polygon([(cx - r * 0.42, cy - r * 1.06), (cx + r * 0.20, cy - r * 1.12),
                      (cx + r * 0.06, cy - r * 0.90), (cx - r * 0.48, cy - r * 0.84)], fill=HAIR_HI)


# ── 主体 ────────────────────────────────────────────────
def draw_actor(draw, cx, ground_y, *, pose="stand", mood="neutral", hair="short",
               shirt=(96, 138, 186), skin=(253, 222, 188), scale=1.0, look=0,
               prop=None, bubble=None, bubble_kind="speech", bubble_tail="down",
               bubble_text="", bounds=None):
    """动漫角色。"""
    s = scale
    lw = max(3, int(4.4 * s))   # 统一描边宽度

    head_r = 46 * s
    torso_w = 26 * s
    torso_h = 62 * s
    leg_len = 56 * s

    hip_y = ground_y - leg_len
    torso_top = hip_y - torso_h
    head_cy = torso_top - head_r * 0.80
    eye_y = head_cy + head_r * 0.12

    hair_c = HAIR
    skin_d = shade(skin, 0.90)
    shirt_d = shade(shirt, 0.76)

    def out_line(pts, width=None, fill=None, closed=True):
        w = width or lw
        if closed:
            draw.polygon(pts, fill=fill)
            draw.line(list(pts) + [pts[0]], fill=OUTLINE, width=w, joint="curve")
        else:
            draw.line(pts, fill=OUTLINE, width=w, joint="curve")

    # ── 躺 / 趴桌 ──
    if pose in ("lie", "sleep", "collapse"):
        # 身体（平躺块面）
        draw.rounded_rectangle([cx - 150 * s, ground_y - 74 * s, cx - 16 * s, ground_y - 22 * s],
                               radius=24 * s, fill=shirt, outline=OUTLINE, width=lw)
        draw.rounded_rectangle([cx - 196 * s, ground_y - 62 * s, cx - 128 * s, ground_y - 30 * s],
                               radius=16 * s, fill=shirt_d, outline=OUTLINE, width=lw)
        hx, hy = cx + 32 * s, ground_y - 54 * s
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=skin, outline=OUTLINE, width=lw)
        draw_hair(draw, hx, hy, head_r, hair)
        draw_face(draw, hx, hy + head_r * 0.14, head_r, "sleep", look)
        # Z
        draw.text((hx + 52 * s, hy - 66 * s), "Z", fill=(120, 112, 104), font=_font(int(30 * s)))
        draw.text((hx + 86 * s, hy - 96 * s), "Z", fill=(120, 112, 104), font=_font(int(22 * s)))
        if bubble:
            _maybe_bubble(draw, bubble, bubble_kind, bubble_tail, bubble_text,
                          cx + 40 * s, hy - head_r * 0.8, head_r, torso_w, s, bounds)
        return

    if pose == "desk":
        draw.rounded_rectangle([cx - 130 * s, ground_y - 44 * s, cx + 30 * s, ground_y - 18 * s],
                               radius=10 * s, fill=(228, 214, 186), outline=OUTLINE, width=lw)
        draw.rounded_rectangle([cx - 116 * s, ground_y - 128 * s, cx - 26 * s, ground_y - 46 * s],
                               radius=22 * s, fill=shirt, outline=OUTLINE, width=lw)
        hx, hy = cx - 132 * s, ground_y - 96 * s
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=skin, outline=OUTLINE, width=lw)
        draw_hair(draw, hx, hy, head_r, hair)
        draw_face(draw, hx, hy + head_r * 0.14, head_r, "sleep", look)
        if bubble:
            _maybe_bubble(draw, bubble, bubble_kind, bubble_tail, bubble_text,
                          hx + 30 * s, hy - head_r * 0.8, head_r, torso_w, s, bounds)
        return

    # ── 腿 ──
    if pose == "run":
        draw.line([(cx - 8 * s, hip_y), (cx - 56 * s, ground_y - 4 * s)], fill=shirt_d, width=int(22 * s))
        draw.line([(cx + 8 * s, hip_y), (cx + 60 * s, ground_y)], fill=shirt_d, width=int(22 * s))
    elif pose == "walk":
        draw.line([(cx - 6 * s, hip_y), (cx - 34 * s, ground_y)], fill=shirt_d, width=int(22 * s))
        draw.line([(cx + 6 * s, hip_y), (cx + 36 * s, ground_y)], fill=shirt_d, width=int(22 * s))
    elif pose == "sit":
        draw.line([(cx, hip_y), (cx + 54 * s, hip_y + 8 * s)], fill=shirt_d, width=int(22 * s))
        draw.line([(cx + 54 * s, hip_y + 8 * s), (cx + 54 * s, ground_y)], fill=shirt_d, width=int(22 * s))
        draw.line([(cx - 52 * s, ground_y - 16 * s), (cx + 64 * s, ground_y - 16 * s)], fill=(210, 196, 168), width=int(16 * s))
    else:
        draw.line([(cx - 8 * s, hip_y), (cx - 10 * s, ground_y)], fill=shirt_d, width=int(22 * s))
        draw.line([(cx + 8 * s, hip_y), (cx + 10 * s, ground_y)], fill=shirt_d, width=int(22 * s))

    # ── 躯干（平涂 + 暗部） ──
    draw.ellipse([cx - torso_w, torso_top, cx + torso_w, hip_y + 14 * s], fill=shirt, outline=OUTLINE, width=lw)
    # 暗部（右下侧一块）
    draw.chord([cx - torso_w, torso_top, cx + torso_w, hip_y + 14 * s], 20, 100, fill=shirt_d)
    draw.chord([cx - torso_w, torso_top, cx + torso_w, hip_y + 14 * s], 20, 100, fill=None, outline=OUTLINE, width=lw)
    # 领口
    draw.polygon([(cx - 9 * s, torso_top + 2 * s), (cx + 9 * s, torso_top + 2 * s),
                  (cx, torso_top + 16 * s)], fill=skin, outline=OUTLINE, width=max(2, int(lw * 0.7)))
    # ── 细腻度：衣服褶皱 + 侧边暗部 + 高光 ──
    fold = _mix_outline(shirt, 0.62)
    draw.line([(cx - torso_w * 0.34, torso_top + 20 * s), (cx - torso_w * 0.20, torso_top + 44 * s)],
              fill=fold, width=max(1, int(lw * 0.5)))
    draw.line([(cx + torso_w * 0.30, torso_top + 18 * s), (cx + torso_w * 0.16, torso_top + 40 * s)],
              fill=fold, width=max(1, int(lw * 0.5)))
    # 腹部横褶
    draw.arc([cx - torso_w * 0.62, hip_y - 16 * s, cx + torso_w * 0.62, hip_y + 10 * s],
             200, 340, fill=fold, width=max(1, int(lw * 0.45)))
    # 衣服高光（左侧受光）
    draw.arc([cx - torso_w * 0.86, torso_top + 6 * s, cx - torso_w * 0.10, hip_y],
             120, 220, fill=tint(shirt, 1.16), width=max(2, int(lw * 0.55)))

    # ── 手臂 ──
    def arm(p1, p2, hand=None):
        draw.line([p1, p2], fill=shirt, width=int(19 * s))
        draw.line([p1, p2], fill=OUTLINE, width=lw)
        if hand:
            draw.ellipse([hand[0] - 9 * s, hand[1] - 9 * s, hand[0] + 9 * s, hand[1] + 9 * s],
                         fill=skin, outline=OUTLINE, width=max(2, int(lw * 0.8)))

    sh_top = (cx - torso_w * 0.72, torso_top + 12 * s)
    sh_top_r = (cx + torso_w * 0.72, torso_top + 12 * s)

    if pose == "run":
        arm(sh_top_r, (cx + torso_w * 1.8, torso_top - 12 * s), (cx + torso_w * 1.8, torso_top - 12 * s))
        arm(sh_top, (cx - torso_w * 1.7, torso_top + 46 * s), (cx - torso_w * 1.7, torso_top + 46 * s))
    elif pose == "walk":
        arm(sh_top_r, (cx + torso_w * 1.5, torso_top + 40 * s), (cx + torso_w * 1.5, torso_top + 40 * s))
        arm(sh_top, (cx - torso_w * 1.4, torso_top + 20 * s), (cx - torso_w * 1.4, torso_top + 20 * s))
    elif pose == "armsup":
        arm(sh_top, (cx - torso_w * 1.9, torso_top - 40 * s), (cx - torso_w * 1.9, torso_top - 40 * s))
        arm(sh_top_r, (cx + torso_w * 1.9, torso_top - 40 * s), (cx + torso_w * 1.9, torso_top - 40 * s))
    elif pose == "headache":
        arm(sh_top, (cx - torso_w * 1.5, torso_top - 28 * s), (cx - torso_w * 1.5, torso_top - 28 * s))
        arm(sh_top_r, (cx + torso_w * 1.5, torso_top - 28 * s), (cx + torso_w * 1.5, torso_top - 28 * s))
    elif pose == "wave":
        arm(sh_top_r, (cx + torso_w * 1.8, torso_top - 36 * s), (cx + torso_w * 1.8, torso_top - 36 * s))
        arm(sh_top, (cx - torso_w * 1.3, torso_top + 44 * s), (cx - torso_w * 1.3, torso_top + 44 * s))
    elif pose == "sit":
        arm(sh_top, (cx - torso_w * 1.3, torso_top + 40 * s), (cx - torso_w * 1.3, torso_top + 40 * s))
        arm(sh_top_r, (cx + torso_w * 1.2, torso_top + 16 * s), (cx + torso_w * 1.2, torso_top + 16 * s))
    else:
        arm(sh_top, (cx - torso_w * 0.95, torso_top + 56 * s), (cx - torso_w * 0.95, torso_top + 56 * s))
        arm(sh_top_r, (cx + torso_w * 0.95, torso_top + 56 * s), (cx + torso_w * 0.95, torso_top + 56 * s))

    # ── 头 ──
    draw.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r],
                 fill=skin, outline=OUTLINE, width=lw)
    # 耳朵
    draw.ellipse([cx - head_r * 1.08, head_cy - head_r * 0.02, cx - head_r * 0.84, head_cy + head_r * 0.30],
                 fill=skin, outline=OUTLINE, width=max(2, int(lw * 0.75)))
    draw.ellipse([cx + head_r * 0.84, head_cy - head_r * 0.02, cx + head_r * 1.08, head_cy + head_r * 0.30],
                 fill=skin, outline=OUTLINE, width=max(2, int(lw * 0.75)))
    draw_hair(draw, cx, head_cy, head_r, hair)
    _hair_strands(draw, cx, head_cy, head_r, hair)
    draw_face(draw, cx, eye_y, head_r, mood, look)

    # ── 细腻度：脸部细节（腮红 / 鼻尖 / 睫毛） ──
    # 鼻尖（极淡的短线）
    if mood not in ("sleep",):
        draw.line([(cx, eye_y + head_r * 0.22),
                   (cx + head_r * 0.06, eye_y + head_r * 0.30)],
                  fill=_mix_outline(skin), width=max(1, int(lw * 0.45)))
    # 腮红
    if mood in ("happy", "joy", "smug", "cry"):
        blush = (240, 148, 138)
        for sgn in (-1, 1):
            bx = cx + sgn * head_r * 0.62
            by = eye_y + head_r * 0.34
            for k in range(3):
                rr = head_r * (0.13 + k * 0.045)
                draw.ellipse([bx - rr, by - rr * 0.62, bx + rr, by + rr * 0.62],
                             fill=blush if k == 0 else _light_soft(blush))
    elif mood == "rage":
        blush = (238, 120, 108)
        for sgn in (-1, 1):
            bx = cx + sgn * head_r * 0.62
            by = eye_y + head_r * 0.34
            for k in range(3):
                rr = head_r * (0.13 + k * 0.045)
                draw.ellipse([bx - rr, by - rr * 0.62, bx + rr, by + rr * 0.62],
                             fill=blush if k == 0 else _light_soft(blush))

    # 漫画符号
    if mood in ("rage", "angry"):
        # 怒气十字
        for ang in (-30, 30):
            a = math.radians(ang)
            bx = cx + head_r * 1.25 + math.cos(a) * 14 * s
            by = head_cy - head_r * 0.95 + math.sin(a) * 14 * s
            draw.line([(bx - 10 * s, by - 10 * s), (bx + 10 * s, by + 10 * s)], fill=(214, 66, 58), width=max(3, int(4 * s)))
    elif mood in ("tired", "cold", "calm"):
        # 汗滴
        sx, sy = cx - head_r * 1.05, head_cy + head_r * 0.30
        draw.ellipse([sx - 7 * s, sy - 10 * s, sx + 7 * s, sy + 8 * s], fill=(140, 200, 238), outline=OUTLINE, width=max(2, int(2.6 * s)))
        draw.polygon([(sx - 7 * s, sy - 2 * s), (sx + 7 * s, sy - 2 * s), (sx, sy - 16 * s)], fill=(140, 200, 238))
    elif mood == "think":
        # 问号
        draw.text((cx + head_r * 0.92, head_cy - head_r * 1.25), "?", fill=(70, 62, 56), font=_font(int(38 * s)))

    # ── 道具 ──
    if prop == "phone":
        px, py = cx + torso_w * 1.3, torso_top + 42 * s
        draw.rounded_rectangle([px - 11 * s, py - 21 * s, px + 11 * s, py + 21 * s],
                               radius=5 * s, fill=(58, 60, 68), outline=OUTLINE, width=max(2, int(lw * 0.7)))
        draw.rounded_rectangle([px - 7 * s, py - 16 * s, px + 7 * s, py + 14 * s],
                               radius=2 * s, fill=(150, 198, 238))
    elif prop == "book":
        bx, by = cx - torso_w * 1.5, torso_top + 44 * s
        draw.polygon([(bx - 30 * s, by), (bx, by - 9 * s), (bx + 30 * s, by),
                      (bx + 30 * s, by + 26 * s), (bx, by + 17 * s), (bx - 30 * s, by + 26 * s)],
                     fill=(244, 238, 224), outline=OUTLINE, width=max(2, int(lw * 0.75)))
        draw.line([(bx, by - 9 * s), (bx, by + 17 * s)], fill=OUTLINE, width=max(2, int(lw * 0.6)))
    elif prop == "laptop":
        lx, ly = cx + torso_w * 1.3, torso_top + 50 * s
        draw.polygon([(lx - 4 * s, ly - 40 * s), (lx + 46 * s, ly - 40 * s),
                      (lx + 36 * s, ly + 14 * s), (lx, ly + 14 * s)],
                     fill=(206, 210, 218), outline=OUTLINE, width=max(2, int(lw * 0.75)))
    elif prop == "clock":
        px, py = cx + torso_w * 1.7, torso_top + 6 * s
        draw.ellipse([px - 18 * s, py - 18 * s, px + 18 * s, py + 18 * s],
                     fill=(252, 246, 232), outline=OUTLINE, width=max(2, int(lw * 0.75)))
        draw.line([(px, py), (px, py - 10 * s)], fill=OUTLINE, width=max(2, int(3 * s)))
        draw.line([(px, py), (px + 7 * s, py + 5 * s)], fill=OUTLINE, width=max(2, int(3 * s)))

    # ── 气泡 ──
    _maybe_bubble(draw, bubble, bubble_kind, bubble_tail, bubble_text,
                  cx, head_cy, head_r, torso_w, s, bounds)


def _maybe_bubble(draw, spec, kind, tail, text, cx, head_cy, head_r, torso_w, s, bounds=None):
    """气泡放在角色头顶或身侧，不遮挡脸和道具。"""
    if not spec:
        return
    if tail == "left":
        anchor_x, anchor_y = cx - head_r * 1.05, head_cy - head_r * 0.75
    elif tail == "right":
        anchor_x, anchor_y = cx + head_r * 1.05, head_cy - head_r * 0.75
    else:
        anchor_x, anchor_y = cx, head_cy - head_r * 1.25
    _draw_bubble(draw, spec, kind, tail, text, anchor_x, anchor_y, s, bounds)


def _draw_bubble(draw, spec, kind, tail, text, anchor_x, anchor_y, s, bounds=None):
    """动漫对白气泡：白底黑边 + 尖尾巴。"""
    bw, bh = 168, 58
    if isinstance(spec, dict):
        bw = spec.get("w", bw)
        bh = spec.get("h", bh)
        bx = spec.get("x")
        by = spec.get("y")
    else:
        bx = None
        by = None

    if bx is None:
        if tail == "left":
            bx = anchor_x - bw - 30
        elif tail == "right":
            bx = anchor_x + 30
        else:
            bx = anchor_x - bw // 2
    if by is None:
        by = anchor_y - bh - 30 if tail == "down" else anchor_y - bh // 2

    # 边界避让：超出画面就翻到另一侧 / 下移
    if bounds:
        bx0, by0, bx1, by1 = bounds
        if bx < bx0:
            bx = bx0
            tail = "right"
        elif bx + bw > bx1:
            bx = bx1 - bw
            tail = "left"
        if by < by0:
            by = by0
        elif by + bh + 26 > by1:
            by = max(by0, by1 - bh - 26)

    lw = max(3, int(4.2 * s))
    if kind == "think":
        # 云朵思考泡
        for i in range(3):
            r = bh * (0.46 - i * 0.10)
            ccx = bx + bw * (0.24 + i * 0.26)
            ccy = by + bh * (0.48 + (0.10 if i % 2 else -0.06))
            draw.ellipse([ccx - r, ccy - r, ccx + r, ccy + r], fill=(255, 255, 255), outline=OUTLINE, width=lw)
        for i, (dx, dy, rr) in enumerate(((0.34, 1.02, 0.13), (0.24, 1.28, 0.085))):
            ccx, ccy = bx + bw * dx, by + bh * dy
            r = bh * rr
            draw.ellipse([ccx - r, ccy - r, ccx + r, ccy + r], fill=(255, 255, 255), outline=OUTLINE, width=lw)
    elif kind == "shout":
        pts = []
        n = 14
        for i in range(n * 2):
            a = math.pi * i / n - math.pi / 2
            k = 1.0 if i % 2 == 0 else 0.80
            px = bx + bw / 2 + math.cos(a) * bw / 2 * k
            py = by + bh / 2 + math.sin(a) * bh / 2 * k
            pts.append((px, py))
        draw.polygon(pts, fill=(255, 255, 255))
        draw.line(pts + [pts[0]], fill=OUTLINE, width=lw, joint="curve")
        tx = bx + bw / 2
        draw.polygon([(tx - 13, by + bh - 6), (tx + 13, by + bh - 6), (tx, by + bh + 22)], fill=(255, 255, 255))
        draw.line([(tx - 13, by + bh - 6), (tx, by + bh + 22), (tx + 13, by + bh - 6)], fill=OUTLINE, width=lw, joint="curve")
    elif kind == "aside":
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=14, fill=(250, 248, 244),
                               outline=(126, 118, 108), width=max(2, int(lw * 0.7)))
        tx = bx + bw // 2
        for i in range(0, 14, 5):
            draw.line([(tx - 4 + i, by + bh), (tx - 1 + i, by + bh + 9)], fill=(126, 118, 108), width=max(2, int(lw * 0.6)))
    else:
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=14, fill=(255, 255, 255),
                               outline=OUTLINE, width=lw)
        # 漫画气泡硬投影
        draw.rounded_rectangle([bx + 7, by + 7, bx + bw + 7, by + bh + 7], radius=14,
                               fill=(70, 62, 56))
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=14, fill=(255, 255, 255),
                               outline=OUTLINE, width=lw)
        # 细腻度：内侧细描边 + 顶部高光弧
        draw.rounded_rectangle([bx + 6, by + 6, bx + bw - 6, by + bh - 6], radius=10,
                               outline=(206, 198, 188), width=2)
        draw.arc([bx + 14, by + 8, bx + bw - 14, by + bh * 0.62], 200, 340,
                 fill=(236, 230, 222), width=5)
        if tail == "down":
            tx = bx + bw // 2
            draw.polygon([(tx - 13, by + bh - 3), (tx + 13, by + bh - 3), (tx, by + bh + 22)], fill=(255, 255, 255))
            draw.line([(tx - 13, by + bh - 3), (tx, by + bh + 22), (tx + 13, by + bh - 3)], fill=OUTLINE, width=lw, joint="curve")
            draw.rectangle([tx - 13, by + bh - 4, tx + 13, by + bh - 1], fill=(255, 255, 255))
        elif tail == "left":
            ty = by + bh // 2
            draw.polygon([(bx + 3, ty - 12), (bx + 3, ty + 12), (bx - 22, ty)], fill=(255, 255, 255))
            draw.line([(bx + 3, ty - 12), (bx - 22, ty), (bx + 3, ty + 12)], fill=OUTLINE, width=lw, joint="curve")
            draw.rectangle([bx, ty - 12, bx + 4, ty + 12], fill=(255, 255, 255))
        elif tail == "right":
            ty = by + bh // 2
            draw.polygon([(bx + bw - 3, ty - 12), (bx + bw - 3, ty + 12), (bx + bw + 22, ty)], fill=(255, 255, 255))
            draw.line([(bx + bw - 3, ty - 12), (bx + bw + 22, ty), (bx + bw - 3, ty + 12)], fill=OUTLINE, width=lw, joint="curve")
            draw.rectangle([bx + bw - 4, ty - 12, bx + bw, ty + 12], fill=(255, 255, 255))

    if not text:
        return
    size = 22
    f = _font(size, bold=True)
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=f) > bw - 24 and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    lines = lines[:2]
    lh = int(size * 1.26)
    ty = by + (bh - len(lines) * lh) // 2
    for ln in lines:
        tw = draw.textlength(ln, font=f)
        draw.text((bx + (bw - tw) / 2, ty), ln, fill=OUTLINE, font=f)
        ty += lh
