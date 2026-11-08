# -*- coding: utf-8 -*-
"""对白气泡系统 —— 让墨线角色开口说话。

气泡种类：
  speech   普通对白（圆角矩形 + 尾巴）
  think    思考气泡（云朵状）
  shout    喊话（尖刺状）
  aside    小声嘀咕（小号气泡 + 虚线）

尾巴指向角色（可指定方向：left / right / down）。
"""

from __future__ import annotations

import math
import random

INK = (38, 33, 28)


def _outline(draw, pts, width=3, color=INK, closed=True):
    if closed:
        draw.polygon(pts, outline=color, width=width)
    else:
        draw.line(pts, fill=color, width=width, joint="curve")


def bubble_speech(draw, x, y, w, h, tail="down", tail_len=26, tail_w=16, width=3):
    """圆角对白框。x,y = 左上角。"""
    r = min(22, h // 2)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=(255, 253, 248), outline=INK, width=width)
    # 尾巴
    if tail == "down":
        tx = x + w // 2
        draw.polygon([(tx - tail_w // 2, y + h - 2), (tx + tail_w // 2, y + h - 2), (tx, y + h + tail_len)],
                     fill=(255, 253, 248), outline=INK, width=width)
        # 盖住尾巴与框的接缝
        draw.rectangle([tx - tail_w // 2 - 1, y + h - 4, tx + tail_w // 2 + 1, y + h + 2], fill=(255, 253, 248))
        draw.line([(tx - tail_w // 2, y + h - 2), (tx, y + h + tail_len)], fill=INK, width=width)
    elif tail == "left":
        ty = y + h // 2
        draw.polygon([(x + 2, ty - tail_w // 2), (x + 2, ty + tail_w // 2), (x - tail_len, ty)],
                     fill=(255, 253, 248), outline=INK, width=width)
        draw.rectangle([x - 1, ty - tail_w // 2 - 1, x + 4, ty + tail_w // 2 + 1], fill=(255, 253, 248))
        draw.line([(x - tail_len, ty), (x + 2, ty + tail_w // 2)], fill=INK, width=width)
    elif tail == "right":
        ty = y + h // 2
        draw.polygon([(x + w - 2, ty - tail_w // 2), (x + w - 2, ty + tail_w // 2), (x + w + tail_len, ty)],
                     fill=(255, 253, 248), outline=INK, width=width)
        draw.rectangle([x + w - 4, ty - tail_w // 2 - 1, x + w + 1, ty + tail_w // 2 + 1], fill=(255, 253, 248))
        draw.line([(x + w - 2, ty + tail_w // 2), (x + w + tail_len, ty)], fill=INK, width=width)


def bubble_think(draw, x, y, w, h, width=3):
    """思考云朵：几个相连的小圆 + 尾巴泡。"""
    n = 4
    for i in range(n):
        cx = x + w * (0.18 + i * 0.22)
        cy = y + h * (0.5 + (0.10 if i % 2 else -0.08))
        r = h * (0.46 - i * 0.07)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 253, 248), outline=INK, width=width)
    # 收口
    draw.ellipse([x - 2, y + h * 0.08, x + w * 0.42, y + h * 0.92], fill=(255, 253, 248), outline=INK, width=width)
    # 小尾巴泡
    for i, (dx, dy, r) in enumerate(((0.30, 1.00, 0.10), (0.20, 1.24, 0.065))):
        cx = x + w * dx
        cy = y + h * dy
        rr = h * r
        draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(255, 253, 248), outline=INK, width=width)


def bubble_shout(draw, x, y, w, h, width=3, spikes=11):
    """喊话气泡：锯齿边。"""
    pts = []
    for i in range(spikes * 2):
        ang = math.pi * i / (spikes * 2) - math.pi / 2
        # 椭圆上的点
        px = x + w / 2 + math.cos(ang) * w / 2
        py = y + h / 2 + math.sin(ang) * h / 2
        if i % 2 == 0:
            k = 1.0
        else:
            k = 0.84
        pts.append((x + w / 2 + (px - x - w / 2) * k, y + h / 2 + (py - y - h / 2) * k))
    draw.polygon(pts, fill=(255, 253, 248), outline=INK, width=width)
    # 尾巴
    tx = x + w / 2
    draw.polygon([(tx - 14, y + h - 4), (tx + 14, y + h - 4), (tx, y + h + 24)], fill=(255, 253, 248))
    draw.line([(tx - 14, y + h - 4), (tx, y + h + 24)], fill=INK, width=width)
    draw.line([(tx, y + h + 24), (tx + 14, y + h - 4)], fill=INK, width=width)


def bubble_aside(draw, x, y, w, h, width=2):
    """小声嘀咕：小气泡 + 虚线边。"""
    draw.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=(248, 246, 240), outline=(120, 112, 102), width=width)
    tx = x + w // 2
    for i in range(0, 16, 6):
        draw.line([(tx - 4 + i, y + h), (tx - 1 + i, y + h + 10)], fill=(120, 112, 102), width=width)


def draw_bubble(draw, kind, box, tail="down"):
    x, y, w, h = box
    if kind == "think":
        bubble_think(draw, x, y, w, h)
    elif kind == "shout":
        bubble_shout(draw, x, y, w, h)
    elif kind == "aside":
        bubble_aside(draw, x, y, w, h)
    else:
        bubble_speech(draw, x, y, w, h, tail=tail)
