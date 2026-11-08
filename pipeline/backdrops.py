# -*- coding: utf-8 -*-
"""背景场景库 —— 《纸上人生》漫画分镜背景元素。

每个场景都是一段可组合的绘图函数，画在角色**背后**，负责把大片空背景填满，
同时和上下句的语义对应（错误做法 vs 正确做法，用同一个场景、两种色调）。

约定：
    每个场景函数签名  fn(d, w, h, pal)
    d   ImageDraw
    w,h 分镜尺寸
    pal 调色板字典：
        far  远景色（最淡）
        mid  中景色
        near 近景色（最浓）
        ink  描边色
        glow 高光/发光色
"""

from __future__ import annotations

import math
import random

INK = (40, 34, 30)


# ── 小工具 ──────────────────────────────────────────────
def _mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def _dark(c, k=0.72):
    return tuple(max(0, int(v * k)) for v in c)


def _light(c, k=1.14):
    return tuple(min(255, int(v * k)) for v in c)


def _rect(d, box, fill, outline=None, width=3):
    d.rectangle(box, fill=fill, outline=outline, width=width)


def _round(d, box, r, fill, outline=None, width=3):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def _hline(d, x0, x1, y, fill, width=3):
    d.line([(x0, y), (x1, y)], fill=fill, width=width)


def _vline(d, x, y0, y1, fill, width=3):
    d.line([(x, y0), (x, y1)], fill=fill, width=width)


def _sky_band(d, w, h, pal):
    """远景天光带：让顶部不那么空。"""
    top = _light(pal["far"], 1.06)
    for i in range(6):
        y0 = h * 0.06 * i
        y1 = h * 0.06 * (i + 1)
        t = i / 5
        d.rectangle([0, y0, w, y1], fill=_mix(top, pal["far"], t))


def _clouds(d, w, h, pal, n=4, ymax=0.30, seed=7):
    """上部补白：几团云。"""
    rnd = random.Random(seed)
    for _ in range(n):
        cx = rnd.uniform(0.02, 0.94) * w
        cy = rnd.uniform(0.04, ymax) * h
        r = rnd.uniform(0.05, 0.10) * w
        col = _mix(pal["glow"], (255, 255, 255), 0.45)
        d.ellipse([cx - r, cy - r * 0.52, cx + r, cy + r * 0.52], fill=col,
                  outline=pal["ink"], width=3)
        d.ellipse([cx - r * 0.5, cy - r * 0.72, cx + r * 0.5, cy + r * 0.28], fill=col,
                  outline=pal["ink"], width=3)


def _birds(d, w, h, pal, n=5, seed=13):
    """上部补白：飞鸟。"""
    rnd = random.Random(seed)
    for _ in range(n):
        cx = rnd.uniform(0.05, 0.95) * w
        cy = rnd.uniform(0.05, 0.26) * h
        s = rnd.uniform(0.012, 0.024) * w
        d.arc([cx - s, cy - s * 0.7, cx, cy + s * 0.5], 200, 340, fill=pal["ink"], width=3)
        d.arc([cx, cy - s * 0.7, cx + s, cy + s * 0.5], 200, 340, fill=pal["ink"], width=3)


def _bunting(d, w, h, pal, y=0.05, n=10, seed=17):
    """上部补白：一串三角旗。"""
    rnd = random.Random(seed)
    cols = [(240, 90, 80), (250, 200, 70), (110, 190, 230), (150, 210, 130), (220, 130, 200)]
    pts = []
    for i in range(n + 1):
        pts.append((w * (0.02 + i * 0.96 / n), h * (y + 0.02 * math.sin(i * 0.9))))
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        d.polygon([(x0, y0), (x1, y1), (mx, my + h * 0.075)],
                  fill=cols[i % len(cols)], outline=pal["ink"], width=2)
    d.line(pts, fill=pal["ink"], width=3)


def _hanging_lights(d, w, h, pal, n=6, y=0.04, seed=19):
    """上部补白：垂下来的小灯串。"""
    rnd = random.Random(seed)
    for i in range(n):
        x = w * (0.06 + i * 0.88 / max(1, n - 1))
        drop = h * (0.10 + 0.04 * math.sin(i * 1.3))
        d.line([(x, 0), (x, drop)], fill=pal["ink"], width=2)
        d.ellipse([x - 11, drop - 11, x + 11, drop + 11], fill=pal["glow"],
                  outline=pal["ink"], width=3)


def _wall_shelf(d, w, h, pal, y=0.12, seed=23):
    """上部补白：墙上一排搁板 + 杂物。"""
    rnd = random.Random(seed)
    _hline(d, w * 0.04, w * 0.46, h * y, pal["ink"], 5)
    d.rectangle([w * 0.04, h * y, w * 0.46, h * y + 10], fill=pal["near"], outline=pal["ink"], width=3)
    x = w * 0.06
    while x < w * 0.44:
        bw = rnd.uniform(0.022, 0.042) * w
        bh = rnd.uniform(0.04, 0.075) * h
        col = _mix(pal["near"], (rnd.randint(170, 245), rnd.randint(140, 215), rnd.randint(130, 205)), 0.6)
        d.rectangle([x, h * y - bh, x + bw, h * y], fill=col, outline=pal["ink"], width=2)
        x += bw + w * 0.006


def _hanging_plant(d, w, h, pal, x=0.86, y=0.0, seed=29):
    """上部补白：吊挂的绿植。"""
    d.line([(w * x, y), (w * x, h * 0.12)], fill=pal["ink"], width=3)
    d.polygon([(w * (x - 0.055), h * 0.12), (w * (x + 0.055), h * 0.12),
               (w * (x + 0.035), h * 0.20), (w * (x - 0.035), h * 0.20)],
              fill=_mix(pal["near"], (200, 130, 90), 0.5), outline=pal["ink"], width=3)
    for a in (-55, -20, 20, 55):
        rad = math.radians(a)
        ex = w * x + math.sin(rad) * 70
        ey = h * 0.20 + math.cos(rad) * 62
        d.line([(w * x, h * 0.20), (ex, ey)], fill=(74, 148, 80), width=5)
        d.ellipse([ex - 16, ey - 12, ex + 16, ey + 12], fill=(104, 190, 92),
                  outline=(56, 132, 68), width=2)


def _sky_sun(d, w, h, pal, x=0.14, y=0.14, r=0.11):
    """上部补白：太阳 + 光晕。"""
    cx, cy = w * x, h * y
    for i in range(8):
        a = math.tau * i / 8
        d.line([(cx + math.cos(a) * r * w * 1.2, cy + math.sin(a) * r * w * 1.2),
                (cx + math.cos(a) * r * w * 1.7, cy + math.sin(a) * r * w * 1.7)],
               fill=pal["glow"], width=5)
    d.ellipse([cx - r * w, cy - r * w, cx + r * w, cy + r * w],
              fill=pal["glow"], outline=pal["ink"], width=4)


def _frame_posters(d, w, h, pal, seed=37):
    """上部补白：墙上挂几幅小画。"""
    rnd = random.Random(seed)
    for _ in range(4):
        x = rnd.uniform(0.04, 0.80) * w
        y = rnd.uniform(0.05, 0.22) * h
        pw = rnd.uniform(0.07, 0.13) * w
        ph = pw * 1.25
        d.rectangle([x, y, x + pw, y + ph], fill=(255, 253, 246), outline=pal["ink"], width=3)
        d.rectangle([x + 6, y + 6, x + pw - 6, y + ph - 6],
                    fill=_mix(pal["glow"], (200, 210, 220), 0.45))


def _banner_text(d, w, h, pal, text, y=0.06, seed=41):
    """上部补白：一条横幅（横着的强调条）。"""
    fy = h * y
    d.rectangle([w * 0.05, fy, w * 0.95, fy + h * 0.075], fill=pal["glow"],
                outline=pal["ink"], width=4)
    for i in range(len(text)):
        pass
    # 简化：用横线表示文字
    x = w * 0.10
    for i in range(9):
        seg = w * (0.06 + 0.02 * (i % 3))
        _hline(d, x, x + seg, fy + h * 0.037, pal["ink"], 4)
        x += seg + w * 0.018
        if x > w * 0.85:
            break


# ── 场景 1：办公室 ─────────────────────────────────────
def scene_office(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 远景：窗
    for i in range(4):
        x0 = w * (0.06 + i * 0.235)
        d.rectangle([x0, h * 0.10, x0 + w * 0.16, h * 0.42], fill=_light(pal["far"], 1.02),
                    outline=pal["ink"], width=3)
        _vline(d, x0 + w * 0.08, h * 0.10, h * 0.42, pal["ink"], 3)
    # 中景：文件架
    for i in range(3):
        x0 = w * (0.70 + i * 0.10)
        col = _mix(pal["mid"], pal["near"], 0.25 + i * 0.2)
        d.rectangle([x0, h * 0.28, x0 + w * 0.085, h * 0.66], fill=col,
                    outline=pal["ink"], width=3)
        for k in range(3):
            d.rectangle([x0 + 5, h * 0.32 + k * h * 0.10, x0 + w * 0.085 - 5, h * 0.32 + k * h * 0.10 + h * 0.07],
                        fill=_light(col, 1.16))
    # 近景：办公桌 + 显示器
    d.rectangle([w * 0.05, h * 0.66, w * 0.55, h * 0.70], fill=pal["near"], outline=pal["ink"], width=3)
    d.rectangle([w * 0.08, h * 0.72, w * 0.10, h * 0.86], fill=_dark(pal["near"]))
    d.rectangle([w * 0.48, h * 0.72, w * 0.50, h * 0.86], fill=_dark(pal["near"]))
    # 显示器
    d.rectangle([w * 0.18, h * 0.34, w * 0.40, h * 0.60], fill=_dark(pal["mid"], 0.55),
                outline=pal["ink"], width=4)
    d.rectangle([w * 0.195, h * 0.355, w * 0.385, h * 0.585], fill=pal["glow"])
    d.rectangle([w * 0.275, h * 0.60, w * 0.305, h * 0.66], fill=_dark(pal["mid"], 0.6))
    d.rectangle([w * 0.245, h * 0.655, w * 0.335, h * 0.67], fill=_dark(pal["mid"], 0.6))


# ── 场景 2：书桌 ───────────────────────────────────────
def scene_desk(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 墙上贴纸
    rnd = random.Random(4)
    for _ in range(9):
        x = rnd.uniform(0.02, 0.94) * w
        y = rnd.uniform(0.05, 0.30) * h
        s = rnd.uniform(0.035, 0.07) * w
        d.rectangle([x, y, x + s, y + s * 0.7], fill=_mix(pal["far"], (255, 255, 255), 0.5),
                    outline=pal["ink"], width=2)
    # 桌面
    d.rectangle([0, h * 0.64, w, h], fill=pal["near"])
    _hline(d, 0, w, h * 0.64, pal["ink"], 4)
    d.rectangle([0, h * 0.64, w, h * 0.68], fill=_light(pal["near"], 1.14))
    # 笔筒
    d.rectangle([w * 0.06, h * 0.44, w * 0.135, h * 0.64], fill=_mix(pal["mid"], (220, 160, 120), 0.5),
                outline=pal["ink"], width=3)
    for i in range(5):
        x = w * (0.075 + i * 0.013)
        d.line([(x, h * 0.44), (x + 4, h * 0.36 - i % 2 * h * 0.05)], fill=pal["ink"], width=4)
    # 台灯
    d.ellipse([w * 0.80, h * 0.60, w * 0.86, h * 0.66], fill=_dark(pal["near"]))
    d.line([(w * 0.83, h * 0.62), (w * 0.83, h * 0.34)], fill=pal["ink"], width=5)
    d.polygon([(w * 0.75, h * 0.34), (w * 0.91, h * 0.34), (w * 0.87, h * 0.24), (w * 0.79, h * 0.24)],
              fill=pal["mid"], outline=pal["ink"])
    d.polygon([(w * 0.78, h * 0.36), (w * 0.88, h * 0.36), (w * 0.83, h * 0.62)], fill=pal["glow"])
    # 摊开的笔记本
    d.polygon([(w * 0.30, h * 0.60), (w * 0.44, h * 0.58), (w * 0.46, h * 0.66), (w * 0.32, h * 0.68)],
              fill=(255, 252, 242), outline=pal["ink"], width=3)
    for i in range(4):
        _hline(d, w * 0.325, w * 0.435, h * (0.605 + i * 0.015), _mix(pal["ink"], (255, 255, 255), 0.45), 2)


# ── 场景 3：手机界面特写 ───────────────────────────────
def scene_phone(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 巨大的手机（背景放大版）
    pw = w * 0.30
    ph = h * 0.86
    x0 = w * 0.66
    y0 = h * 0.07
    _round(d, [x0, y0, x0 + pw, y0 + ph], 26, _dark(pal["near"], 0.55), pal["ink"], 5)
    _round(d, [x0 + 12, y0 + 16, x0 + pw - 12, y0 + ph - 16], 18, pal["glow"], None)
    # 屏幕里的列表
    for i in range(6):
        y = y0 + 40 + i * (ph - 90) / 6
        d.rectangle([x0 + 30, y, x0 + pw - 30, y + (ph - 90) / 10],
                    fill=_mix(pal["glow"], (255, 255, 255), 0.55))
    # 搜索框
    _round(d, [w * 0.06, h * 0.22, w * 0.52, h * 0.36], 14, (255, 255, 255), pal["ink"], 4)
    d.ellipse([w * 0.09, h * 0.26, w * 0.135, h * 0.32], outline=pal["ink"], width=4)
    d.line([(w * 0.132, h * 0.315), (w * 0.15, h * 0.335)], fill=pal["ink"], width=4)
    # 放大镜扫过菜单列表
    for i in range(7):
        y = h * 0.46 + i * h * 0.07
        d.rectangle([w * 0.06, y, w * 0.50, y + h * 0.045], fill=_mix(pal["far"], (255, 255, 255), 0.45),
                    outline=pal["ink"], width=2)
    d.ellipse([w * 0.40, h * 0.40, w * 0.54, h * 0.62], outline=(214, 62, 44), width=6)
    d.line([(w * 0.51, h * 0.59), (w * 0.58, h * 0.66)], fill=(214, 62, 44), width=7)


# ── 场景 4：城市天际线 ─────────────────────────────────
def scene_city(d, w, h, pal):
    _sky_band(d, w, h, pal)
    _sky_sun(d, w, h, pal, x=0.78, y=0.16, r=0.09)
    _clouds(d, w, h, pal, n=3, ymax=0.24, seed=231)
    # 远景楼群
    rnd = random.Random(9)
    x = -20
    while x < w + 20:
        bw = rnd.uniform(0.05, 0.11) * w
        bh = rnd.uniform(0.22, 0.44) * h
        col = _mix(pal["far"], pal["mid"], rnd.uniform(0.1, 0.4))
        d.rectangle([x, h * 0.58 - bh, x + bw, h * 0.58], fill=col)
        x += bw + rnd.uniform(0.005, 0.02) * w
    # 中景楼群 + 亮窗
    x = -20
    while x < w + 20:
        bw = rnd.uniform(0.07, 0.13) * w
        bh = rnd.uniform(0.30, 0.58) * h
        col = _mix(pal["mid"], pal["near"], rnd.uniform(0.2, 0.6))
        d.rectangle([x, h * 0.64 - bh, x + bw, h * 0.64], fill=col, outline=pal["ink"], width=2)
        for r in range(int(bh / (h * 0.075))):
            for c in range(int(bw / (w * 0.035))):
                if rnd.random() < 0.55:
                    wx = x + 6 + c * w * 0.035
                    wy = h * 0.64 - bh + 8 + r * h * 0.075
                    if wx + w * 0.022 < x + bw - 4 and wy + h * 0.04 < h * 0.64:
                        d.rectangle([wx, wy, wx + w * 0.022, wy + h * 0.038],
                                    fill=pal["glow"] if rnd.random() < 0.7 else _dark(col, 0.8))
        x += bw + rnd.uniform(0.01, 0.03) * w
    # 地面
    d.rectangle([0, h * 0.64, w, h], fill=pal["near"])
    _hline(d, 0, w, h * 0.64, pal["ink"], 4)


# ── 场景 5：山野 ───────────────────────────────────────
def scene_mountain(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上部：太阳 + 云 + 飞鸟
    _sky_sun(d, w, h, pal, x=0.72, y=0.18, r=0.10)
    _clouds(d, w, h, pal, n=4, ymax=0.28, seed=63)
    _birds(d, w, h, pal, n=6, seed=65)
    # 云
    rnd = random.Random(21)
    for _ in range(5):
        cx = rnd.uniform(0.05, 0.95) * w
        cy = rnd.uniform(0.06, 0.26) * h
        r = rnd.uniform(0.035, 0.07) * w
        d.ellipse([cx - r, cy - r * 0.55, cx + r, cy + r * 0.55],
                  fill=_mix(pal["glow"], (255, 255, 255), 0.4))
    # 远山
    d.polygon([(0, h * 0.62), (w * 0.28, h * 0.26), (w * 0.52, h * 0.62)], fill=pal["far"])
    d.polygon([(w * 0.34, h * 0.62), (w * 0.68, h * 0.20), (w * 1.02, h * 0.62)], fill=_mix(pal["far"], pal["mid"], 0.35))
    # 近山
    d.polygon([(0, h * 0.72), (w * 0.36, h * 0.40), (w * 0.74, h * 0.72)], fill=pal["mid"], outline=pal["ink"])
    d.polygon([(w * 0.40, h * 0.72), (w * 0.78, h * 0.42), (w * 1.02, h * 0.72)], fill=pal["near"], outline=pal["ink"])
    # 地面
    d.rectangle([0, h * 0.70, w, h], fill=_mix(pal["near"], (120, 160, 90), 0.4))
    _hline(d, 0, w, h * 0.70, pal["ink"], 4)
    for _ in range(14):
        tx = rnd.uniform(0, 1) * w
        ty = rnd.uniform(0.74, 0.96) * h
        d.line([(tx, ty), (tx, ty - h * 0.05)], fill=_dark(pal["near"], 0.7), width=3)


# ── 场景 6：客厅 ───────────────────────────────────────
def scene_living(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上部：墙上挂画 + 搁板
    _frame_posters(d, w, h, pal, seed=81)
    _wall_shelf(d, w, h, pal, y=0.16, seed=83)
    # 落地窗
    d.rectangle([w * 0.60, h * 0.08, w * 0.94, h * 0.60], fill=_light(pal["glow"], 1.02),
                outline=pal["ink"], width=4)
    _vline(d, w * 0.77, h * 0.08, h * 0.60, pal["ink"], 4)
    d.polygon([(w * 0.60, h * 0.60), (w * 0.77, h * 0.20), (w * 0.94, h * 0.60)],
              fill=_mix(pal["glow"], (255, 255, 255), 0.5))
    # 沙发
    d.rounded_rectangle([w * 0.04, h * 0.52, w * 0.46, h * 0.72], radius=16,
                        fill=pal["mid"], outline=pal["ink"], width=4)
    d.rounded_rectangle([w * 0.02, h * 0.66, w * 0.48, h * 0.76], radius=14,
                        fill=pal["near"], outline=pal["ink"], width=4)
    # 抱枕
    d.rounded_rectangle([w * 0.10, h * 0.55, w * 0.20, h * 0.66], radius=10,
                        fill=_mix(pal["near"], (240, 130, 110), 0.6), outline=pal["ink"], width=3)
    # 地毯
    d.ellipse([w * 0.14, h * 0.82, w * 0.70, h * 0.98], fill=_mix(pal["near"], (255, 255, 255), 0.28),
              outline=pal["ink"], width=3)
    # 落地灯
    d.line([(w * 0.56, h * 0.72), (w * 0.56, h * 0.30)], fill=pal["ink"], width=5)
    d.polygon([(w * 0.50, h * 0.30), (w * 0.62, h * 0.30), (w * 0.59, h * 0.20), (w * 0.53, h * 0.20)],
              fill=pal["glow"], outline=pal["ink"])
    d.ellipse([w * 0.52, h * 0.70, w * 0.60, h * 0.76], fill=_dark(pal["near"]))


# ── 场景 7：会议桌 ─────────────────────────────────────
def scene_meeting(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 白板
    d.rectangle([w * 0.08, h * 0.10, w * 0.44, h * 0.44], fill=(252, 250, 244),
                outline=pal["ink"], width=4)
    for i in range(5):
        _hline(d, w * 0.11, w * (0.18 + 0.05 * (i % 4)), h * (0.16 + i * 0.055),
               _mix(pal["ink"], (255, 255, 255), 0.4), 3)
    d.rectangle([w * 0.30, h * 0.12, w * 0.42, h * 0.17], fill=_mix(pal["glow"], (255, 255, 255), 0.3))
    # 桌子（透视）
    d.polygon([(w * 0.30, h * 0.62), (w * 1.02, h * 0.62), (w * 1.02, h * 0.80), (w * 0.22, h * 0.80)],
              fill=pal["near"], outline=pal["ink"])
    # 纸杯
    for i, cx in enumerate((0.42, 0.60, 0.80)):
        d.rectangle([w * cx, h * 0.55, w * (cx + 0.045), h * 0.63], fill=(255, 255, 255),
                    outline=pal["ink"], width=3)
    # 笔记本
    d.polygon([(w * 0.66, h * 0.66), (w * 0.84, h * 0.655), (w * 0.86, h * 0.72), (w * 0.68, h * 0.725)],
              fill=(255, 252, 242), outline=pal["ink"], width=3)
    # 背后椅背剪影
    for cx in (0.22, 0.40, 0.58):
        d.rounded_rectangle([w * cx, h * 0.50, w * (cx + 0.09), h * 0.66], radius=10,
                            fill=_dark(pal["mid"], 0.8), outline=pal["ink"], width=3)


# ── 场景 8：卧室 ───────────────────────────────────────
def scene_bedroom(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上部：墙纸条纹 + 吊灯 + 挂饰
    for i in range(12):
        x = w * (i * 0.085)
        d.line([(x, 0), (x, h * 0.40)], fill=_mix(pal["far"], pal["ink"], 0.12), width=3)
    d.line([(w * 0.05, 0), (w * 0.05, h * 0.40)], fill=pal["ink"], width=4)
    d.ellipse([w * 0.44, h * 0.02, w * 0.56, h * 0.14], fill=pal["glow"],
              outline=pal["ink"], width=4)
    d.line([(w * 0.50, 0), (w * 0.50, h * 0.04)], fill=pal["ink"], width=3)
    # 墙上小相框
    for cx in (0.14, 0.24):
        d.rectangle([w * cx, h * 0.06, w * (cx + 0.07), h * 0.20], fill=(255, 253, 246),
                    outline=pal["ink"], width=3)
        d.rectangle([w * cx + 5, h * 0.06 + 5, w * (cx + 0.07) - 5, h * 0.20 - 5],
                    fill=_mix(pal["far"], (200, 210, 220), 0.5))
    # 窗 + 窗帘
    d.rectangle([w * 0.62, h * 0.10, w * 0.90, h * 0.44], fill=_light(pal["glow"], 0.95),
                outline=pal["ink"], width=4)
    for sx in (0.58, 0.90):
        d.polygon([(w * sx, h * 0.06), (w * (sx + 0.07), h * 0.06),
                   (w * (sx + 0.05), h * 0.52), (w * (sx - 0.02), h * 0.52)],
                  fill=pal["mid"], outline=pal["ink"])
    # 床
    d.rectangle([w * 0.04, h * 0.60, w * 0.58, h * 0.80], fill=pal["near"], outline=pal["ink"], width=4)
    d.rounded_rectangle([w * 0.06, h * 0.52, w * 0.24, h * 0.64], radius=12,
                        fill=(255, 252, 242), outline=pal["ink"], width=3)
    d.rectangle([w * 0.20, h * 0.58, w * 0.58, h * 0.80], fill=_mix(pal["mid"], (255, 255, 255), 0.25),
                outline=pal["ink"], width=3)
    # 床头柜 + 闹钟
    d.rectangle([w * 0.60, h * 0.58, w * 0.74, h * 0.78], fill=pal["mid"], outline=pal["ink"], width=3)
    d.ellipse([w * 0.635, h * 0.44, w * 0.705, h * 0.56], fill=(255, 250, 238),
              outline=pal["ink"], width=3)
    d.line([(w * 0.67, h * 0.50), (w * 0.67, h * 0.455)], fill=pal["ink"], width=3)
    d.line([(w * 0.67, h * 0.50), (w * 0.695, h * 0.515)], fill=pal["ink"], width=3)
    # 夜灯
    d.ellipse([w * 0.20, h * 0.86, w * 0.30, h * 0.96], fill=pal["glow"], outline=pal["ink"], width=3)


# ── 场景 9：餐桌 ───────────────────────────────────────
def scene_kitchen(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 吊柜
    for i in range(3):
        x0 = w * (0.04 + i * 0.32)
        d.rectangle([x0, h * 0.02, x0 + w * 0.24, h * 0.26], fill=_mix(pal["mid"], (210, 170, 130), 0.4),
                    outline=pal["ink"], width=3)
        d.rectangle([x0 + 8, h * 0.04, x0 + w * 0.24 - 8, h * 0.24],
                    fill=_mix(pal["mid"], (255, 255, 255), 0.18), outline=pal["ink"], width=2)
    _hanging_plant(d, w, h, pal, x=0.06, seed=211)
    # 吊灯
    for cx in (0.16, 0.5, 0.84):
        d.line([(w * cx, 0), (w * cx, h * 0.12)], fill=pal["ink"], width=3)
        d.polygon([(w * (cx - 0.05), h * 0.22), (w * (cx + 0.05), h * 0.22),
                   (w * (cx + 0.03), h * 0.12), (w * (cx - 0.03), h * 0.12)],
                  fill=pal["glow"], outline=pal["ink"])
    # 橱柜
    d.rectangle([0, h * 0.34, w, h * 0.62], fill=_mix(pal["mid"], (200, 160, 120), 0.35),
                outline=pal["ink"], width=3)
    for i in range(4):
        x0 = w * (0.04 + i * 0.24)
        d.rectangle([x0, h * 0.38, x0 + w * 0.19, h * 0.58], fill=_mix(pal["mid"], (255, 255, 255), 0.16),
                    outline=pal["ink"], width=2)
    # 餐桌
    d.rectangle([0, h * 0.64, w, h * 0.72], fill=pal["near"], outline=pal["ink"], width=4)
    d.rectangle([0, h * 0.72, w, h], fill=_dark(pal["near"], 0.92))
    # 碗 + 筷
    d.pieslice([w * 0.30, h * 0.50, w * 0.44, h * 0.64], 0, 180, fill=(255, 255, 255),
               outline=pal["ink"], width=3)
    d.ellipse([w * 0.335, h * 0.525, w * 0.405, h * 0.58], fill=_mix(pal["glow"], (240, 160, 90), 0.5))
    d.line([(w * 0.46, h * 0.52), (w * 0.50, h * 0.62)], fill=pal["ink"], width=4)
    d.line([(w * 0.485, h * 0.52), (w * 0.525, h * 0.62)], fill=pal["ink"], width=4)


# ── 场景 10：地铁/通勤 ────────────────────────────────
def scene_commute(d, w, h, pal):
    _sky_band(d, w, h, pal)
    _banner_text(d, w, h, pal, "地铁", y=0.02)
    # 站台标识
    d.rectangle([w * 0.06, h * 0.02, w * 0.24, h * 0.10], fill=pal["glow"],
                outline=pal["ink"], width=3)
    # 车窗
    d.rectangle([w * 0.05, h * 0.12, w * 0.95, h * 0.52], fill=_light(pal["glow"], 0.92),
                outline=pal["ink"], width=5)
    for i in range(1, 5):
        _vline(d, w * (0.05 + i * 0.18), h * 0.12, h * 0.52, pal["ink"], 5)
    # 窗外掠过的灯
    rnd = random.Random(31)
    for _ in range(12):
        x = rnd.uniform(0.05, 0.95) * w
        y = rnd.uniform(0.16, 0.48) * h
        d.ellipse([x, y, x + 12, y + 12], fill=_light(pal["glow"], 1.1))
    # 座椅
    d.rectangle([0, h * 0.60, w, h * 0.72], fill=pal["mid"], outline=pal["ink"], width=3)
    d.rectangle([0, h * 0.66, w, h], fill=_dark(pal["mid"], 0.85))
    # 吊环
    for cx in (0.2, 0.45, 0.7, 0.92):
        d.line([(w * cx, h * 0.12), (w * cx, h * 0.22)], fill=pal["ink"], width=4)
        d.ellipse([w * cx - 14, h * 0.22, w * cx + 14, h * 0.30], outline=pal["ink"], width=4)


# ── 场景 11：树林草地 ─────────────────────────────────
def scene_nature(d, w, h, pal):
    _sky_band(d, w, h, pal)
    _sky_sun(d, w, h, pal, x=0.50, y=0.16, r=0.10)
    _clouds(d, w, h, pal, n=4, ymax=0.28, seed=69)
    _birds(d, w, h, pal, n=5, seed=71)
    rnd = random.Random(41)
    # 远树
    for i in range(6):
        x = rnd.uniform(0, 1) * w
        tr = rnd.uniform(0.035, 0.07) * w
        th = rnd.uniform(0.16, 0.30) * h
        d.rectangle([x - tr * 0.12, h * 0.64 - th, x + tr * 0.12, h * 0.64], fill=_mix(pal["far"], pal["mid"], 0.4))
        d.ellipse([x - tr, h * 0.64 - th - tr, x + tr, h * 0.64 - th + tr * 0.6], fill=pal["far"])
    # 近树（大）
    for cx, s in ((0.08, 1.0), (0.90, 0.85)):
        x = w * cx
        tr = 0.09 * w * s
        th = 0.34 * h * s
        d.rectangle([x - tr * 0.16, h * 0.68 - th, x + tr * 0.16, h * 0.68], fill=pal["near"],
                    outline=pal["ink"], width=3)
        d.ellipse([x - tr, h * 0.68 - th - tr * 0.9, x + tr, h * 0.68 - th + tr * 0.5],
                  fill=pal["mid"], outline=pal["ink"], width=3)
    # 草地
    d.rectangle([0, h * 0.66, w, h], fill=_mix(pal["near"], (128, 172, 88), 0.55))
    _hline(d, 0, w, h * 0.66, pal["ink"], 4)
    for _ in range(22):
        tx = rnd.uniform(0, 1) * w
        ty = rnd.uniform(0.70, 0.98) * h
        d.line([(tx, ty), (tx + rnd.uniform(-6, 6), ty - h * 0.045)], fill=_dark(pal["near"], 0.72), width=3)


# ── 场景 12：钱 / 存钱 ─────────────────────────────────
def scene_money(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上部：硬币雨 + 计算器
    rnd0 = random.Random(49)
    for _ in range(11):
        cx = rnd0.uniform(0.03, 0.95) * w
        cy = rnd0.uniform(0.03, 0.30) * h
        r = rnd0.uniform(0.014, 0.024) * w
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(246, 196, 62),
                  outline=pal["ink"], width=3)
    # 计算器
    d.rounded_rectangle([w * 0.70, h * 0.04, w * 0.94, h * 0.30], radius=8,
                        fill=_dark(pal["near"], 0.55), outline=pal["ink"], width=4)
    d.rectangle([w * 0.73, h * 0.07, w * 0.91, h * 0.13], fill=pal["glow"],
                outline=pal["ink"], width=2)
    for r_ in range(3):
        for c_ in range(4):
            x = w * (0.72 + c_ * 0.052)
            y = h * (0.16 + r_ * 0.045)
            d.rectangle([x, y, x + w * 0.036, y + h * 0.03],
                        fill=_mix(pal["near"], (255, 255, 255), 0.35), outline=pal["ink"], width=1)
    # 存钱罐
    d.ellipse([w * 0.08, h * 0.36, w * 0.40, h * 0.74], fill=_mix(pal["mid"], (236, 130, 120), 0.55),
              outline=pal["ink"], width=4)
    d.ellipse([w * 0.30, h * 0.46, w * 0.38, h * 0.58], fill=_mix(pal["mid"], (255, 255, 255), 0.35),
              outline=pal["ink"], width=3)
    d.polygon([(w * 0.16, h * 0.34), (w * 0.28, h * 0.34), (w * 0.24, h * 0.22)], fill=pal["near"],
              outline=pal["ink"], width=3)
    # 硬币缝
    d.rectangle([w * 0.15, h * 0.50, w * 0.28, h * 0.54], fill=_dark(pal["near"], 0.8))
    # 钞票堆
    rnd = random.Random(51)
    for i in range(6):
        x = w * (0.46 + rnd.uniform(-0.03, 0.05))
        y = h * (0.60 + i * 0.045)
        ang = rnd.uniform(-8, 8)
        col = _mix(pal["glow"], (150, 200, 150), rnd.uniform(0, 0.4))
        d.polygon([(x, y), (x + w * 0.26, y - 6), (x + w * 0.28, y + 14), (x + 2, y + 18)],
                  fill=col, outline=pal["ink"], width=2)
    # 金币
    for _ in range(9):
        cx = rnd.uniform(0.44, 0.96) * w
        cy = rnd.uniform(0.20, 0.56) * h
        r = rnd.uniform(0.016, 0.026) * w
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(246, 196, 62), outline=pal["ink"], width=3)
    d.rectangle([0, h * 0.80, w, h], fill=pal["near"])


# ── 场景 13：书架 ─────────────────────────────────────
def scene_books(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上层书架（够到顶部）
    d.rectangle([w * 0.02, h * 0.02, w * 0.98, h * 0.30], fill=pal["mid"], outline=pal["ink"], width=4)
    rnd0 = random.Random(59)
    x = w * 0.06
    while x < w * 0.92:
        bw = rnd0.uniform(0.020, 0.038) * w
        bh = rnd0.uniform(0.60, 0.92) * (h * 0.24)
        col = _mix(pal["near"], (rnd0.randint(180, 240), rnd0.randint(120, 200), rnd0.randint(120, 200)), 0.55)
        d.rectangle([x, h * 0.28 - bh, x + bw, h * 0.28], fill=col, outline=pal["ink"], width=2)
        x += bw + rnd0.uniform(0.002, 0.008) * w
    d.rectangle([w * 0.04, h * 0.28, w * 0.96, h * 0.30], fill=_dark(pal["near"], 0.85),
                outline=pal["ink"], width=3)
    # 书架
    d.rectangle([w * 0.02, h * 0.08, w * 0.98, h * 0.92], fill=pal["mid"], outline=pal["ink"], width=4)
    rnd = random.Random(61)
    for row in range(3):
        y0 = h * (0.12 + row * 0.27)
        y1 = y0 + h * 0.23
        d.rectangle([w * 0.06, y1 - 8, w * 0.94, y1], fill=_dark(pal["near"], 0.85))
        x = w * 0.08
        while x < w * 0.90:
            bw = rnd.uniform(0.020, 0.040) * w
            bh = rnd.uniform(0.62, 0.95) * (y1 - y0)
            col = _mix(pal["near"], (rnd.randint(180, 240), rnd.randint(120, 200), rnd.randint(120, 200)), 0.55)
            d.rectangle([x, y1 - 8 - bh, x + bw, y1 - 8], fill=col, outline=pal["ink"], width=2)
            x += bw + rnd.uniform(0.002, 0.008) * w


# ── 场景 14：相机 / 拍照 ───────────────────────────────
def scene_camera(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 背景光斑
    rnd = random.Random(71)
    for _ in range(16):
        cx = rnd.uniform(0, 1) * w
        cy = rnd.uniform(0.05, 0.85) * h
        r = rnd.uniform(0.02, 0.05) * w
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_mix(pal["far"], pal["glow"], 0.5))
    # 大相机
    cx, cy = w * 0.72, h * 0.46
    bw, bh = w * 0.34, h * 0.40
    d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], radius=20,
                        fill=_dark(pal["near"], 0.75), outline=pal["ink"], width=5)
    d.rectangle([cx - bw * 0.16, cy - bh / 2 - 26, cx + bw * 0.10, cy - bh / 2], fill=_dark(pal["near"], 0.6),
                outline=pal["ink"], width=4)
    r = bw * 0.26
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pal["glow"], outline=pal["ink"], width=5)
    d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55], fill=pal["far"],
              outline=pal["ink"], width=3)
    # 取景框（四宫格辅助线）
    for i in range(1, 3):
        _vline(d, w * i / 3, h * 0.08, h * 0.92, _mix(pal["ink"], (255, 255, 255), 0.55), 2)
        _hline(d, 0, w, h * (0.08 + i * 0.28), _mix(pal["ink"], (255, 255, 255), 0.55), 2)


# ── 场景 15：键盘特写 ─────────────────────────────────
def scene_keyboard(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 放大的键盘（透视）
    d.polygon([(w * 0.10, h * 0.34), (w * 1.02, h * 0.24), (w * 1.02, h * 0.86), (w * 0.04, h * 0.92)],
              fill=_dark(pal["near"], 0.72), outline=pal["ink"], width=5)
    rnd = random.Random(81)
    for row in range(4):
        t0 = row / 4
        t1 = (row + 1) / 4
        y0 = h * (0.36 + t0 * 0.52)
        y1 = h * (0.36 + t1 * 0.52)
        x = w * 0.13
        while x < w * 0.99:
            kw = rnd.uniform(0.035, 0.062) * w
            kh = (y1 - y0) * 0.72
            col = _mix(pal["near"], (255, 255, 255), 0.25 + 0.1 * (row % 2))
            d.rounded_rectangle([x, y0, x + kw, y0 + kh], radius=5, fill=col,
                                outline=pal["ink"], width=2)
            x += kw + w * 0.006
    # 手指
    for cx, cy, r in ((0.30, 0.30, 0.055), (0.40, 0.26, 0.05), (0.66, 0.22, 0.052)):
        d.ellipse([w * (cx - r), h * (cy - r * 0.8), w * (cx + r), h * (cy + r * 0.8)],
                  fill=(253, 222, 188), outline=pal["ink"], width=4)


# ── 场景 16：聊天气泡墙 ───────────────────────────────
def scene_chat(d, w, h, pal):
    _sky_band(d, w, h, pal)
    rnd = random.Random(91)
    # 漂浮气泡
    for _ in range(11):
        bw = rnd.uniform(0.10, 0.20) * w
        bh = rnd.uniform(0.09, 0.16) * h
        x = rnd.uniform(0.01, 0.80) * w
        y = rnd.uniform(0.04, 0.78) * h
        col = _mix(pal["glow"], (255, 255, 255), rnd.uniform(0.2, 0.6))
        _round(d, [x, y, x + bw, y + bh], 16, col, pal["ink"], 3)
        for i in range(2):
            ly = y + bh * (0.35 + i * 0.24)
            _hline(d, x + bw * 0.14, x + bw * rnd.uniform(0.55, 0.85), ly,
                   _mix(pal["ink"], (255, 255, 255), 0.4), 3)
    # 手机（前景提示）
    d.rounded_rectangle([w * 0.03, h * 0.58, w * 0.17, h * 1.02], radius=14,
                        fill=_dark(pal["near"], 0.6), outline=pal["ink"], width=4)
    d.rectangle([w * 0.05, h * 0.63, w * 0.15, h * 0.99], fill=pal["glow"])


# ── 场景 17：清单打勾墙 ───────────────────────────────
def scene_checklist(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 顶部挂的日程板
    d.rectangle([w * 0.16, h * 0.02, w * 0.84, h * 0.14], fill=_mix(pal["glow"], (255, 255, 255), 0.4),
                outline=pal["ink"], width=4)
    for i in range(7):
        x = w * (0.19 + i * 0.092)
        d.rectangle([x, h * 0.05, x + w * 0.062, h * 0.11],
                    fill=_mix(pal["far"], (255, 255, 255), 0.5), outline=pal["ink"], width=2)
    # 大清单板
    d.rectangle([w * 0.10, h * 0.06, w * 0.90, h * 0.94], fill=(252, 250, 242),
                outline=pal["ink"], width=5)
    rnd = random.Random(101)
    for i in range(7):
        y = h * (0.13 + i * 0.115)
        bx = w * 0.15
        done = i < 3
        d.rectangle([bx, y, bx + 30, y + 30], fill=(255, 255, 255), outline=pal["ink"], width=3)
        if done:
            d.line([(bx + 5, y + 15), (bx + 12, y + 25), (bx + 25, y + 4)], fill=(70, 158, 92), width=5)
        _hline(d, bx + 46, bx + 46 + rnd.uniform(0.22, 0.40) * w, y + 15,
               _mix(pal["ink"], (255, 255, 255), 0.45), 4)
        if done:
            _hline(d, bx + 46, bx + 46 + rnd.uniform(0.22, 0.40) * w, y + 15,
                   _mix(pal["ink"], (255, 255, 255), 0.7), 6)


# ── 场景 18：灯泡 ─────────────────────────────────────
def scene_bulb(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上部：灯泡上方的小灯泡群 + 齿轮
    rnd0 = random.Random(89)
    for _ in range(8):
        cx = rnd0.uniform(0.03, 0.95) * w
        cy = rnd0.uniform(0.03, 0.16) * h
        r = rnd0.uniform(0.016, 0.028) * w
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pal["glow"],
                  outline=pal["ink"], width=3)
        d.rectangle([cx - r * 0.35, cy + r, cx + r * 0.35, cy + r * 1.7],
                    fill=pal["mid"], outline=pal["ink"], width=2)
    d.ellipse([w * 0.82, h * 0.04, w * 0.94, h * 0.16], fill=_mix(pal["mid"], (190, 190, 200), 0.5),
              outline=pal["ink"], width=3)
    d.ellipse([w * 0.855, h * 0.075, w * 0.905, h * 0.125], fill=pal["glow"],
              outline=pal["ink"], width=2)
    # 放射光线
    cx, cy = w * 0.50, h * 0.42
    for i in range(16):
        a = math.tau * i / 16
        r0, r1 = h * 0.30, h * 0.72
        d.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                (cx + math.cos(a) * r1, cy + math.sin(a) * r1)],
               fill=_mix(pal["far"], pal["glow"], 0.6), width=6)
    r = h * 0.24
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pal["glow"], outline=pal["ink"], width=5)
    d.rectangle([cx - r * 0.38, cy + r * 0.86, cx + r * 0.38, cy + r * 1.42],
                fill=_mix(pal["mid"], (170, 170, 180), 0.5), outline=pal["ink"], width=4)
    for i in range(3):
        _hline(d, cx - r * 0.36, cx + r * 0.36, cy + r * (1.0 + i * 0.14), pal["ink"], 3)
    d.ellipse([cx - r * 0.5, cy - r * 0.5, cx - r * 0.1, cy - r * 0.1], fill=(255, 255, 255))


# ── 场景 19：挂钟 ─────────────────────────────────────
def scene_clockwall(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 大挂钟
    cx, cy, r = w * 0.74, h * 0.36, h * 0.30
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 250, 238), outline=pal["ink"], width=6)
    for i in range(12):
        a = math.tau * i / 12
        x1 = cx + math.cos(a) * r * 0.82
        y1 = cy + math.sin(a) * r * 0.82
        x2 = cx + math.cos(a) * r * 0.94
        y2 = cy + math.sin(a) * r * 0.94
        d.line([(x1, y1), (x2, y2)], fill=pal["ink"], width=4)
    d.line([(cx, cy), (cx, cy - r * 0.60)], fill=pal["ink"], width=7)
    d.line([(cx, cy), (cx + r * 0.42, cy + r * 0.26)], fill=pal["ink"], width=5)
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(214, 62, 44))
    # 侧面小钟（对比）
    cx2, cy2, r2 = w * 0.16, h * 0.52, h * 0.17
    d.ellipse([cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2], fill=(255, 250, 238), outline=pal["ink"], width=4)
    d.line([(cx2, cy2), (cx2, cy2 - r2 * 0.55)], fill=pal["ink"], width=5)
    d.line([(cx2, cy2), (cx2 + r2 * 0.40, cy2 + r2 * 0.30)], fill=pal["ink"], width=4)


# ── 场景 20：门 ───────────────────────────────────────
def scene_door(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 墙
    d.rectangle([0, 0, w, h], fill=_mix(pal["far"], (255, 255, 255), 0.25))
    # 门框
    d.rectangle([w * 0.30, h * 0.06, w * 0.74, h * 0.96], fill=_mix(pal["near"], (150, 100, 70), 0.45),
                outline=pal["ink"], width=5)
    # 门板
    d.rectangle([w * 0.335, h * 0.10, w * 0.705, h * 0.92], fill=_mix(pal["mid"], (160, 110, 78), 0.5),
                outline=pal["ink"], width=3)
    d.rectangle([w * 0.37, h * 0.16, w * 0.67, h * 0.44], fill=_mix(pal["mid"], (255, 255, 255), 0.12),
                outline=pal["ink"], width=2)
    d.rectangle([w * 0.37, h * 0.52, w * 0.67, h * 0.84], fill=_mix(pal["mid"], (255, 255, 255), 0.12),
                outline=pal["ink"], width=2)
    # 把手
    d.ellipse([w * 0.655, h * 0.50, w * 0.695, h * 0.56], fill=(250, 214, 120),
              outline=pal["ink"], width=3)
    # 门牌
    d.rectangle([w * 0.78, h * 0.14, w * 0.94, h * 0.28], fill=(255, 255, 255),
                outline=pal["ink"], width=4)
    # 地垫
    d.rectangle([w * 0.28, h * 0.92, w * 0.76, h], fill=_mix(pal["near"], (120, 140, 160), 0.4))


# ── 场景 21：雨伞 / 雨 ────────────────────────────────
def scene_rain(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 雨云
    for i, (cx, cy, r) in enumerate(((0.28, 0.22, 0.16), (0.52, 0.16, 0.20), (0.76, 0.24, 0.15))):
        d.ellipse([w * (cx - r), h * (cy - r * 0.6), w * (cx + r), h * (cy + r * 0.6)],
                  fill=_mix(pal["far"], (150, 150, 165), 0.5), outline=pal["ink"], width=3)
    # 雨线
    rnd = random.Random(111)
    for _ in range(48):
        x = rnd.uniform(0, 1) * w
        y = rnd.uniform(0.10, 0.95) * h
        d.line([(x, y), (x - 10, y + 26)], fill=_mix(pal["glow"], (255, 255, 255), 0.4), width=3)
    # 大伞
    cx = w * 0.30
    d.pieslice([cx - w * 0.24, h * 0.40, cx + w * 0.24, h * 0.88], 180, 360,
               fill=_mix(pal["near"], (230, 90, 80), 0.6), outline=pal["ink"], width=5)
    d.line([(cx, h * 0.40), (cx, h * 0.86)], fill=pal["ink"], width=5)
    d.arc([cx - w * 0.16, h * 0.46, cx - w * 0.02, h * 0.78], 0, 180, fill=pal["ink"], width=3)
    d.arc([cx + w * 0.02, h * 0.46, cx + w * 0.16, h * 0.78], 0, 180, fill=pal["ink"], width=3)
    # 水洼
    d.ellipse([w * 0.44, h * 0.86, w * 0.78, h * 0.98], fill=_mix(pal["far"], (160, 190, 210), 0.6),
              outline=pal["ink"], width=3)


# ── 场景 22：路 / 方向箭头 ────────────────────────────
def scene_road(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 远山
    d.polygon([(0, h * 0.52), (w * 0.22, h * 0.30), (w * 0.46, h * 0.52)], fill=pal["far"])
    d.polygon([(w * 0.42, h * 0.52), (w * 0.72, h * 0.26), (w * 1.02, h * 0.52)], fill=_mix(pal["far"], pal["mid"], 0.4))
    # 公路（透视梯形）
    d.polygon([(w * 0.42, h * 0.52), (w * 0.58, h * 0.52), (w * 0.96, h), (w * 0.04, h)],
              fill=_dark(pal["near"], 0.82), outline=pal["ink"])
    # 中线
    for i in range(5):
        t0 = i / 5
        t1 = t0 + 0.06
        y0 = h * (0.52 + t0 * 0.48)
        y1 = h * (0.52 + t1 * 0.48)
        w0 = w * (0.02 + t0 * 0.02)
        w1 = w * (0.005 + t1 * 0.012)
        d.polygon([(w * 0.5 - w0, y0), (w * 0.5 + w0, y0), (w * 0.5 + w1, y1), (w * 0.5 - w1, y1)],
                  fill=(255, 250, 220))
    # 路边箭头牌
    d.rectangle([w * 0.06, h * 0.18, w * 0.30, h * 0.30], fill=(255, 255, 255),
                outline=pal["ink"], width=4)
    d.polygon([(w * 0.12, h * 0.235), (w * 0.20, h * 0.235), (w * 0.20, h * 0.205),
               (w * 0.26, h * 0.24), (w * 0.20, h * 0.275), (w * 0.20, h * 0.245),
               (w * 0.12, h * 0.245)], fill=(70, 150, 92))
    d.rectangle([w * 0.175, h * 0.30, w * 0.185, h * 0.52], fill=pal["ink"], width=4)


# ── 场景 23：台阶 ─────────────────────────────────────
def scene_stairs(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上部：顶部的光 + 两侧栏杆扶手
    d.rectangle([w * 0.42, h * 0.02, w * 0.58, h * 0.14], fill=pal["glow"],
                outline=pal["ink"], width=4)
    for i in range(10):
        d.line([(w * (0.44 + i * 0.014), h * 0.14), (w * (0.36 + i * 0.028), h * 0.44)],
               fill=_mix(pal["glow"], (255, 255, 255), 0.4), width=5)
    # 两侧扶手柱
    for cx in (0.06, 0.94):
        d.rectangle([w * (cx - 0.018), h * 0.10, w * (cx + 0.018), h * 0.46],
                    fill=pal["near"], outline=pal["ink"], width=4)
        d.ellipse([w * (cx - 0.030), h * 0.06, w * (cx + 0.030), h * 0.12],
                  fill=pal["glow"], outline=pal["ink"], width=3)
    # 台阶（透视上升）
    n = 6
    for i in range(n):
        t = i / n
        y = h * (0.88 - t * 0.72)
        x0 = w * (0.50 - t * 0.34)
        x1 = w * (0.50 + t * 0.34)
        d.polygon([(x0, y), (x1, y), (x1, y - h * 0.055), (x0, y - h * 0.055)],
                  fill=_mix(pal["near"], (255, 255, 255), 0.10 + t * 0.3), outline=pal["ink"])
    # 顶端光
    d.rectangle([w * 0.44, h * 0.06, w * 0.56, h * 0.16], fill=pal["glow"], outline=pal["ink"], width=3)
    for i in range(9):
        d.line([(w * (0.46 + i * 0.010), h * 0.16), (w * (0.40 + i * 0.024), h * 0.40)],
               fill=_mix(pal["glow"], (255, 255, 255), 0.5), width=4)


# ── 场景 24：名片 / 简历 ───────────────────────────────
def scene_cards(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上方一排小卡片
    for i in range(3):
        x = w * (0.06 + i * 0.16)
        d.rounded_rectangle([x, h * 0.04, x + w * 0.13, h * 0.16], radius=8,
                            fill=_mix(pal["glow"], (255, 255, 255), 0.45), outline=pal["ink"], width=3)
        d.rectangle([x + 6, h * 0.06, x + w * 0.13 - 6, h * 0.09], fill=pal["near"])
    # 背后的简历
    d.rectangle([w * 0.06, h * 0.10, w * 0.46, h * 0.72], fill=(255, 253, 246),
                outline=pal["ink"], width=4)
    d.ellipse([w * 0.10, h * 0.14, w * 0.20, h * 0.30], fill=_mix(pal["mid"], (180, 180, 190), 0.5),
              outline=pal["ink"], width=3)
    for i in range(6):
        _hline(d, w * 0.23, w * (0.24 + 0.02 * (i % 3)), h * (0.16 + i * 0.055),
               _mix(pal["ink"], (255, 255, 255), 0.5), 3)
    for i in range(4):
        _hline(d, w * 0.10, w * (0.20 + 0.16 * (i % 2)), h * (0.36 + i * 0.06),
               _mix(pal["ink"], (255, 255, 255), 0.6), 3)
    # 前景名片
    d.rounded_rectangle([w * 0.44, h * 0.44, w * 0.92, h * 0.76], radius=12,
                        fill=(255, 255, 255), outline=pal["ink"], width=5)
    d.rectangle([w * 0.46, h * 0.46, w * 0.54, h * 0.74], fill=pal["near"])
    for i in range(3):
        _hline(d, w * 0.57, w * (0.64 + 0.12 * (i % 2)), h * (0.52 + i * 0.08),
               _mix(pal["ink"], (255, 255, 255), 0.45), 4)
    # 两张名片（对比）
    d.rounded_rectangle([w * 0.52, h * 0.20, w * 0.90, h * 0.42], radius=10,
                        fill=_mix(pal["glow"], (255, 255, 255), 0.3), outline=pal["ink"], width=4)


# ── 场景 25：地图 ─────────────────────────────────────
def scene_map(d, w, h, pal):
    _sky_band(d, w, h, pal)
    _frame_posters(d, w, h, pal, seed=221)
    # 背景地图框（放大版的第二张）
    d.rounded_rectangle([w * 0.60, h * 0.02, w * 0.98, h * 0.30], radius=12,
                        fill=_mix(pal["far"], (245, 238, 216), 0.6), outline=pal["ink"], width=4)
    for i in range(4):
        _hline(d, w * 0.64, w * (0.70 + 0.06 * (i % 3)), h * (0.07 + i * 0.055),
               _mix(pal["ink"], (255, 255, 255), 0.45), 3)
    d.ellipse([w * 0.82, h * 0.10, w * 0.90, h * 0.22], fill=pal["glow"],
              outline=pal["ink"], width=3)
    # 地图底
    d.rounded_rectangle([w * 0.04, h * 0.08, w * 0.96, h * 0.92], radius=16,
                        fill=(250, 244, 224), outline=pal["ink"], width=5)
    rnd = random.Random(121)
    # 区块
    for _ in range(9):
        x = rnd.uniform(0.08, 0.72) * w
        y = rnd.uniform(0.12, 0.66) * h
        bw = rnd.uniform(0.07, 0.16) * w
        bh = rnd.uniform(0.08, 0.18) * h
        d.rectangle([x, y, x + bw, y + bh], fill=_mix(pal["far"], (190, 210, 180), 0.6),
                    outline=pal["ink"], width=2)
    # 路线
    pts = [(0.10, 0.74), (0.28, 0.58), (0.46, 0.62), (0.66, 0.40), (0.86, 0.26)]
    d.line([(w * a, h * b) for a, b in pts], fill=(214, 62, 44), width=7, joint="curve")
    for a, b in pts:
        d.ellipse([w * a - 9, h * b - 9, w * a + 9, h * b + 9], fill=(255, 255, 255),
                  outline=(214, 62, 44), width=4)
    # 定位针
    cx, cy = w * 0.66, h * 0.40
    d.polygon([(cx, cy - 44), (cx - 15, cy + 12), (cx + 15, cy + 12)], fill=(214, 62, 44),
              outline=pal["ink"], width=3)
    d.ellipse([cx - 9, cy - 12, cx + 9, cy + 6], fill=(255, 255, 255), outline=pal["ink"], width=3)


# ── 场景 26：健身房 ───────────────────────────────────
def scene_gym(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 窗
    d.rectangle([w * 0.56, h * 0.08, w * 0.94, h * 0.44], fill=_light(pal["glow"], 0.98),
                outline=pal["ink"], width=4)
    # 杠铃架
    d.rectangle([w * 0.06, h * 0.14, w * 0.10, h * 0.82], fill=pal["near"], outline=pal["ink"], width=4)
    d.rectangle([w * 0.42, h * 0.14, w * 0.46, h * 0.82], fill=pal["near"], outline=pal["ink"], width=4)
    d.rectangle([w * 0.04, h * 0.26, w * 0.48, h * 0.31], fill=pal["mid"], outline=pal["ink"], width=3)
    # 杠铃
    d.rectangle([w * 0.02, h * 0.20, w * 0.50, h * 0.245], fill=_mix(pal["near"], (150, 150, 160), 0.5),
                outline=pal["ink"], width=4)
    for cx in (0.10, 0.38):
        d.rectangle([w * cx, h * 0.155, w * (cx + 0.05), h * 0.29], fill=(70, 70, 78),
                    outline=pal["ink"], width=3)
    # 地面
    d.rectangle([0, h * 0.80, w, h], fill=pal["near"])
    _hline(d, 0, w, h * 0.80, pal["ink"], 4)


# ── 场景 27：咖啡馆 ───────────────────────────────────
def scene_cafe(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 吧台后架
    d.rectangle([w * 0.02, h * 0.06, w * 0.42, h * 0.60], fill=_mix(pal["far"], (170, 130, 95), 0.4),
                outline=pal["ink"], width=4)
    for r in range(3):
        y = h * (0.14 + r * 0.16)
        d.rectangle([w * 0.05, y + h * 0.10, w * 0.39, y + h * 0.13], fill=_dark(pal["near"], 0.8))
        for i in range(6):
            x = w * (0.06 + i * 0.055)
            d.rectangle([x, y, x + w * 0.035, y + h * 0.10],
                        fill=_mix(pal["mid"], (rnd_color(i, r)), 0.5), outline=pal["ink"], width=2)
    # 桌
    d.rectangle([0, h * 0.70, w, h * 0.78], fill=pal["near"], outline=pal["ink"], width=4)
    d.rectangle([0, h * 0.78, w, h], fill=_dark(pal["near"], 0.9))
    # 杯子
    d.rounded_rectangle([w * 0.56, h * 0.56, w * 0.66, h * 0.71], radius=8,
                        fill=(255, 255, 255), outline=pal["ink"], width=4)
    d.arc([w * 0.645, h * 0.59, w * 0.695, h * 0.66], 270, 90, fill=pal["ink"], width=4)
    d.ellipse([w * 0.565, h * 0.555, w * 0.655, h * 0.585], fill=(120, 80, 52))
    # 笔记本
    d.polygon([(w * 0.30, h * 0.64), (w * 0.48, h * 0.625), (w * 0.50, h * 0.70), (w * 0.32, h * 0.715)],
              fill=(255, 252, 242), outline=pal["ink"], width=3)


def rnd_color(i, r):
    return (200 - i * 12, 150 + r * 18, 130 + i * 9)


# ── 场景 28：睡 / 闹钟夜 ──────────────────────────────
def scene_night(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 月亮
    d.ellipse([w * 0.74, h * 0.08, w * 0.88, h * 0.30], fill=(255, 250, 220),
              outline=pal["ink"], width=4)
    d.ellipse([w * 0.70, h * 0.05, w * 0.84, h * 0.27], fill=pal["far"])
    # 星星
    rnd = random.Random(131)
    for _ in range(22):
        x = rnd.uniform(0.02, 0.95) * w
        y = rnd.uniform(0.03, 0.42) * h
        r = rnd.uniform(2, 5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 220))
    # 窗框
    d.rectangle([w * 0.04, h * 0.04, w * 0.60, h * 0.50], fill=None, outline=pal["ink"], width=6)
    _vline(d, w * 0.32, h * 0.04, h * 0.50, pal["ink"], 5)
    # 床沿
    d.rectangle([0, h * 0.72, w, h], fill=pal["near"], outline=pal["ink"], width=4)
    d.rounded_rectangle([w * 0.08, h * 0.62, w * 0.30, h * 0.74], radius=14,
                        fill=(255, 252, 242), outline=pal["ink"], width=4)


# ── 场景 29：文件柜 / 抽屉 ────────────────────────────
def scene_cabinet(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 三层抽屉柜
    for i in range(3):
        y0 = h * (0.10 + i * 0.28)
        d.rectangle([w * 0.02, y0, w * 0.40, y0 + h * 0.25], fill=pal["mid"],
                    outline=pal["ink"], width=4)
        d.rectangle([w * 0.05, y0 + h * 0.05, w * 0.37, y0 + h * 0.20],
                    fill=_mix(pal["near"], (255, 255, 255), 0.12), outline=pal["ink"], width=2)
        d.rectangle([w * 0.17, y0 + h * 0.11, w * 0.25, y0 + h * 0.135],
                    fill=_dark(pal["near"], 0.7), outline=pal["ink"], width=2)
    # 右侧散落文件
    rnd = random.Random(141)
    for i in range(7):
        x = w * (0.46 + rnd.uniform(0, 0.10))
        y = h * (0.62 + i * 0.05)
        d.polygon([(x, y), (x + w * 0.32, y - 8), (x + w * 0.34, y + 12), (x + 2, y + 18)],
                  fill=_mix(pal["glow"], (255, 255, 255), 0.45), outline=pal["ink"], width=2)
    d.rectangle([0, h * 0.86, w, h], fill=pal["near"])


# ── 场景 30：地板 / 整理 ──────────────────────────────
def scene_floor(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上部：墙面 + 挂画 + 搁板
    d.rectangle([0, 0, w, h * 0.38], fill=_mix(pal["far"], (255, 255, 255), 0.30))
    _hline(d, 0, w, h * 0.38, pal["ink"], 4)
    _frame_posters(d, w, h, pal, seed=151)
    _wall_shelf(d, w, h, pal, y=0.20, seed=153)
    _hanging_plant(d, w, h, pal, x=0.92, seed=155)
    # 地板透视
    for i in range(7):
        x0 = w * (0.5 + (i - 3) * 0.16)
        d.line([(w * 0.5, h * 0.36), (x0 * 1.6, h)], fill=_mix(pal["far"], pal["near"], 0.5), width=3)
    for i in range(5):
        y = h * (0.36 + (i / 5) ** 1.6 * 0.64)
        _hline(d, 0, w, y, _mix(pal["far"], pal["near"], 0.45), 3)
    d.rectangle([0, h * 0.34, w, h * 0.38], fill=_mix(pal["mid"], (255, 255, 255), 0.2))
    # 杂物堆
    rnd = random.Random(151)
    for _ in range(12):
        x = rnd.uniform(0.02, 0.42) * w
        y = rnd.uniform(0.46, 0.94) * h
        bw = rnd.uniform(0.03, 0.09) * w
        bh = rnd.uniform(0.03, 0.08) * h
        col = _mix(pal["near"], (rnd.randint(150, 240), rnd.randint(130, 210), rnd.randint(120, 200)), 0.5)
        d.rectangle([x, y, x + bw, y + bh], fill=col, outline=pal["ink"], width=2)


# ── 场景 31：电台 / 播客 ──────────────────────────────
def scene_radio(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 大麦克风
    cx = w * 0.72
    d.rounded_rectangle([cx - w * 0.09, h * 0.30, cx + w * 0.09, h * 0.62], radius=26,
                        fill=_mix(pal["near"], (150, 150, 160), 0.45), outline=pal["ink"], width=5)
    for i in range(5):
        _hline(d, cx - w * 0.075, cx + w * 0.075, h * (0.35 + i * 0.055), pal["ink"], 3)
    d.rectangle([cx - w * 0.02, h * 0.62, cx + w * 0.02, h * 0.80], fill=pal["ink"])
    d.ellipse([cx - w * 0.10, h * 0.78, cx + w * 0.10, h * 0.86], fill=pal["near"], outline=pal["ink"], width=4)
    # 声波
    for i, r in enumerate((0.10, 0.15, 0.20, 0.25)):
        d.arc([cx - w * r, h * 0.46 - w * r, cx + w * r, h * 0.46 + w * r], 200, 340,
              fill=_mix(pal["glow"], (255, 255, 255), 0.5), width=5)
    # 左边唱片
    d.ellipse([w * 0.08, h * 0.32, w * 0.34, h * 0.76], fill=_dark(pal["near"], 0.7),
              outline=pal["ink"], width=5)
    d.ellipse([w * 0.13, h * 0.40, w * 0.29, h * 0.68], outline=_mix(pal["ink"], (255, 255, 255), 0.5), width=3)
    d.ellipse([w * 0.195, h * 0.50, w * 0.225, h * 0.58], fill=(214, 62, 44), outline=pal["ink"], width=2)


# ── 场景 32：晾衣 / 阳台 ──────────────────────────────
def scene_balcony(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 天空 + 云
    for cx, cy, r in ((0.22, 0.16, 0.11), (0.62, 0.11, 0.13)):
        d.ellipse([w * (cx - r), h * (cy - r * 0.6), w * (cx + r), h * (cy + r * 0.6)],
                  fill=(255, 255, 255))
    # 栏杆
    d.rectangle([0, h * 0.52, w, h], fill=_mix(pal["near"], (200, 200, 210), 0.4))
    for i in range(12):
        x = w * (0.02 + i * 0.084)
        d.rectangle([x, h * 0.30, x + 8, h * 0.56], fill=pal["mid"], outline=pal["ink"], width=2)
    d.rectangle([0, h * 0.28, w, h * 0.32], fill=pal["mid"], outline=pal["ink"], width=3)
    # 晾晒的衣物
    for cx, col in ((0.14, (240, 140, 120)), (0.32, (120, 170, 230)), (0.50, (240, 200, 110))):
        d.polygon([(w * cx, h * 0.32), (w * (cx + 0.10), h * 0.32),
                   (w * (cx + 0.09), h * 0.54), (w * (cx + 0.01), h * 0.54)],
                  fill=col, outline=pal["ink"], width=3)
    # 盆栽
    d.rectangle([w * 0.82, h * 0.40, w * 0.90, h * 0.54], fill=(206, 118, 74), outline=pal["ink"], width=3)
    for a in (-40, -12, 16, 42):
        rad = math.radians(a)
        d.line([(w * 0.86, h * 0.40), (w * 0.86 + math.sin(rad) * 46, h * 0.40 - math.cos(rad) * 46)],
               fill=(64, 148, 74), width=5)


# ── 场景 33：镜子 / 自拍 ──────────────────────────────
def scene_mirror(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 大镜子
    d.rounded_rectangle([w * 0.30, h * 0.06, w * 0.80, h * 0.94], radius=40,
                        fill=_mix(pal["glow"], (255, 255, 255), 0.4), outline=pal["ink"], width=6)
    d.rounded_rectangle([w * 0.34, h * 0.10, w * 0.76, h * 0.90], radius=32,
                        fill=_mix(pal["far"], (255, 255, 255), 0.55), outline=pal["ink"], width=3)
    # 镜面反光斜条
    for i in range(3):
        x0 = w * (0.36 + i * 0.13)
        d.polygon([(x0, h * 0.12), (x0 + 26, h * 0.12), (x0 - 70, h * 0.88), (x0 - 96, h * 0.88)],
                  fill=(255, 255, 255))
    # 镜子上的小贴纸
    d.rectangle([w * 0.66, h * 0.62, w * 0.74, h * 0.72], fill=(255, 214, 66), outline=pal["ink"], width=3)
    # 边框灯
    for cx, cy in ((0.30, 0.12), (0.80, 0.12), (0.30, 0.88), (0.80, 0.88)):
        d.ellipse([w * cx - 12, h * cy - 12, w * cx + 12, h * cy + 12],
                  fill=(255, 246, 200), outline=pal["ink"], width=3)


# ── 场景 34：跑步 / 运动 ──────────────────────────────
def scene_running(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上部：赛道看台 + 旗帜
    d.rectangle([0, h * 0.06, w, h * 0.30], fill=_mix(pal["mid"], pal["near"], 0.3),
                outline=pal["ink"], width=3)
    for i in range(12):
        x = w * (0.02 + i * 0.083)
        d.rectangle([x, h * 0.09, x + w * 0.045, h * 0.20],
                    fill=_mix(pal["far"], (200, 210, 225), 0.45), outline=pal["ink"], width=2)
    d.rectangle([0, h * 0.30, w, h * 0.33], fill=pal["near"], outline=pal["ink"], width=3)
    _bunting(d, w, h, pal, y=0.0, n=10, seed=87)
    # 跑道
    d.polygon([(w * 0.30, h * 0.44), (w * 0.52, h * 0.44), (w * 0.96, h), (w * 0.02, h)],
              fill=_mix(pal["near"], (230, 120, 90), 0.45), outline=pal["ink"])
    for i in range(5):
        t0 = i / 5
        t1 = t0 + 0.07
        y0 = h * (0.44 + t0 * 0.56)
        y1 = h * (0.44 + t1 * 0.56)
        w0 = w * (0.005 + t0 * 0.010)
        w1 = w * (0.002 + t1 * 0.008)
        d.polygon([(w * 0.5 - w0, y0), (w * 0.5 + w0, y0), (w * 0.5 + w1, y1), (w * 0.5 - w1, y1)],
                  fill=(255, 252, 240))
    # 速度线
    for i in range(14):
        y = h * (0.50 + i * 0.033)
        d.line([(0, y), (w * 0.30, y)], fill=_mix(pal["glow"], (255, 255, 255), 0.55), width=5)
    # 远处终点
    d.rectangle([w * 0.34, h * 0.30, w * 0.48, h * 0.44], fill=(255, 255, 255),
                outline=pal["ink"], width=3)
    for i in range(6):
        d.rectangle([w * (0.34 + i * 0.023), h * 0.30, w * (0.354 + i * 0.023), h * 0.44],
                    fill=(34, 30, 28) if i % 2 == 0 else (255, 255, 255))


# ── 场景 35：人群 / 社交 ──────────────────────────────
def scene_crowd(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上部：横幅 + 灯串（聚会/饭局场景）
    _bunting(d, w, h, pal, y=0.03, n=11, seed=73)
    _hanging_lights(d, w, h, pal, n=6, y=0.0, seed=75)
    rnd = random.Random(161)
    # 背景人剪影
    for i in range(10):
        x = w * (0.02 + i * 0.105) + rnd.uniform(-14, 14)
        y = h * 0.66
        hh = rnd.uniform(0.22, 0.34) * h
        col = _mix(pal["mid"], pal["near"], rnd.uniform(0.2, 0.7))
        d.ellipse([x - hh * 0.16, y - hh, x + hh * 0.16, y - hh * 0.66], fill=col, outline=pal["ink"], width=2)
        d.rounded_rectangle([x - hh * 0.20, y - hh * 0.68, x + hh * 0.20, y], radius=10,
                            fill=col, outline=pal["ink"], width=2)
    # 连接线（社交网络）
    nodes = [(w * 0.16, h * 0.44), (w * 0.42, h * 0.30), (w * 0.68, h * 0.42),
             (w * 0.30, h * 0.62), (w * 0.60, h * 0.62)]
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if rnd.random() < 0.5:
                d.line([nodes[i], nodes[j]], fill=_mix(pal["ink"], (255, 255, 255), 0.55), width=3)
    for x, y in nodes:
        d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=pal["glow"], outline=pal["ink"], width=3)
    d.rectangle([0, h * 0.88, w, h], fill=pal["near"])


# ── 场景 36：抽屉 / 收纳 ──────────────────────────────
def scene_drawer(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上部：贴纸 / 便签墙
    rnd0 = random.Random(173)
    for _ in range(12):
        x = rnd0.uniform(0.05, 0.92) * w
        y = rnd0.uniform(0.04, 0.36) * h
        bw = rnd0.uniform(0.045, 0.085) * w
        bh = bw * rnd0.uniform(0.8, 1.2)
        col = [(255, 214, 66), (240, 150, 150), (150, 210, 230), (170, 230, 150)][rnd0.randint(0, 3)]
        d.rectangle([x, y, x + bw, y + bh], fill=col, outline=pal["ink"], width=2)
        for k in range(2):
            _hline(d, x + 6, x + bw - 8, y + bh * (0.35 + k * 0.28), pal["ink"], 2)
    # 打开的抽屉
    d.polygon([(w * 0.14, h * 0.56), (w * 0.86, h * 0.56), (w * 0.94, h * 0.94), (w * 0.06, h * 0.94)],
              fill=_dark(pal["near"], 0.72), outline=pal["ink"], width=5)
    d.rectangle([w * 0.16, h * 0.50, w * 0.84, h * 0.57], fill=pal["near"], outline=pal["ink"], width=4)
    # 里面的东西
    rnd = random.Random(171)
    for _ in range(14):
        x = rnd.uniform(0.18, 0.74) * w
        y = rnd.uniform(0.58, 0.84) * h
        bw = rnd.uniform(0.04, 0.10) * w
        bh = rnd.uniform(0.04, 0.10) * h
        col = _mix(pal["glow"], (rnd.randint(150, 245), rnd.randint(140, 220), rnd.randint(130, 210)), 0.55)
        d.rectangle([x, y, x + bw, y + bh], fill=col, outline=pal["ink"], width=2)
    # 标签贴纸
    d.rectangle([w * 0.44, h * 0.16, w * 0.62, h * 0.30], fill=(255, 214, 66), outline=pal["ink"], width=4)
    d.line([(w * 0.47, h * 0.23), (w * 0.59, h * 0.23)], fill=pal["ink"], width=4)
    d.line([(w * 0.47, h * 0.27), (w * 0.55, h * 0.27)], fill=pal["ink"], width=3)


# ── 场景 37：声音 / 说话 ──────────────────────────────
def scene_voice(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 声波柱
    rnd = random.Random(181)
    cx = w * 0.68
    base = h * 0.62
    for i in range(22):
        x = cx - w * 0.24 + i * w * 0.022
        amp = (0.5 + 0.5 * math.sin(i * 0.9)) * (0.6 + 0.4 * math.sin(i * 0.31))
        hh = amp * h * 0.34
        col = _mix(pal["near"], (255, 214, 66), 0.35 + 0.4 * amp)
        d.rounded_rectangle([x, base - hh, x + w * 0.014, base + hh], radius=6,
                            fill=col, outline=pal["ink"], width=2)
    # 大嘴说话
    d.ellipse([w * 0.08, h * 0.24, w * 0.42, h * 0.72], fill=(253, 222, 188),
              outline=pal["ink"], width=5)
    d.ellipse([w * 0.14, h * 0.36, w * 0.26, h * 0.54], fill=(255, 255, 255), outline=pal["ink"], width=3)
    d.ellipse([w * 0.15, h * 0.38, w * 0.22, h * 0.46], fill=(74, 132, 214))
    d.pieslice([w * 0.16, h * 0.46, w * 0.34, h * 0.66], 0, 180, fill=(180, 70, 76),
               outline=pal["ink"], width=3)


# ── 场景 38：闹钟 / 时间紧迫 ───────────────────────────
def scene_alarm(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 上部：钟表店背景 —— 挂钟排 + 灯串
    for i in range(4):
        cx = w * (0.12 + i * 0.25)
        r = w * 0.045
        d.ellipse([cx - r, h * 0.06, cx + r, h * 0.06 + r * 2], fill=(255, 250, 238),
                  outline=pal["ink"], width=3)
        d.line([(cx, h * 0.06 + r), (cx, h * 0.06 + r * 0.45)], fill=pal["ink"], width=3)
    _hanging_lights(d, w, h, pal, n=6, y=0.0, seed=191)
    _bunting(d, w, h, pal, y=0.03, n=9, seed=193)
    # 大闹钟（对比两个）
    for cx, cy, r, fast in ((0.28, 0.42, 0.26, True), (0.72, 0.42, 0.26, False)):
        d.ellipse([w * (cx - r), h * (cy - r), w * (cx + r), h * (cy + r)],
                  fill=(255, 250, 238), outline=pal["ink"], width=6)
        for i in range(12):
            a = math.tau * i / 12
            d.line([(w * cx + math.cos(a) * r * w * 0.82, h * cy + math.sin(a) * r * h * 0.82),
                    (w * cx + math.cos(a) * r * w * 0.92, h * cy + math.sin(a) * r * h * 0.92)],
                   fill=pal["ink"], width=3)
        ang = 250 if fast else 150
        a = math.radians(ang)
        d.line([(w * cx, h * cy), (w * cx + math.cos(a) * r * w * 0.62, h * cy + math.sin(a) * r * h * 0.62)],
               fill=(214, 62, 44) if fast else pal["ink"], width=7)
        # 铃铛
        d.ellipse([w * (cx - r - 14), h * (cy - r - 10), w * (cx - r + 16), h * (cy - r + 22)],
                  fill=pal["mid"], outline=pal["ink"], width=3)
        d.ellipse([w * (cx + r - 16), h * (cy - r - 10), w * (cx + r + 14), h * (cy - r + 22)],
                  fill=pal["mid"], outline=pal["ink"], width=3)
        d.rectangle([w * cx - 14, h * (cy + r - 6), w * cx + 14, h * (cy + r + 24)],
                    fill=pal["mid"], outline=pal["ink"], width=3)
    # 地面
    d.rectangle([0, h * 0.82, w, h], fill=pal["near"])


# ── 场景 39：厨房灶台 ─────────────────────────────────
def scene_stove(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 瓷砖墙
    for r in range(4):
        for c in range(9):
            x0 = w * (0.02 + c * 0.11)
            y0 = h * (0.06 + r * 0.115)
            d.rectangle([x0, y0, x0 + w * 0.095, y0 + h * 0.10],
                        fill=_mix(pal["far"], (255, 255, 255), 0.35), outline=pal["ink"], width=2)
    # 灶台
    d.rectangle([0, h * 0.58, w, h * 0.66], fill=_dark(pal["near"], 0.7), outline=pal["ink"], width=4)
    d.rectangle([0, h * 0.66, w, h], fill=pal["near"], outline=pal["ink"], width=3)
    # 锅
    d.rectangle([w * 0.30, h * 0.44, w * 0.60, h * 0.58], fill=_dark(pal["mid"], 0.55),
                outline=pal["ink"], width=4)
    d.rectangle([w * 0.27, h * 0.40, w * 0.63, h * 0.45], fill=pal["mid"], outline=pal["ink"], width=4)
    # 火
    for cx in (0.38, 0.50):
        d.polygon([(w * (cx - 0.018), h * 0.58), (w * (cx + 0.018), h * 0.58),
                   (w * cx, h * 0.50)], fill=(240, 140, 60))
    # 蒸汽
    for i in range(3):
        x = w * (0.36 + i * 0.07)
        for k in range(4):
            yy = h * (0.38 - k * 0.055)
            d.arc([x - 14 + k * 3, yy - 12, x + 14 + k * 3, yy + 12], 200, 340,
                  fill=(255, 255, 255), width=3)


# ── 场景 40：派对 / 庆祝 ──────────────────────────────
def scene_party(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 彩旗
    for i in range(9):
        x0 = w * (0.02 + i * 0.11)
        col = [(240, 90, 80), (250, 200, 70), (90, 180, 220), (140, 210, 130)][i % 4]
        d.polygon([(x0, h * 0.04), (x0 + w * 0.08, h * 0.04), (x0 + w * 0.04, h * 0.18)],
                  fill=col, outline=pal["ink"], width=2)
    # 气球
    for cx, cy, r, col in ((0.18, 0.30, 0.055, (240, 100, 90)), (0.32, 0.20, 0.045, (250, 200, 80)),
                            (0.72, 0.26, 0.050, (110, 190, 230))):
        d.ellipse([w * (cx - r), h * (cy - r * 1.2), w * (cx + r), h * (cy + r * 1.2)],
                  fill=col, outline=pal["ink"], width=3)
        d.line([(w * cx, h * (cy + r * 1.2)), (w * (cx + 6), h * (cy + r * 2.6))],
               fill=pal["ink"], width=2)
    # 桌子 + 蛋糕
    d.rectangle([0, h * 0.70, w, h * 0.78], fill=pal["near"], outline=pal["ink"], width=4)
    d.rectangle([0, h * 0.78, w, h], fill=_dark(pal["near"], 0.9))
    d.rectangle([w * 0.42, h * 0.52, w * 0.58, h * 0.70], fill=(250, 220, 180), outline=pal["ink"], width=3)
    d.rectangle([w * 0.44, h * 0.46, w * 0.56, h * 0.54], fill=(240, 160, 170), outline=pal["ink"], width=3)
    d.line([(w * 0.50, h * 0.46), (w * 0.50, h * 0.38)], fill=pal["ink"], width=3)
    # 彩纸
    rnd = random.Random(191)
    for _ in range(20):
        x = rnd.uniform(0, 1) * w
        y = rnd.uniform(0.04, 0.55) * h
        col = [(240, 90, 80), (250, 200, 70), (110, 190, 230)][rnd.randint(0, 2)]
        d.polygon([(x, y), (x + 12, y + 8), (x + 4, y + 18)], fill=col)


# ── 场景 41：地铁卡 / 钱袋 ────────────────────────────
def scene_wallet(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 钱包
    d.rounded_rectangle([w * 0.18, h * 0.34, w * 0.82, h * 0.78], radius=16,
                        fill=_mix(pal["near"], (150, 100, 70), 0.5), outline=pal["ink"], width=5)
    d.rounded_rectangle([w * 0.20, h * 0.38, w * 0.80, h * 0.74], radius=12,
                        fill=_mix(pal["mid"], (180, 130, 90), 0.5), outline=pal["ink"], width=3)
    # 卡
    for i in range(4):
        y = h * (0.40 + i * 0.085)
        d.rounded_rectangle([w * 0.26, y, w * 0.74, y + h * 0.065], radius=6,
                            fill=(255, 255, 255), outline=pal["ink"], width=2)
        d.rectangle([w * 0.28, y + 6, w * 0.40, y + h * 0.045], fill=pal["glow"])
    # 硬币
    for i, cx in enumerate((0.24, 0.34, 0.44)):
        d.ellipse([w * cx, h * 0.80, w * (cx + 0.07), h * 0.90], fill=(246, 196, 62),
                  outline=pal["ink"], width=3)
    # 上方飘的钱
    for _ in range(5):
        cx = w * (0.22 + i * 0.13)
        d.rounded_rectangle([cx, h * 0.12, cx + w * 0.10, h * 0.24], radius=5,
                            fill=_mix(pal["glow"], (160, 200, 160), 0.4), outline=pal["ink"], width=3)


# ── 场景 42：练习 / 钢琴 ──────────────────────────────
def scene_practice(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 谱架 + 乐谱
    d.polygon([(w * 0.30, h * 0.16), (w * 0.78, h * 0.16), (w * 0.80, h * 0.44), (w * 0.28, h * 0.44)],
              fill=(255, 253, 246), outline=pal["ink"], width=4)
    for i in range(5):
        _hline(d, w * 0.31, w * 0.78, h * (0.22 + i * 0.05), pal["ink"], 2)
    for i in range(9):
        d.ellipse([w * (0.33 + i * 0.05), h * (0.20 + (i % 3) * 0.05), w * (0.345 + i * 0.05), h * (0.225 + (i % 3) * 0.05)],
                  fill=pal["ink"])
    # 钢琴键
    d.rectangle([w * 0.08, h * 0.66, w * 0.92, h * 0.86], fill=(255, 255, 255), outline=pal["ink"], width=5)
    for i in range(14):
        x = w * (0.09 + i * 0.059)
        d.line([(x, h * 0.66), (x, h * 0.86)], fill=pal["ink"], width=2)
    for i in range(1, 14, 3):
        x = w * (0.09 + i * 0.059)
        d.rectangle([x, h * 0.66, x + w * 0.032, h * 0.78], fill=(34, 30, 28))
    d.rectangle([w * 0.06, h * 0.86, w * 0.94, h], fill=pal["near"])


# ── 场景 43：打包 / 行李 ──────────────────────────────
def scene_luggage(d, w, h, pal):
    _sky_band(d, w, h, pal)
    # 窗外的飞机
    d.polygon([(w * 0.60, h * 0.14), (w * 0.86, h * 0.16), (w * 0.86, h * 0.24), (w * 0.60, h * 0.24)],
              fill=(255, 255, 255), outline=pal["ink"], width=3)
    d.polygon([(w * 0.66, h * 0.16), (w * 0.74, h * 0.08), (w * 0.78, h * 0.08), (w * 0.74, h * 0.16)],
              fill=(255, 255, 255), outline=pal["ink"], width=3)
    d.rectangle([w * 0.04, h * 0.04, w * 0.52, h * 0.34], fill=_light(pal["glow"], 0.95),
                outline=pal["ink"], width=4)
    # 行李箱
    d.rounded_rectangle([w * 0.58, h * 0.42, w * 0.86, h * 0.92], radius=14,
                        fill=_mix(pal["near"], (90, 110, 160), 0.5), outline=pal["ink"], width=5)
    d.rectangle([w * 0.62, h * 0.48, w * 0.70, h * 0.86], fill=_mix(pal["near"], (255, 255, 255), 0.18),
                outline=pal["ink"], width=2)
    d.rectangle([w * 0.63, h * 0.38, w * 0.81, h * 0.44], fill=pal["mid"], outline=pal["ink"], width=4)
    # 标签
    d.rectangle([w * 0.73, h * 0.50, w * 0.83, h * 0.58], fill=(255, 214, 66), outline=pal["ink"], width=3)
    # 地上的包
    d.rounded_rectangle([w * 0.14, h * 0.66, w * 0.42, h * 0.88], radius=12,
                        fill=_mix(pal["mid"], (200, 150, 110), 0.5), outline=pal["ink"], width=4)


# ── 场景 44：球场 / 运动场 ────────────────────────────
def scene_field(d, w, h, pal):
    _sky_band(d, w, h, pal)
    _sky_sun(d, w, h, pal, x=0.16, y=0.16, r=0.09)
    _clouds(d, w, h, pal, n=4, ymax=0.26, seed=201)
    # 看台
    for i in range(3):
        d.rectangle([0, h * (0.10 + i * 0.08), w, h * (0.14 + i * 0.08)],
                    fill=_mix(pal["mid"], pal["near"], i / 3), outline=pal["ink"], width=2)
        rnd = random.Random(200 + i)
        for j in range(24):
            x = w * (j / 24 + rnd.uniform(0, 0.02))
            d.ellipse([x, h * (0.08 + i * 0.08), x + 12, h * (0.12 + i * 0.08)],
                      fill=_mix(pal["far"], (rnd.randint(150, 240),) * 3, 0.5))
    # 球场
    d.rectangle([0, h * 0.36, w, h], fill=_mix(pal["near"], (110, 170, 90), 0.55))
    # 中圈
    d.ellipse([w * 0.30, h * 0.52, w * 0.70, h * 0.86], outline=(255, 255, 255), width=4)
    # 球门
    d.rectangle([w * 0.02, h * 0.44, w * 0.16, h * 0.78], fill=(255, 255, 255), outline=pal["ink"], width=3)
    for i in range(6):
        for j in range(4):
            d.rectangle([w * (0.02 + i * 0.023), h * (0.44 + j * 0.085),
                         w * (0.043 + i * 0.023), h * (0.525 + j * 0.085)],
                        outline=_mix(pal["ink"], (255, 255, 255), 0.6), width=1)
    # 球
    d.ellipse([w * 0.80, h * 0.72, w * 0.88, h * 0.86], fill=(255, 255, 255), outline=pal["ink"], width=3)
    d.polygon([(w * 0.83, h * 0.76), (w * 0.86, h * 0.77), (w * 0.855, h * 0.80), (w * 0.825, h * 0.80), (w * 0.82, h * 0.77)],
              fill=pal["ink"])


# ── 场景 45：花园 / 散步 ──────────────────────────────
def scene_garden(d, w, h, pal):
    _sky_band(d, w, h, pal)
    _sky_sun(d, w, h, pal, x=0.20, y=0.16, r=0.09)
    _clouds(d, w, h, pal, n=3, ymax=0.24, seed=241)
    _birds(d, w, h, pal, n=5, seed=243)
    # 小路
    d.polygon([(w * 0.36, h * 0.40), (w * 0.62, h * 0.40), (w * 0.98, h), (w * 0.02, h)],
              fill=_mix(pal["near"], (215, 200, 170), 0.6), outline=pal["ink"])
    for i in range(7):
        t = i / 7
        y = h * (0.40 + t * 0.60)
        hw = w * (0.13 + t * 0.30)
        d.ellipse([w * 0.5 - hw, y - 6, w * 0.5 + hw, y + 10],
                  fill=_mix(pal["near"], (150, 140, 120), 0.5))
    # 草地
    d.rectangle([0, h * 0.38, w, h * 0.46], fill=_mix(pal["near"], (120, 170, 88), 0.6))
    # 灌木
    rnd = random.Random(211)
    for cx in (0.08, 0.24, 0.80, 0.94):
        r = w * 0.075
        d.ellipse([w * cx - r, h * 0.24, w * cx + r, h * 0.44],
                  fill=_mix(pal["mid"], (96, 170, 88), 0.6), outline=pal["ink"], width=3)
    # 花
    for _ in range(12):
        cx = rnd.uniform(0.02, 0.98) * w
        cy = rnd.uniform(0.46, 0.92) * h
        col = [(240, 110, 100), (250, 210, 90), (240, 150, 190)][rnd.randint(0, 2)]
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=col)
    # 长椅
    d.rectangle([w * 0.04, h * 0.56, w * 0.28, h * 0.60], fill=_mix(pal["near"], (150, 110, 78), 0.5),
                outline=pal["ink"], width=3)
    d.rectangle([w * 0.04, h * 0.50, w * 0.28, h * 0.54], fill=_mix(pal["near"], (150, 110, 78), 0.5),
                outline=pal["ink"], width=3)
    d.rectangle([w * 0.06, h * 0.60, w * 0.08, h * 0.72], fill=pal["ink"])
    d.rectangle([w * 0.24, h * 0.60, w * 0.26, h * 0.72], fill=pal["ink"])


# ── 小元素库（点缀道具） ─────────────────────────────────
# 每个元素画在分镜的空白处，用来把画面和文案"扣"在一起。
# 签名统一： fn(d, x, y, s, pal)   s = 缩放，x,y = 底边中心

def _p_cup(d, x, y, s, pal):
    d.rounded_rectangle([x - 26 * s, y - 46 * s, x + 26 * s, y], radius=8 * s,
                        fill=(255, 255, 255), outline=INK, width=max(2, int(3 * s)))
    d.arc([x + 20 * s, y - 34 * s, x + 46 * s, y - 12 * s], 270, 90, fill=INK, width=max(2, int(3 * s)))
    d.ellipse([x - 24 * s, y - 50 * s, x + 24 * s, y - 38 * s], fill=(112, 76, 48), outline=INK, width=2)


def _p_mug(d, x, y, s, pal):
    _p_cup(d, x, y, s * 0.9, pal)
    d.ellipse([x - 22 * s, y - 44 * s, x + 22 * s, y - 34 * s], fill=(206, 96, 78), outline=INK, width=2)


def _p_notebook(d, x, y, s, pal):
    d.polygon([(x - 34 * s, y - 10 * s), (x + 34 * s, y - 16 * s),
               (x + 34 * s, y - 2 * s), (x - 34 * s, y + 4 * s)],
              fill=(255, 253, 246), outline=INK, width=max(2, int(2.4 * s)))
    for i in range(3):
        _hline(d, x - 24 * s, x + 22 * s, y - 12 * s + i * 5 * s, (150, 140, 130), 2)


def _p_pen(d, x, y, s, pal):
    d.line([(x - 28 * s, y), (x + 28 * s, y - 10 * s)], fill=(226, 78, 58), width=int(7 * s))
    d.polygon([(x + 28 * s, y - 10 * s), (x + 40 * s, y - 13 * s), (x + 30 * s, y - 2 * s)], fill=(240, 220, 180))


def _p_clock(d, x, y, s, pal):
    d.ellipse([x - 26 * s, y - 52 * s, x + 26 * s, y], fill=(255, 250, 238), outline=INK, width=max(2, int(3 * s)))
    d.line([(x, y - 26 * s), (x, y - 42 * s)], fill=INK, width=max(2, int(3 * s)))
    d.line([(x, y - 26 * s), (x + 15 * s, y - 18 * s)], fill=INK, width=max(2, int(2.4 * s)))


def _p_plant(d, x, y, s, pal):
    d.polygon([(x - 20 * s, y - 28 * s), (x + 20 * s, y - 28 * s),
               (x + 15 * s, y), (x - 15 * s, y)], fill=(206, 118, 74), outline=INK, width=max(2, int(2.6 * s)))
    for ang in (-48, -14, 18, 48):
        a = math.radians(ang)
        ex = x + math.sin(a) * 34 * s
        ey = y - 28 * s - math.cos(a) * 34 * s
        d.line([(x, y - 28 * s), (ex, ey)], fill=(64, 148, 74), width=int(4 * s))
        d.ellipse([ex - 13 * s, ey - 10 * s, ex + 13 * s, ey + 10 * s], fill=(104, 190, 92),
                  outline=(56, 132, 68), width=2)


def _p_book(d, x, y, s, pal):
    d.polygon([(x - 32 * s, y - 34 * s), (x, y - 40 * s), (x + 32 * s, y - 34 * s),
               (x + 32 * s, y), (x, y - 6 * s), (x - 32 * s, y)],
              fill=(255, 252, 242), outline=INK, width=max(2, int(2.4 * s)))
    d.line([(x, y - 40 * s), (x, y - 6 * s)], fill=INK, width=2)


def _p_phone(d, x, y, s, pal):
    d.rounded_rectangle([x - 15 * s, y - 42 * s, x + 15 * s, y], radius=6 * s,
                        fill=(58, 60, 68), outline=INK, width=max(2, int(2.4 * s)))
    d.rounded_rectangle([x - 10 * s, y - 35 * s, x + 10 * s, y - 5 * s], radius=3 * s,
                        fill=(150, 198, 238))


def _p_laptop(d, x, y, s, pal):
    d.polygon([(x - 6 * s, y - 44 * s), (x + 32 * s, y - 44 * s),
               (x + 24 * s, y - 6 * s), (x, y - 6 * s)], fill=(206, 210, 218), outline=INK, width=max(2, int(2.4 * s)))
    d.polygon([(x - 36 * s, y - 6 * s), (x + 40 * s, y - 6 * s),
               (x + 36 * s, y), (x - 32 * s, y)], fill=(180, 186, 196), outline=INK, width=2)


def _p_glasses(d, x, y, s, pal):
    d.ellipse([x - 38 * s, y - 24 * s, x - 4 * s, y - 4 * s], outline=INK, width=max(2, int(3 * s)))
    d.ellipse([x + 4 * s, y - 24 * s, x + 38 * s, y - 4 * s], outline=INK, width=max(2, int(3 * s)))
    d.line([(x - 4 * s, y - 14 * s), (x + 4 * s, y - 14 * s)], fill=INK, width=3)


def _p_cat(d, x, y, s, pal):
    d.ellipse([x - 26 * s, y - 34 * s, x + 26 * s, y], fill=(238, 214, 186), outline=INK, width=max(2, int(2.6 * s)))
    d.ellipse([x - 30 * s, y - 62 * s, x - 2 * s, y - 34 * s], fill=(238, 214, 186), outline=INK, width=max(2, int(2.4 * s)))
    d.polygon([(x - 30 * s, y - 56 * s), (x - 22 * s, y - 74 * s), (x - 12 * s, y - 56 * s)], fill=(238, 214, 186), outline=INK, width=2)
    d.ellipse([x - 25 * s, y - 52 * s, x - 19 * s, y - 44 * s], fill=INK)
    d.ellipse([x - 15 * s, y - 52 * s, x - 9 * s, y - 44 * s], fill=INK)


def _p_dog(d, x, y, s, pal):
    d.ellipse([x - 30 * s, y - 40 * s, x + 30 * s, y], fill=(206, 166, 118), outline=INK, width=max(2, int(2.6 * s)))
    d.ellipse([x - 22 * s, y - 66 * s, x + 22 * s, y - 34 * s], fill=(206, 166, 118), outline=INK, width=max(2, int(2.4 * s)))
    d.ellipse([x - 36 * s, y - 62 * s, x - 18 * s, y - 42 * s], fill=(150, 112, 76), outline=INK, width=2)
    d.ellipse([x - 12 * s, y - 54 * s, x - 6 * s, y - 46 * s], fill=INK)
    d.ellipse([x + 6 * s, y - 54 * s, x + 12 * s, y - 46 * s], fill=INK)
    d.ellipse([x - 7 * s, y - 46 * s, x + 7 * s, y - 40 * s], fill=INK)


def _p_bird(d, x, y, s, pal):
    d.ellipse([x - 16 * s, y - 20 * s, x + 16 * s, y], fill=(110, 160, 210), outline=INK, width=2)
    d.ellipse([x + 8 * s, y - 32 * s, x + 26 * s, y - 14 * s], fill=(140, 186, 226), outline=INK, width=2)
    d.polygon([(x + 26 * s, y - 24 * s), (x + 40 * s, y - 20 * s), (x + 26 * s, y - 17 * s)], fill=(240, 190, 70))
    d.ellipse([x + 18 * s, y - 27 * s, x + 22 * s, y - 23 * s], fill=INK)


def _p_butterfly(d, x, y, s, pal):
    for sgn in (-1, 1):
        d.ellipse([x + sgn * 6 * s, y - 30 * s, x + sgn * 30 * s, y - 10 * s],
                  fill=(240, 160, 200), outline=INK, width=2)
        d.ellipse([x + sgn * 5 * s, y - 12 * s, x + sgn * 24 * s, y + 2 * s],
                  fill=(250, 210, 130), outline=INK, width=2)
    d.line([(x, y - 12 * s), (x, y + 2 * s)], fill=INK, width=3)


def _p_ball(d, x, y, s, pal):
    d.ellipse([x - 26 * s, y - 52 * s, x + 26 * s, y], fill=(255, 255, 255), outline=INK, width=max(2, int(3 * s)))
    d.polygon([(x, y - 44 * s), (x + 12 * s, y - 30 * s), (x, y - 16 * s), (x - 12 * s, y - 30 * s)], fill=INK)


def _p_umbrella(d, x, y, s, pal):
    d.pieslice([x - 36 * s, y - 56 * s, x + 36 * s, y - 8 * s], 180, 360,
               fill=(226, 96, 84), outline=INK, width=max(2, int(3 * s)))
    d.line([(x, y - 32 * s), (x, y)], fill=INK, width=max(2, int(3 * s)))
    d.arc([x - 9 * s, y - 8 * s, x + 9 * s, y + 8 * s], 0, 180, fill=INK, width=3)


def _p_bag(d, x, y, s, pal):
    d.polygon([(x - 28 * s, y - 44 * s), (x + 28 * s, y - 44 * s),
               (x + 32 * s, y), (x - 32 * s, y)], fill=(216, 150, 96), outline=INK, width=max(2, int(3 * s)))
    d.arc([x - 16 * s, y - 62 * s, x + 16 * s, y - 30 * s], 180, 360, fill=INK, width=3)


def _p_shoe(d, x, y, s, pal):
    d.polygon([(x - 34 * s, y - 18 * s), (x + 6 * s, y - 18 * s),
               (x + 20 * s, y - 30 * s), (x + 36 * s, y - 12 * s), (x + 36 * s, y),
               (x - 34 * s, y)], fill=(238, 240, 244), outline=INK, width=max(2, int(2.8 * s)))
    d.line([(x - 34 * s, y - 4 * s), (x + 36 * s, y - 4 * s)], fill=(226, 78, 58), width=int(4 * s))


def _p_key(d, x, y, s, pal):
    d.ellipse([x - 34 * s, y - 30 * s, x - 10 * s, y - 6 * s], outline=(226, 190, 60), width=int(6 * s))
    d.line([(x - 10 * s, y - 18 * s), (x + 36 * s, y - 18 * s)], fill=(226, 190, 60), width=int(6 * s))
    d.line([(x + 22 * s, y - 18 * s), (x + 22 * s, y - 6 * s)], fill=(226, 190, 60), width=int(6 * s))
    d.line([(x + 34 * s, y - 18 * s), (x + 34 * s, y - 4 * s)], fill=(226, 190, 60), width=int(6 * s))


def _p_coin(d, x, y, s, pal):
    d.ellipse([x - 20 * s, y - 40 * s, x + 20 * s, y], fill=(246, 196, 62), outline=INK, width=max(2, int(2.6 * s)))
    d.ellipse([x - 12 * s, y - 32 * s, x + 12 * s, y - 8 * s], outline=(190, 140, 40), width=2)


def _p_apple(d, x, y, s, pal):
    d.ellipse([x - 24 * s, y - 40 * s, x + 24 * s, y], fill=(222, 78, 66), outline=INK, width=max(2, int(2.8 * s)))
    d.line([(x, y - 38 * s), (x + 6 * s, y - 52 * s)], fill=(96, 140, 70), width=int(4 * s))
    d.ellipse([x - 16 * s, y - 34 * s, x - 4 * s, y - 24 * s], fill=(248, 160, 150))


def _p_bread(d, x, y, s, pal):
    d.ellipse([x - 34 * s, y - 34 * s, x + 34 * s, y], fill=(228, 188, 122), outline=INK, width=max(2, int(2.8 * s)))
    for i in range(3):
        d.line([(x - 16 * s + i * 16 * s, y - 24 * s), (x - 8 * s + i * 16 * s, y - 14 * s)],
               fill=(170, 130, 76), width=3)


def _p_egg(d, x, y, s, pal):
    d.ellipse([x - 20 * s, y - 40 * s, x + 20 * s, y], fill=(255, 252, 240), outline=INK, width=max(2, int(2.6 * s)))
    d.ellipse([x - 8 * s, y - 22 * s, x + 8 * s, y - 8 * s], fill=(246, 196, 62))


def _p_lamp(d, x, y, s, pal):
    d.line([(x, y), (x, y - 52 * s)], fill=INK, width=int(4 * s))
    d.polygon([(x - 26 * s, y - 52 * s), (x + 26 * s, y - 52 * s),
               (x + 16 * s, y - 78 * s), (x - 16 * s, y - 78 * s)],
              fill=(255, 232, 150), outline=INK, width=max(2, int(2.8 * s)))


def _p_tv(d, x, y, s, pal):
    d.rounded_rectangle([x - 40 * s, y - 62 * s, x + 40 * s, y - 8 * s], radius=6 * s,
                        fill=(70, 74, 84), outline=INK, width=max(2, int(2.8 * s)))
    d.rectangle([x - 33 * s, y - 55 * s, x + 33 * s, y - 15 * s], fill=(150, 198, 238))
    d.line([(x, y - 8 * s), (x, y)], fill=INK, width=int(4 * s))


def _p_remote(d, x, y, s, pal):
    d.rounded_rectangle([x - 13 * s, y - 56 * s, x + 13 * s, y], radius=8 * s,
                        fill=(60, 62, 70), outline=INK, width=max(2, int(2.4 * s)))
    for r in range(3):
        for c in range(2):
            d.ellipse([x - 8 * s + c * 12 * s, y - 46 * s + r * 14 * s,
                       x - 3 * s + c * 12 * s, y - 41 * s + r * 14 * s],
                      fill=(200, 200, 210))


def _p_sticky(d, x, y, s, pal):
    d.polygon([(x - 24 * s, y - 24 * s), (x + 24 * s, y - 26 * s),
               (x + 22 * s, y), (x - 26 * s, y - 2 * s)], fill=(255, 214, 66), outline=INK, width=2)
    for i in range(2):
        _hline(d, x - 16 * s, x + 16 * s, y - 16 * s + i * 8 * s, (140, 110, 40), 2)


def _p_paper(d, x, y, s, pal):
    d.polygon([(x - 24 * s, y - 40 * s), (x + 24 * s, y - 36 * s),
               (x + 22 * s, y), (x - 26 * s, y - 4 * s)], fill=(255, 253, 246), outline=INK, width=2)
    for i in range(3):
        _hline(d, x - 16 * s, x + 16 * s, y - 28 * s + i * 9 * s, (170, 162, 150), 2)


def _p_folder(d, x, y, s, pal):
    d.polygon([(x - 34 * s, y - 34 * s), (x - 6 * s, y - 34 * s), (x + 2 * s, y - 26 * s),
               (x + 34 * s, y - 26 * s), (x + 34 * s, y), (x - 34 * s, y)],
              fill=(244, 198, 96), outline=INK, width=max(2, int(2.6 * s)))


def _p_battery(d, x, y, s, pal):
    d.rounded_rectangle([x - 16 * s, y - 40 * s, x + 16 * s, y], radius=5 * s,
                        fill=(70, 74, 84), outline=INK, width=2)
    d.rectangle([x - 5 * s, y - 45 * s, x + 5 * s, y - 40 * s], fill=INK)
    d.rectangle([x - 12 * s, y - 34 * s, x - 2 * s, y - 6 * s], fill=(110, 200, 120))


def _p_plug(d, x, y, s, pal):
    d.rounded_rectangle([x - 20 * s, y - 32 * s, x + 20 * s, y], radius=6 * s,
                        fill=(236, 236, 240), outline=INK, width=max(2, int(2.6 * s)))
    d.line([(x - 8 * s, y - 32 * s), (x - 8 * s, y - 48 * s)], fill=INK, width=int(4 * s))
    d.line([(x + 8 * s, y - 32 * s), (x + 8 * s, y - 48 * s)], fill=INK, width=int(4 * s))


def _p_headphones(d, x, y, s, pal):
    d.arc([x - 34 * s, y - 62 * s, x + 34 * s, y - 6 * s], 180, 360, fill=INK, width=int(6 * s))
    d.rounded_rectangle([x - 44 * s, y - 32 * s, x - 22 * s, y], radius=8 * s,
                        fill=(226, 78, 58), outline=INK, width=2)
    d.rounded_rectangle([x + 22 * s, y - 32 * s, x + 44 * s, y], radius=8 * s,
                        fill=(226, 78, 58), outline=INK, width=2)


def _p_soap(d, x, y, s, pal):
    d.rounded_rectangle([x - 26 * s, y - 26 * s, x + 26 * s, y], radius=10 * s,
                        fill=(190, 226, 240), outline=INK, width=2)
    d.ellipse([x - 8 * s, y - 18 * s, x + 8 * s, y - 4 * s], fill=(240, 250, 255))


def _p_toothbrush(d, x, y, s, pal):
    d.rounded_rectangle([x - 6 * s, y - 46 * s, x + 6 * s, y], radius=3 * s,
                        fill=(120, 190, 220), outline=INK, width=2)
    d.rounded_rectangle([x - 11 * s, y - 62 * s, x + 11 * s, y - 44 * s], radius=4 * s,
                        fill=(250, 250, 252), outline=INK, width=2)


def _p_towel(d, x, y, s, pal):
    d.polygon([(x - 28 * s, y - 48 * s), (x + 28 * s, y - 48 * s),
               (x + 26 * s, y), (x - 26 * s, y)], fill=(140, 200, 220), outline=INK, width=max(2, int(2.8 * s)))
    for i in range(3):
        _hline(d, x - 22 * s, x + 22 * s, y - 38 * s + i * 8 * s, (100, 170, 196), 2)


def _p_pillow(d, x, y, s, pal):
    d.rounded_rectangle([x - 36 * s, y - 26 * s, x + 36 * s, y], radius=12 * s,
                        fill=(255, 252, 242), outline=INK, width=max(2, int(2.8 * s)))
    d.arc([x - 26 * s, y - 20 * s, x + 26 * s, y - 2 * s], 200, 340, fill=(228, 222, 210), width=2)


def _p_blanket(d, x, y, s, pal):
    d.polygon([(x - 40 * s, y - 30 * s), (x + 40 * s, y - 34 * s),
               (x + 38 * s, y), (x - 38 * s, y - 4 * s)], fill=(160, 150, 210), outline=INK, width=max(2, int(2.8 * s)))
    for i in range(3):
        _hline(d, x - 30 * s, x + 30 * s, y - 24 * s + i * 8 * s, (128, 118, 180), 2)


def _p_mic(d, x, y, s, pal):
    d.rounded_rectangle([x - 15 * s, y - 56 * s, x + 15 * s, y - 20 * s], radius=13 * s,
                        fill=(150, 152, 162), outline=INK, width=max(2, int(2.6 * s)))
    for i in range(4):
        _hline(d, x - 11 * s, x + 11 * s, y - 48 * s + i * 7 * s, INK, 2)
    d.line([(x, y - 20 * s), (x, y - 4 * s)], fill=INK, width=int(4 * s))
    d.ellipse([x - 16 * s, y - 10 * s, x + 16 * s, y], fill=(90, 92, 100), outline=INK, width=2)


def _p_guitar(d, x, y, s, pal):
    d.ellipse([x - 30 * s, y - 62 * s, x + 30 * s, y - 22 * s], fill=(226, 160, 90), outline=INK, width=max(2, int(2.6 * s)))
    d.ellipse([x - 24 * s, y - 38 * s, x + 24 * s, y - 8 * s], fill=(238, 186, 120), outline=INK, width=2)
    d.rectangle([x - 8 * s, y - 96 * s, x + 8 * s, y - 56 * s], fill=(120, 88, 62), outline=INK, width=2)
    d.ellipse([x - 10 * s, y - 50 * s, x + 10 * s, y - 38 * s], fill=(70, 58, 48))


def _p_camera(d, x, y, s, pal):
    d.rounded_rectangle([x - 36 * s, y - 46 * s, x + 36 * s, y], radius=8 * s,
                        fill=(84, 86, 96), outline=INK, width=max(2, int(2.8 * s)))
    d.ellipse([x - 18 * s, y - 38 * s, x + 18 * s, y - 2 * s], fill=(160, 200, 232), outline=INK, width=3)
    d.rectangle([x - 12 * s, y - 52 * s, x + 6 * s, y - 44 * s], fill=(84, 86, 96), outline=INK, width=2)


def _p_mouse(d, x, y, s, pal):
    d.rounded_rectangle([x - 18 * s, y - 42 * s, x + 18 * s, y], radius=16 * s,
                        fill=(232, 234, 238), outline=INK, width=max(2, int(2.6 * s)))
    d.line([(x, y - 40 * s), (x, y - 20 * s)], fill=INK, width=2)


def _p_calendar(d, x, y, s, pal):
    d.rectangle([x - 30 * s, y - 52 * s, x + 30 * s, y], fill=(255, 253, 246), outline=INK, width=max(2, int(2.6 * s)))
    d.rectangle([x - 30 * s, y - 52 * s, x + 30 * s, y - 38 * s], fill=(226, 78, 58), outline=INK, width=2)
    for r in range(3):
        for c in range(4):
            d.rectangle([x - 24 * s + c * 13 * s, y - 32 * s + r * 11 * s,
                         x - 18 * s + c * 13 * s, y - 26 * s + r * 11 * s], fill=(190, 182, 170))


def _p_trash(d, x, y, s, pal):
    d.polygon([(x - 26 * s, y - 44 * s), (x + 26 * s, y - 44 * s),
               (x + 20 * s, y), (x - 20 * s, y)], fill=(150, 156, 164), outline=INK, width=max(2, int(2.6 * s)))
    d.rectangle([x - 30 * s, y - 52 * s, x + 30 * s, y - 44 * s], fill=(178, 184, 192), outline=INK, width=2)


def _p_box(d, x, y, s, pal):
    d.polygon([(x - 34 * s, y - 44 * s), (x + 34 * s, y - 44 * s),
               (x + 34 * s, y), (x - 34 * s, y)], fill=(214, 176, 126), outline=INK, width=max(2, int(2.8 * s)))
    d.line([(x - 34 * s, y - 30 * s), (x + 34 * s, y - 30 * s)], fill=INK, width=2)
    d.line([(x, y - 44 * s), (x, y)], fill=INK, width=2)


def _p_calculator(d, x, y, s, pal):
    d.rounded_rectangle([x - 26 * s, y - 52 * s, x + 26 * s, y], radius=6 * s,
                        fill=(96, 100, 110), outline=INK, width=max(2, int(2.6 * s)))
    d.rectangle([x - 20 * s, y - 46 * s, x + 20 * s, y - 32 * s], fill=(190, 220, 190), outline=INK, width=2)
    for r in range(3):
        for c in range(3):
            d.rectangle([x - 19 * s + c * 13 * s, y - 27 * s + r * 9 * s,
                         x - 12 * s + c * 13 * s, y - 21 * s + r * 9 * s], fill=(220, 220, 228))


def _p_banknote(d, x, y, s, pal):
    d.rectangle([x - 42 * s, y - 28 * s, x + 42 * s, y], fill=(170, 210, 160), outline=INK, width=max(2, int(2.6 * s)))
    d.ellipse([x - 12 * s, y - 22 * s, x + 12 * s, y - 6 * s], outline=(90, 140, 90), width=2)
    for i in range(2):
        _hline(d, x + 18 * s, x + 34 * s, y - 20 * s + i * 8 * s, (90, 140, 90), 2)


def _p_piggy(d, x, y, s, pal):
    d.ellipse([x - 34 * s, y - 46 * s, x + 34 * s, y], fill=(240, 152, 150), outline=INK, width=max(2, int(2.8 * s)))
    d.polygon([(x - 12 * s, y - 44 * s), (x + 6 * s, y - 44 * s), (x - 2 * s, y - 58 * s)],
              fill=(240, 152, 150), outline=INK, width=2)
    d.ellipse([x + 20 * s, y - 30 * s, x + 36 * s, y - 18 * s], fill=(228, 130, 128), outline=INK, width=2)
    d.rectangle([x - 16 * s, y - 22 * s, x + 8 * s, y - 18 * s], fill=(200, 120, 118))


def _p_target(d, x, y, s, pal):
    for i, col in enumerate(((226, 78, 58), (255, 255, 255), (226, 78, 58))):
        rr = (30 - i * 10) * s
        d.ellipse([x - rr, y - 60 * s - 30 * s + rr, x + rr, y - 60 * s - 30 * s + 3 * rr],
                  fill=col, outline=INK, width=2)


def _p_arrow(d, x, y, s, pal):
    d.rectangle([x - 44 * s, y - 22 * s, x + 8 * s, y - 4 * s], fill=(255, 255, 255), outline=INK, width=max(2, int(2.6 * s)))
    d.polygon([(x + 4 * s, y - 34 * s), (x + 36 * s, y - 13 * s), (x + 4 * s, y + 8 * s)],
              fill=(90, 170, 110), outline=INK, width=2)


def _p_tree(d, x, y, s, pal):
    d.rectangle([x - 7 * s, y - 30 * s, x + 7 * s, y], fill=(134, 96, 62), outline=INK, width=2)
    d.ellipse([x - 34 * s, y - 74 * s, x + 34 * s, y - 20 * s], fill=(104, 186, 96), outline=INK, width=max(2, int(2.6 * s)))
    d.ellipse([x - 16 * s, y - 60 * s, x + 16 * s, y - 34 * s], fill=(132, 206, 116))


def _p_flower(d, x, y, s, pal):
    d.line([(x, y), (x - 3 * s, y - 34 * s)], fill=(88, 152, 76), width=int(3 * s))
    for i in range(5):
        a = math.tau * i / 5
        d.ellipse([x - 3 * s + math.cos(a) * 12 * s - 9 * s, y - 34 * s + math.sin(a) * 12 * s - 9 * s,
                   x - 3 * s + math.cos(a) * 12 * s + 9 * s, y - 34 * s + math.sin(a) * 12 * s + 9 * s],
                  fill=(244, 130, 140), outline=INK, width=2)
    d.ellipse([x - 8 * s, y - 40 * s, x + 8 * s, y - 28 * s], fill=(250, 214, 80), outline=INK, width=2)


def _p_sun(d, x, y, s, pal):
    d.ellipse([x - 24 * s, y - 48 * s, x + 24 * s, y], fill=(252, 220, 90), outline=INK, width=max(2, int(2.6 * s)))
    for i in range(8):
        a = math.tau * i / 8
        d.line([(x + math.cos(a) * 28 * s, y - 24 * s + math.sin(a) * 28 * s),
                (x + math.cos(a) * 38 * s, y - 24 * s + math.sin(a) * 38 * s)], fill=(252, 220, 90), width=3)


def _p_cloud(d, x, y, s, pal):
    d.ellipse([x - 40 * s, y - 28 * s, x + 40 * s, y], fill=(255, 255, 255), outline=INK, width=max(2, int(2.4 * s)))
    d.ellipse([x - 24 * s, y - 42 * s, x + 12 * s, y - 10 * s], fill=(255, 255, 255), outline=INK, width=2)
    d.ellipse([x - 6 * s, y - 36 * s, x + 28 * s, y - 8 * s], fill=(255, 255, 255), outline=INK, width=2)


def _p_train(d, x, y, s, pal):
    d.rounded_rectangle([x - 46 * s, y - 48 * s, x + 46 * s, y], radius=10 * s,
                        fill=(120, 170, 210), outline=INK, width=max(2, int(2.8 * s)))
    for i in range(3):
        d.rectangle([x - 36 * s + i * 26 * s, y - 40 * s, x - 18 * s + i * 26 * s, y - 22 * s],
                    fill=(214, 236, 246), outline=INK, width=2)
    d.ellipse([x - 26 * s, y - 10 * s, x - 10 * s, y + 6 * s], fill=(70, 70, 78), outline=INK, width=2)
    d.ellipse([x + 10 * s, y - 10 * s, x + 26 * s, y + 6 * s], fill=(70, 70, 78), outline=INK, width=2)


def _p_bus(d, x, y, s, pal):
    d.rounded_rectangle([x - 46 * s, y - 56 * s, x + 46 * s, y - 6 * s], radius=8 * s,
                        fill=(236, 176, 70), outline=INK, width=max(2, int(2.8 * s)))
    for i in range(3):
        d.rectangle([x - 38 * s + i * 26 * s, y - 48 * s, x - 20 * s + i * 26 * s, y - 28 * s],
                    fill=(214, 236, 246), outline=INK, width=2)
    d.ellipse([x - 28 * s, y - 14 * s, x - 12 * s, y + 2 * s], fill=(70, 70, 78), outline=INK, width=2)
    d.ellipse([x + 12 * s, y - 14 * s, x + 28 * s, y + 2 * s], fill=(70, 70, 78), outline=INK, width=2)


def _p_plane(d, x, y, s, pal):
    d.polygon([(x - 44 * s, y - 26 * s), (x + 30 * s, y - 30 * s),
               (x + 44 * s, y - 22 * s), (x + 30 * s, y - 14 * s), (x - 44 * s, y - 14 * s)],
              fill=(255, 255, 255), outline=INK, width=max(2, int(2.6 * s)))
    d.polygon([(x - 8 * s, y - 26 * s), (x + 8 * s, y - 46 * s), (x + 20 * s, y - 44 * s), (x + 12 * s, y - 24 * s)],
              fill=(255, 255, 255), outline=INK, width=2)
    for i in range(4):
        d.ellipse([x - 30 * s + i * 16 * s, y - 22 * s, x - 22 * s + i * 16 * s, y - 16 * s],
                  fill=(150, 198, 238), outline=INK, width=1)


def _p_balloon(d, x, y, s, pal):
    d.ellipse([x - 22 * s, y - 62 * s, x + 22 * s, y - 18 * s], fill=(240, 110, 100), outline=INK, width=max(2, int(2.6 * s)))
    d.polygon([(x - 6 * s, y - 20 * s), (x + 6 * s, y - 20 * s), (x, y - 12 * s)], fill=(226, 92, 84), outline=INK, width=2)
    d.line([(x, y - 12 * s), (x + 5 * s, y)], fill=INK, width=2)


def _p_cake(d, x, y, s, pal):
    d.rectangle([x - 32 * s, y - 30 * s, x + 32 * s, y], fill=(250, 222, 186), outline=INK, width=max(2, int(2.6 * s)))
    d.rectangle([x - 36 * s, y - 42 * s, x + 36 * s, y - 28 * s], fill=(242, 166, 176), outline=INK, width=2)
    d.line([(x, y - 42 * s), (x, y - 56 * s)], fill=INK, width=2)
    d.ellipse([x - 5 * s, y - 60 * s, x + 5 * s, y - 52 * s], fill=(252, 214, 80))


def _p_target_board(d, x, y, s, pal):
    d.rectangle([x - 34 * s, y - 58 * s, x + 34 * s, y], fill=(245, 240, 228), outline=INK, width=max(2, int(2.8 * s)))
    for i, col in enumerate(((226, 78, 58), (255, 255, 255))):
        rr = (22 - i * 10) * s
        d.ellipse([x - rr, y - 44 * s - rr, x + rr, y - 44 * s + rr], fill=col, outline=INK, width=2)


def _p_gear(d, x, y, s, pal):
    import math as _m
    d.ellipse([x - 24 * s, y - 48 * s, x + 24 * s, y], fill=(160, 166, 176), outline=INK, width=max(2, int(2.6 * s)))
    for i in range(8):
        a = _m.tau * i / 8
        d.rectangle([x + _m.cos(a) * 22 * s - 4 * s, y - 24 * s + _m.sin(a) * 22 * s - 4 * s,
                     x + _m.cos(a) * 22 * s + 4 * s, y - 24 * s + _m.sin(a) * 22 * s + 4 * s], fill=INK)
    d.ellipse([x - 9 * s, y - 33 * s, x + 9 * s, y - 15 * s], fill=(120, 126, 136))


def _p_scissors(d, x, y, s, pal):
    d.line([(x - 24 * s, y), (x + 10 * s, y - 34 * s)], fill=INK, width=int(5 * s))
    d.line([(x + 24 * s, y), (x - 10 * s, y - 34 * s)], fill=INK, width=int(5 * s))
    d.ellipse([x - 34 * s, y - 14 * s, x - 16 * s, y + 4 * s], outline=(226, 78, 58), width=int(4 * s))
    d.ellipse([x + 16 * s, y - 14 * s, x + 34 * s, y + 4 * s], outline=(226, 78, 58), width=int(4 * s))


def _p_tape(d, x, y, s, pal):
    d.ellipse([x - 26 * s, y - 50 * s, x + 26 * s, y - 2 * s], fill=(238, 220, 170), outline=INK, width=max(2, int(2.6 * s)))
    d.ellipse([x - 12 * s, y - 38 * s, x + 12 * s, y - 14 * s], fill=(255, 255, 255), outline=INK, width=2)


def _p_elevator(d, x, y, s, pal):
    d.rectangle([x - 28 * s, y - 62 * s, x + 28 * s, y], fill=(190, 196, 206), outline=INK, width=max(2, int(2.8 * s)))
    d.line([(x, y - 62 * s), (x, y)], fill=INK, width=2)
    d.polygon([(x - 12 * s, y - 48 * s), (x + 12 * s, y - 48 * s), (x, y - 38 * s)], fill=(226, 78, 58), outline=INK, width=2)


def _p_sign(d, x, y, s, pal):
    d.rectangle([x - 4 * s, y - 40 * s, x + 4 * s, y], fill=INK)
    d.rectangle([x - 34 * s, y - 66 * s, x + 34 * s, y - 40 * s], fill=(255, 255, 255), outline=INK, width=max(2, int(2.8 * s)))
    for i in range(2):
        _hline(d, x - 24 * s, x + 24 * s, y - 58 * s + i * 10 * s, (150, 142, 132), 3)


def _p_star(d, x, y, s, pal):
    d.polygon([(x, y - 52 * s), (x + 13 * s, y - 22 * s), (x + 44 * s, y - 18 * s),
               (x + 20 * s, y + 4 * s), (x + 28 * s, y + 34 * s), (x, y + 14 * s),
               (x - 28 * s, y + 34 * s), (x - 20 * s, y + 4 * s), (x - 44 * s, y - 18 * s),
               (x - 13 * s, y - 22 * s)], fill=(250, 214, 66), outline=INK, width=max(2, int(2.4 * s)))


def _p_moon(d, x, y, s, pal):
    d.ellipse([x - 26 * s, y - 50 * s, x + 26 * s, y], fill=(252, 244, 200), outline=INK, width=max(2, int(2.6 * s)))
    d.ellipse([x - 34 * s, y - 56 * s, x + 14 * s, y - 6 * s], fill=(226, 226, 236), outline=INK, width=2)


def _p_fish(d, x, y, s, pal):
    d.ellipse([x - 30 * s, y - 34 * s, x + 20 * s, y - 4 * s], fill=(120, 190, 220), outline=INK, width=max(2, int(2.4 * s)))
    d.polygon([(x + 16 * s, y - 19 * s), (x + 38 * s, y - 32 * s), (x + 38 * s, y - 6 * s)],
              fill=(150, 210, 232), outline=INK, width=2)
    d.ellipse([x - 22 * s, y - 24 * s, x - 16 * s, y - 18 * s], fill=INK)


def _p_bread_knife(d, x, y, s, pal):
    d.polygon([(x - 30 * s, y - 16 * s), (x + 26 * s, y - 26 * s), (x + 30 * s, y - 18 * s),
               (x - 26 * s, y - 8 * s)], fill=(210, 214, 220), outline=INK, width=2)
    d.rectangle([x - 40 * s, y - 16 * s, x - 28 * s, y - 6 * s], fill=(140, 96, 62), outline=INK, width=2)


def _p_dumbbell(d, x, y, s, pal):
    d.rectangle([x - 34 * s, y - 10 * s, x + 34 * s, y], fill=(150, 156, 166), outline=INK, width=2)
    d.rectangle([x - 46 * s, y - 24 * s, x - 30 * s, y + 4 * s], fill=(90, 94, 104), outline=INK, width=2)
    d.rectangle([x + 30 * s, y - 24 * s, x + 46 * s, y + 4 * s], fill=(90, 94, 104), outline=INK, width=2)


def _p_shoes(d, x, y, s, pal):
    _p_shoe(d, x - 12 * s, y, s * 0.8, pal)
    _p_shoe(d, x + 22 * s, y, s * 0.8, pal)


PROPS = {
    "cup": _p_cup, "mug": _p_mug, "notebook": _p_notebook, "pen": _p_pen,
    "clock": _p_clock, "plant": _p_plant, "book": _p_book, "phone": _p_phone,
    "laptop": _p_laptop, "glasses": _p_glasses, "cat": _p_cat, "dog": _p_dog,
    "bird": _p_bird, "butterfly": _p_butterfly, "ball": _p_ball, "umbrella": _p_umbrella,
    "bag": _p_bag, "shoe": _p_shoe, "key": _p_key, "coin": _p_coin,
    "apple": _p_apple, "bread": _p_bread, "egg": _p_egg, "lamp": _p_lamp,
    "tv": _p_tv, "remote": _p_remote, "sticky": _p_sticky, "paper": _p_paper,
    "folder": _p_folder, "battery": _p_battery, "plug": _p_plug,
    "headphones": _p_headphones, "soap": _p_soap, "toothbrush": _p_toothbrush,
    "towel": _p_towel, "pillow": _p_pillow, "blanket": _p_blanket, "mic": _p_mic,
    "guitar": _p_guitar, "camera": _p_camera, "mouse": _p_mouse,
    "calendar": _p_calendar, "trash": _p_trash, "box": _p_box,
    "calculator": _p_calculator, "banknote": _p_banknote, "piggy": _p_piggy,
    "target": _p_target, "arrow": _p_arrow, "tree": _p_tree, "flower": _p_flower,
    "sun": _p_sun, "cloud": _p_cloud, "train": _p_train, "bus": _p_bus,
    "plane": _p_plane, "balloon": _p_balloon, "cake": _p_cake,
    "target_board": _p_target_board, "gear": _p_gear, "scissors": _p_scissors,
    "tape": _p_tape, "elevator": _p_elevator, "sign": _p_sign, "star": _p_star,
    "moon": _p_moon, "fish": _p_fish, "knife": _p_bread_knife,
    "dumbbell": _p_dumbbell, "shoes": _p_shoes,
}


def draw_props(d, w, h, props, pal, avoid_x=None):
    """在分镜里散落小元素，避开角色与字幕框。

    props: 元素名列表
    avoid_x: 角色所在的 x（相对分镜宽度的比例），小元素会躲开它

    位置策略：元素底边落在分镜 30%~72% 高度之间（避开底部字幕框覆盖区），
    横向分布在角色两侧，靠近边缘但不贴边。
    """
    if not props:
        return
    names = [p for p in props if p in PROPS]
    if not names:
        return
    rnd = random.Random(sum(ord(c) for c in ",".join(names)) * 7 + 13)

    ax = (avoid_x if avoid_x is not None else 0.5)
    # 候选位：(x 比例, 底边 y 比例)
    # 前 8 个是四角区（0.075 / 0.925 × 上下），保证画面边缘不空
    corner_slots = [
        (0.075, 0.66), (0.075, 0.40), (0.075, 0.30),
        (0.925, 0.64), (0.925, 0.38), (0.925, 0.28),
        (0.175, 0.72), (0.175, 0.26),
        (0.825, 0.70), (0.825, 0.24),
    ]
    inner_slots = [
        (0.285, 0.30), (0.285, 0.68),
        (0.715, 0.28), (0.715, 0.66),
        (0.055, 0.50), (0.945, 0.48),
        (0.375, 0.24), (0.625, 0.22),
        (0.215, 0.52), (0.785, 0.50),
    ]
    # 过滤：离角色太近的位去掉
    corner_slots = [s for s in corner_slots if abs(s[0] - ax) > 0.13] or corner_slots
    inner_slots = [s for s in inner_slots if abs(s[0] - ax) > 0.13] or inner_slots
    rnd.shuffle(corner_slots)
    rnd.shuffle(inner_slots)
    slots = corner_slots + inner_slots
    for i, name in enumerate(names):
        if i >= len(slots):
            break
        fx, fy = slots[i]
        x = w * fx
        y = h * fy
        s = rnd.uniform(0.95, 1.30) * min(w, h) / 560.0
        try:
            PROPS[name](d, x, y, s, pal)
        except Exception:  # noqa: BLE001
            pass


# ── 场景注册表 ─────────────────────────────────────────
SCENES = {
    "office": scene_office,
    "desk": scene_desk,
    "phone": scene_phone,
    "city": scene_city,
    "mountain": scene_mountain,
    "living": scene_living,
    "meeting": scene_meeting,
    "bedroom": scene_bedroom,
    "kitchen": scene_kitchen,
    "commute": scene_commute,
    "nature": scene_nature,
    "money": scene_money,
    "books": scene_books,
    "camera": scene_camera,
    "keyboard": scene_keyboard,
    "chat": scene_chat,
    "checklist": scene_checklist,
    "bulb": scene_bulb,
    "clockwall": scene_clockwall,
    "door": scene_door,
    "rain": scene_rain,
    "road": scene_road,
    "stairs": scene_stairs,
    "cards": scene_cards,
    "map": scene_map,
    "gym": scene_gym,
    "cafe": scene_cafe,
    "night": scene_night,
    "cabinet": scene_cabinet,
    "floor": scene_floor,
    "radio": scene_radio,
    "balcony": scene_balcony,
    "mirror": scene_mirror,
    "running": scene_running,
    "crowd": scene_crowd,
    "drawer": scene_drawer,
    "voice": scene_voice,
    "alarm": scene_alarm,
    "stove": scene_stove,
    "party": scene_party,
    "wallet": scene_wallet,
    "practice": scene_practice,
    "luggage": scene_luggage,
    "field": scene_field,
    "garden": scene_garden,
}


# ── 语义匹配：关键词 → 场景 ────────────────────────────
KEYWORD_SCENES: list[tuple[tuple[str, ...], str]] = [
    # 手机 / 消息
    (("手机", "消息", "微信", "回复", "在吗", "秒回", "短信", "聊天", "发消息"), "chat"),
    (("截图", "长图", "滚动"), "phone"),
    (("键盘", "打字", "字母", "盲打", "手速"), "keyboard"),
    # 工作 / 电脑
    (("电脑", "桌面", "文件夹", "窗口", "软件", "文档", "文件", "桌面"), "cabinet"),
    (("会议", "开会", "录音", "笔记", "重点", "结论"), "meeting"),
    (("公司", "同事", "领导", "任务", "项目", "需求", "汇报"), "office"),
    (("简历", "名片", "求职", "面试", "岗位", "HR"), "cards"),
    (("裁员", "跳槽", "招聘", "入职"), "map"),
    # 学习 / 阅读
    (("书", "读", "划线", "记住", "背", "抄", "外行", "要点", "论文"), "books"),
    (("复习", "回想", "隔一天", "记忆"), "bulb"),
    (("练习", "打字", "每天五分钟", "训练"), "practice"),
    # 拍照
    (("拍照", "照片", "构图", "镜头", "光", "角度", "证件照"), "camera"),
    (("镜子", "自拍", "照镜子"), "mirror"),
    # 家务 / 生活
    (("房间", "桌面", "摆件", "灯", "落地灯", "高级", "整理", "扔"), "living"),
    (("厨房", "做饭", "早餐", "灶", "锅"), "stove"),
    (("餐桌", "吃饭", "碗", "筷子"), "kitchen"),
    (("床", "睡", "闹钟", "醒", "晚上"), "bedroom"),
    (("阳台", "晾", "晒"), "balcony"),
    (("抽屉", "收纳", "归位", "整理"), "drawer"),
    # 钱
    (("钱", "存钱", "工资", "花", "记账", "存", "转走", "余钱"), "money"),
    (("钱包", "卡", "支付", "扫码"), "wallet"),
    # 沟通 / 社交
    (("求人", "帮忙", "拒绝", "说话", "开口", "说清", "选项"), "voice"),
    (("解释", "反驳", "对话", "消息", "说"), "voice"),
    (("圈子", "人脉", "饭局", "认识", "社交", "机会"), "crowd"),
    (("会议", "一起", "同事"), "meeting"),
    # 出行 / 通勤
    (("出门", "迟到", "赶", "冲", "路上", "通勤", "地铁", "公交"), "commute"),
    (("走", "散步", "跑", "运动", "锻炼", "健身", "球"), "field"),
    (("健身", "跑步", "运动"), "running"),
    (("方向", "选择", "路", "目标", "阶段"), "road"),
    (("台阶", "爬", "登", "上升", "进阶"), "stairs"),
    # 拖延 / 行动
    (("拖延", "开始", "动手", "五分钟", "行动"), "road"),
    (("任务", "拆", "第一步", "计划"), "checklist"),
    (("清单", "列", "三件事", "三行", "计划", "要点"), "checklist"),
    # 情绪
    (("生气", "怒", "崩溃", "烦", "骂", "吼", "吵"), "rain"),
    (("难过", "哭", "委屈", "低落", "痛"), "rain"),
    (("累", "疲惫", "困", "熬夜", "两点"), "night"),
    (("孤独", "闷", "一个人", "没人"), "night"),
    # 思维
    (("想清楚", "意义", "改变", "认知", "道理", "本质"), "bulb"),
    (("机会", "选择", "稀缺"), "map"),
    (("时间", "分钟", "小时", "多久", "准时"), "alarm"),
    (("专注", "注意力", "分心"), "radar" if False else "clockwall"),
    # 其他
    (("广播", "播客", "听", "声音", "讲"), "radio"),
    (("地图", "路线", "导航"), "map"),
    (("旅行", "出门带", "行李", "打包"), "luggage"),
    (("party", "庆祝", "生日", "聚会"), "party"),
    (("分享", "演讲", "表达", "发言", "讲给"), "radio"),
    (("空间", "格局", "视野", "世界"), "mountain"),
    (("成长", "积累", "沉淀", "长期"), "mountain"),
]


def pick_scene(text: str, default: str = "office") -> str:
    """按文案语义挑一个背景场景。"""
    t = text.lower()
    best = None
    best_len = 0
    for kws, name in KEYWORD_SCENES:
        if name not in SCENES:
            continue
        for kw in kws:
            if kw in t and len(kw) > best_len:
                best = name
                best_len = len(kw)
    return best or default


# ── 语义匹配：关键词 → 小元素 ────────────────────────────
KEYWORD_PROPS: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    # 桌面 / 办公
    (("咖啡", "喝", "杯"), ("cup", "mug")),
    (("笔记本", "本子", "记", "写"), ("notebook", "pen")),
    (("笔", "划线", "标注"), ("pen", "sticky")),
    (("桌", "工位", "办公"), ("notebook", "pen", "cup")),
    (("文件", "文档", "报告"), ("paper", "folder")),
    (("文件夹", "整理", "归类"), ("folder", "paper")),
    (("电脑", "屏幕", "程序", "软件"), ("laptop", "mouse")),
    (("鼠标", "点击", "光标"), ("mouse",)),
    (("手机", "刷", "看", "玩"), ("phone",)),
    (("耳机", "听", "音乐", "播客"), ("headphones", "mic")),
    (("相机", "拍", "镜头", "摄影"), ("camera",)),
    (("书", "读", "翻页", "抄"), ("book", "glasses")),
    (("眼镜", "看"), ("glasses",)),
    (("钟", "闹钟", "几点", "分钟", "时候", "时间"), ("clock",)),
    (("日历", "日程", "计划", "安排"), ("calendar", "sign")),
    (("钥匙", "锁", "开门"), ("key", "door_sign")),
    # 钱
    (("钱", "工资", "存", "花", "转走"), ("coin", "banknote")),
    (("账", "记账", "算", "数字", "计算"), ("calculator", "banknote")),
    (("余钱", "月底"), ("piggy", "coin")),
    (("卡", "钱包", "支付", "扫码"), ("banknote",)),
    # 家务
    (("房间", "摆件", "沙发", "客厅"), ("plant", "lamp", "towel")),
    (("灯", "光", "暖光"), ("lamp",)),
    (("床", "睡", "被", "枕"), ("pillow", "blanket")),
    (("厨房", "灶", "锅", "做饭"), ("egg", "bread", "knife")),
    (("早餐", "吃", "碗", "筷", "面包"), ("bread", "cup", "egg")),
    (("洗", "澡", "刷", "牙", "毛巾"), ("soap", "toothbrush", "towel")),
    (("桌", "抽屉", "收纳", "杂物"), ("box", "trash", "tape")),
    (("垃圾", "扔", "丢掉"), ("trash", "box")),
    (("箱子", "打包", "行李"), ("box", "bag")),
    (("包", "带", "装"), ("bag",)),
    # 出行
    (("出门", "赶", "迟到", "冲", "路上"), ("umbrella", "bag", "shoe")),
    (("鞋", "跑", "走", "鞋"), ("shoe",)),
    (("地铁", "公交", "通勤", "车"), ("train",)),
    (("飞机", "旅行", "打包"), ("plane", "bag")),
    (("伞", "下雨", "雨"), ("umbrella", "cloud")),
    (("方向", "路口", "箭头", "往哪"), ("arrow", "sign")),
    (("电梯", "楼", "上"), ("elevator", "sign")),
    # 情绪 / 自然
    (("太阳", "晴", "天气"), ("sun", "cloud")),
    (("夜", "晚", "凌晨", "两点", "睡"), ("moon", "clock")),
    (("雨", "崩", "难过", "哭", "低落", "烦"), ("cloud", "umbrella")),
    (("怒", "生气", "吼", "吵", "骂"), ("gear", "star")),
    (("孤", "一个人", "闷", "没人"), ("moon", "cloud")),
    (("成长", "路", "目标", "方向", "阶", "爬"), ("tree", "arrow")),
    (("开始", "动手", "行动", "第一步"), ("star", "arrow")),
    (("坚持", "习惯", "每天", "积累"), ("star", "calendar")),
    # 社交 / 沟通
    (("说", "讲", "开口", "表达", "分享"), ("mic", "cup")),
    (("话", "沟通", "交流", "回", "消息"), ("phone", "notebook")),
    (("饭局", "人脉", "圈子", "认识", "机会", "同事"), ("cup", "cake")),
    (("求人", "帮忙", "拒绝", "答应"), ("sign", "notebook")),
    # 运动 / 健康
    (("跑", "运动", "锻炼", "健身", "球"), ("ball", "dumbbell", "shoes")),
    (("练", "练习", "学", "打字"), ("keyboard_sticky",)),
    # 其他
    (("鱼", "游泳"), ("fish",)),
    (("目标", "靶", "打", "射"), ("target", "target_board")),
    (("奖", "成功", "赢", "第一"), ("star", "cake")),
    (("剪", "裁", "切"), ("scissors", "knife")),
    (("充", "电", "电池", "没电"), ("battery", "plug")),
    (("遥控", "电视", "看"), ("remote", "tv")),
    (("蝴蝶", "花园", "花", "散步", "公园"), ("flower", "butterfly", "tree")),
    (("云", "天气"), ("cloud", "sun")),
    (("鸟", "天空"), ("bird", "cloud")),
    (("猫", "狗", "宠物"), ("cat", "dog")),
    (("鱼",), ("fish", "plant")),
    (("蜡烛", "生日"), ("cake", "balloon")),
    (("气球", "庆祝", "派对"), ("balloon", "cake")),
    (("转盘", "随机", "选择"), ("gear",)),
    (("刀", "切", "剪"), ("knife", "scissors")),
    # ── 补齐：让每页都能配上小元素 ──
    (("球", "比赛", "运动"), ("ball",)),
    (("苹果", "水果", "健康"), ("apple",)),
    (("吉他", "琴", "弹", "唱歌"), ("guitar", "mic")),
    (("地铁", "公交", "坐车", "打车"), ("bus",)),
    (("飞机", "出差", "飞"), ("plane", "bag")),
    (("胶带", "封", "粘"), ("tape",)),
    (("哑铃", "举", "力量"), ("dumbbell",)),
    (("跑鞋", "球鞋"), ("shoes",)),
    (("喝完", "水", "茶", "喝"), ("mug",)),
    (("旋转", "转", "拧"), ("gear",)),
    (("复习", "重读", "第二遍"), ("book", "notebook")),
    (("背", "记住", "记下来"), ("book", "pen")),
    (("讲给", "外行", "解释给"), ("mic", "cup")),
    (("结论", "要做的事", "三行"), ("paper", "pen")),
    (("闹钟", "响", "响铃"), ("clock", "phone")),
    (("关机", "静音", "专注"), ("phone", "headphones")),
    (("排队", "等", "久了"), ("clock", "sign")),
    (("钱袋", "存钱罐"), ("piggy",)),
    (("分期", "花呗", "免息"), ("banknote", "calculator")),
    (("朋友", "家人", "亲人"), ("cup", "cake")),
    (("弟弟", "妹妹", "孩子"), ("ball", "star")),
    (("同事", "领导", "老板", "客户"), ("paper", "cup")),
    (("简历", "面试", "岗位"), ("paper", "pen")),
    (("裁员", "离职", "辞职"), ("box", "trash")),
    (("存", "转", "账户"), ("calculator", "banknote")),
    (("酒店", "民宿", "旅行"), ("plane", "bag")),
    (("雨伞", "淋雨"), ("umbrella", "cloud")),
    (("奖励", "好处", "划算"), ("coin", "star")),
    (("秒", "立刻", "马上"), ("arrow", "star")),
    (("省", "省事"), ("coin", "piggy")),
    (("整理", "收纳", "归"), ("box", "folder", "tape")),
    (("跑", "坚持", "习惯"), ("shoes", "calendar")),
    (("沟通", "表达", "讲清楚"), ("mic", "pen")),
    (("扔掉", "舍弃", "断舍离"), ("trash", "box")),
    (("锻炼", "身体", "健康"), ("dumbbell", "apple")),
    (("拍照", "角度"), ("camera", "star")),
    (("锁屏", "壁纸"), ("phone", "clock")),
    (("充电", "插座"), ("plug", "battery")),
    (("台灯", "照明"), ("lamp", "book")),
    (("日历", "安排", "顺序"), ("calendar", "pen")),
    (("思路", "框架", "结构"), ("paper", "pen")),
    (("互相", "理解", "误会"), ("cup", "mic")),
    (("孤独", "一个人"), ("moon", "cloud")),
    (("新人", "老手", "内行"), ("notebook", "cup")),
    (("转告", "传话"), ("mic", "phone")),
    (("坚持", "不放弃"), ("star", "sun")),
]

# 兜底元素（关键词一个都没命中时用这些，按 hash 轮换，避免每页都一样）
FALLBACK_PROPS = [
    ("plant", "cup"), ("notebook", "pen"), ("clock", "mug"),
    ("book", "glasses"), ("phone", "calendar"), ("flower", "butterfly"),
    ("cloud", "sun"), ("star", "cake"), ("shoes", "bag"),
    ("apple", "bread"), ("fish", "plant"), ("guitar", "mic"),
    ("plane", "bag"), ("bus", "train"), ("ball", "dumbbell"),
]

# 出现在多个关键词里的元素，重复时不再画
_PROP_ALIAS = {
    "door_sign": "sign",
    "keyboard_sticky": "sticky",
}

# ── 场景默认元素：关键词没命中时，用背景场景本身该有的道具 ──
SCENE_PROPS: dict[str, tuple[str, ...]] = {
    "office": ("notebook", "pen", "cup", "paper"),
    "desk": ("notebook", "pen", "cup", "laptop"),
    "phone": ("phone", "notebook", "pen", "paper"),
    "city": ("sign", "arrow", "bus", "clock"),
    "mountain": ("tree", "cloud", "sun", "bird"),
    "living": ("lamp", "plant", "cup", "towel"),
    "meeting": ("paper", "cup", "calendar", "pen"),
    "bedroom": ("pillow", "blanket", "clock", "plant"),
    "kitchen": ("egg", "bread", "cup", "knife"),
    "commute": ("train", "bag", "umbrella", "clock"),
    "nature": ("tree", "flower", "butterfly", "sun"),
    "money": ("coin", "banknote", "calculator", "piggy"),
    "books": ("book", "glasses", "notebook", "pen"),
    "camera": ("camera", "star", "bag", "flower"),
    "keyboard": ("laptop", "cup", "notebook", "pen"),
    "chat": ("phone", "notebook", "cup", "mug"),
    "checklist": ("calendar", "pen", "paper", "sticky"),
    "bulb": ("star", "gear", "pen", "paper"),
    "clockwall": ("clock", "calendar", "star", "lamp"),
    "door": ("key", "sign", "shoe", "bag"),
    "rain": ("umbrella", "cloud", "shoes", "bag"),
    "road": ("arrow", "sign", "shoes", "bag"),
    "stairs": ("star", "lamp", "sign", "plant"),
    "cards": ("paper", "pen", "cup", "mug"),
    "map": ("arrow", "sign", "paper", "clock"),
    "gym": ("dumbbell", "shoes", "ball", "towel"),
    "cafe": ("cup", "mug", "notebook", "laptop"),
    "night": ("moon", "clock", "star", "cloud"),
    "cabinet": ("folder", "paper", "pen", "box"),
    "floor": ("box", "trash", "shoe", "plant"),
    "radio": ("mic", "headphones", "guitar", "cup"),
    "balcony": ("plant", "towel", "umbrella", "flower"),
    "mirror": ("camera", "star", "flower", "glasses"),
    "running": ("shoes", "ball", "dumbbell", "star"),
    "crowd": ("cup", "cake", "balloon", "mug"),
    "drawer": ("sticky", "paper", "pen", "tape"),
    "voice": ("mic", "cup", "paper", "pen"),
    "alarm": ("clock", "calendar", "phone", "star"),
    "stove": ("egg", "bread", "knife", "mug"),
    "party": ("cake", "balloon", "cup", "star"),
    "wallet": ("banknote", "coin", "calculator", "key"),
    "practice": ("guitar", "notebook", "pen", "mic"),
    "luggage": ("box", "bag", "plane", "shoe"),
    "field": ("ball", "shoes", "sign", "towel"),
    "garden": ("flower", "butterfly", "tree", "plant"),
}


def pick_props(text: str, limit: int = 4, scene: str | None = None) -> list[str]:
    """按文案语义挑一组小元素（去重）。

    优先级：文案关键词 > 背景场景默认元素 > 通用兜底。
    """
    t = text.lower()
    found: list[str] = []
    for kws, props in KEYWORD_PROPS:
        if any(kw in t for kw in kws):
            for p in props:
                p = _PROP_ALIAS.get(p, p)
                if p in PROPS and p not in found:
                    found.append(p)
    # 关键词只给了一部分，用场景元素补齐
    if len(found) < limit and scene:
        for p in SCENE_PROPS.get(scene, ()):
            if p in PROPS and p not in found:
                found.append(p)
            if len(found) >= limit:
                break
    if not found:
        idx = sum(ord(c) for c in text) % len(FALLBACK_PROPS)
        found = list(FALLBACK_PROPS[idx])
    return found[:limit]
