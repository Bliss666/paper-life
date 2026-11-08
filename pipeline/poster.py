# -*- coding: utf-8 -*-
"""「图解万物」风格大字观点卡片渲染器。

版式要点（对标图解万物 / 认知类图文号）：
  · 纯色或双色渐变背景，一页一个观点，大字标题居中偏上
  · 关键词用强调色标出（标题里用 *星号* 包裹）
  · 每页左上角分类 chip，右上角页码
  · 底部品牌条：ThinkNote logo + thinknote.pro
  · 可选真实产品截图面板（增强可信度）

输出：
  cover  1080x1440 (3:4，微信视频号图文首图)
  page   1080x1440 (3:4，正文图)
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── 画布 ────────────────────────────────────────────────
COVER_W, COVER_H = 1080, 1440
PAGE_W, PAGE_H = 1080, 1440

MARGIN = 96

# ── 字体 ────────────────────────────────────────────────
FONT_DIR = Path("C:/Windows/Fonts")
FONT_REGULAR = FONT_DIR / "msyh.ttc"
FONT_BOLD = FONT_DIR / "msyhbd.ttc"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    if not path.exists():
        path = FONT_REGULAR
    return ImageFont.truetype(str(path), size)


# ── 配色主题 ────────────────────────────────────────────
# (bg_top, bg_bottom, ink, accent)
THEMES: dict[str, tuple[tuple[int, int, int], ...]] = {
    "warm": ((244, 239, 230), (230, 221, 205), (43, 38, 32), (194, 94, 58)),
    "blue": ((231, 236, 247), (209, 219, 240), (30, 36, 51), (56, 106, 203)),
    "green": ((234, 243, 231), (214, 231, 211), (32, 46, 31), (72, 132, 68)),
    "violet": ((240, 235, 251), (223, 214, 246), (40, 33, 62), (119, 87, 210)),
    "orange": ((253, 238, 227), (249, 217, 194), (50, 35, 25), (220, 108, 45)),
    "gray": ((237, 237, 237), (219, 219, 219), (30, 30, 30), (68, 68, 68)),
    "brand": ((20, 24, 30), (11, 14, 18), (240, 245, 250), (45, 182, 168)),
}

THEME_ORDER = ["warm", "blue", "green", "violet", "orange", "gray"]


def pick_theme(seed: str, allow_brand: bool = True) -> str:
    """按 slug 稳定地分配一个主题，保证同一选题每次渲染颜色一致。"""
    pool = THEME_ORDER + (["brand"] if allow_brand else [])
    idx = sum(ord(c) for c in seed) % len(pool)
    return pool[idx]


# ── 基础绘制工具 ────────────────────────────────────────
def _vgradient(w: int, h: int, top, bottom) -> Image.Image:
    im = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(im)
    span = max(1, h - 1)
    for y in range(h):
        t = y / span
        d.line(
            [(0, y), (w, y)],
            fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
        )
    return im


def _mix(c1, c2, t: float):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _rich_runs(text: str):
    """把 *强调* 切成 (文本, 是否强调) 片段。"""
    runs = []
    for part in re.split(r"(\*[^*\n]+\*)", text):
        if not part:
            continue
        if part.startswith("*") and part.endswith("*") and len(part) > 2:
            runs.append((part[1:-1], True))
        else:
            runs.append((part, False))
    return runs or [("", False)]


def _wrap_rich(draw, text: str, f_regular, f_accent, max_w: int):
    """富文本折行：返回 [[(片段, 是否强调), ...], ...]"""
    lines: list[list[tuple[str, bool]]] = []
    cur: list[tuple[str, bool]] = []
    cur_w = 0.0
    for run_text, is_accent in _rich_runs(text):
        f = f_accent if is_accent else f_regular
        for ch in run_text:
            if ch == "\n":
                lines.append(cur)
                cur, cur_w = [], 0.0
                continue
            w = draw.textlength(ch, font=f)
            if cur_w + w > max_w and cur:
                lines.append(cur)
                cur, cur_w = [], 0.0
            cur.append((ch, is_accent))
            cur_w += w
    if cur:
        lines.append(cur)
    return lines


def _draw_rich_line(draw, x: int, y: int, segments, f_regular, f_accent, ink, accent):
    for ch, is_accent in segments:
        f = f_accent if is_accent else f_regular
        draw.text((x, y), ch, fill=accent if is_accent else ink, font=f)
        x += draw.textlength(ch, font=f)
    return x


def _fit_rich(draw, text, max_w, max_h, sizes, bold=True):
    """在候选字号里挑最大的、能塞进给定盒子的一个。"""
    for size in sizes:
        f_regular = font(size, bold=False)
        f_accent = font(size, bold=True)
        lines = _wrap_rich(draw, text, f_regular, f_accent, max_w)
        line_h = int(size * 1.32)
        if len(lines) * line_h <= max_h:
            return size, lines, line_h
    size = sizes[-1]
    f_regular = font(size, bold=False)
    f_accent = font(size, bold=True)
    lines = _wrap_rich(draw, text, f_regular, f_accent, max_w)
    return size, lines, int(size * 1.32)


def _rounded_panel(im, box, radius, fill=None, outline=None, width=2):
    x, y, w, h = box
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=fill, outline=outline, width=width)
    im.paste(layer, (x, y), layer)


def _fit_contain(img: Image.Image, box_w: int, box_h: int):
    s = min(box_w / img.width, box_h / img.height)
    nw, nh = max(1, int(img.width * s)), max(1, int(img.height * s))
    return img.resize((nw, nh), Image.LANCZOS)


# ── 渲染器 ──────────────────────────────────────────────
class PosterRenderer:
    def __init__(self, out_dir: Path, assets_dir: Path, site: str = "thinknote.pro"):
        self.out_dir = Path(out_dir)
        self.assets_dir = Path(assets_dir)
        self.site = site
        self.out_dir.mkdir(parents=True, exist_ok=True)

    # ── 背景 ───────────────────────────────────────────
    def _background(self, theme: str, w: int, h: int, deco: bool = True):
        top, bottom, ink, accent = THEMES[theme]
        im = _vgradient(w, h, top, bottom)
        if deco:
            layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            r = int(w * 0.62)
            d.ellipse([w - r - 40, h - r - 30, w - 40, h - 30], fill=accent + (26,))
            d.ellipse([-int(w * 0.30), -int(w * 0.30), int(w * 0.42), int(w * 0.42)], fill=ink + (16,))
            im = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
        return im, ink, accent

    # ── 品牌条 ─────────────────────────────────────────
    def _brand_bar(self, im, ink, accent, page_label: str = ""):
        w, h = im.width, im.height
        d = ImageDraw.Draw(im)
        logo = self.assets_dir / "ThinkNote-logo.png"
        if logo.exists():
            lg = Image.open(logo).convert("RGBA").resize((46, 46), Image.LANCZOS)
            im.paste(lg, (MARGIN, h - 92), lg)
        d = ImageDraw.Draw(im)
        d.text((MARGIN + 62, h - 88), "ThinkNote", fill=ink, font=font(30, bold=True))
        sw = d.textlength(self.site, font=font(26))
        d.text((w - MARGIN - sw, h - 86), self.site, fill=accent, font=font(26))
        if page_label:
            pw = d.textlength(page_label, font=font(24))
            d.text((w - MARGIN - pw, MARGIN - 4), page_label, fill=_mix(ink, (255, 255, 255), 0.45), font=font(24))

    # ── chip ───────────────────────────────────────────
    def _chip(self, im, text: str, accent, ink):
        if not text:
            return
        d = ImageDraw.Draw(im)
        f = font(30, bold=True)
        tw = d.textlength(text, font=f)
        bw = int(tw + 52)
        bh = 62
        x, y = MARGIN, MARGIN
        _rounded_panel(im, (x, y, bw, bh), radius=bh // 2, fill=accent)
        d = ImageDraw.Draw(im)
        d.text((x + 26, y + 13), text, fill=(255, 255, 255), font=f)

    # ── 截图面板 ───────────────────────────────────────
    def _shot_panel(self, im, shot_rel: str, box):
        path = (self.assets_dir / shot_rel).resolve()
        if not path.exists():
            return False
        shot = Image.open(path).convert("RGB")
        x, y, w, h = box
        pad = 16
        fitted = _fit_contain(shot, w - pad * 2, h - pad * 2)
        inner = Image.new("RGB", (w, h), (255, 255, 255))
        inner.paste(fitted, ((w - fitted.width) // 2, (h - fitted.height) // 2))
        _rounded_panel(im, (x, y, w, h), radius=22, fill=(255, 255, 255, 235))
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=22, fill=255)
        im.paste(inner, (x, y), mask)
        return True

    # ── 公开 API ───────────────────────────────────────
    def render_page(
        self,
        headline: str,
        note: str = "",
        points: list[str] | None = None,
        kicker: str = "",
        shot: str = "",
        theme: str = "warm",
        page_label: str = "",
        out_name: str = "page.jpg",
        title_max_h: int = 620,
    ):
        w, h = PAGE_W, PAGE_H
        im, ink, accent = self._background(theme, w, h)
        d = ImageDraw.Draw(im)

        self._chip(im, kicker, accent, ink)
        self._brand_bar(im, ink, accent, page_label)

        inner_w = w - MARGIN * 2
        y = MARGIN + 130

        # 大标题
        sizes = [96, 88, 80, 72, 64, 58, 52, 46, 40]
        size, lines, line_h = _fit_rich(d, headline, inner_w, title_max_h, sizes)
        for ln in lines:
            seg_w = sum(d.textlength(c, font=font(size, bold=s)) for c, s in ln)
            x = MARGIN + (inner_w - seg_w) / 2
            _draw_rich_line(d, int(x), y, ln, font(size, bold=False), font(size, bold=True), ink, accent)
            y += line_h
        y += 34

        # 分割线
        d = ImageDraw.Draw(im)
        d.rectangle([w // 2 - 40, y, w // 2 + 40, y + 6], fill=accent)
        y += 46

        # 说明文字
        if note:
            fn = font(36)
            note_lines = _wrap_rich(d, note, fn, fn, inner_w)
            for ln in note_lines[:4]:
                seg_w = sum(d.textlength(c, font=fn) for c, s in ln)
                x = MARGIN + (inner_w - seg_w) / 2
                _draw_rich_line(d, int(x), y, ln, fn, fn, ink, _mix(ink, (255, 255, 255), 0.25))
                y += 54
            y += 24

        # 要点列表
        if points:
            d = ImageDraw.Draw(im)
            for pt in points[:4]:
                d.ellipse([MARGIN, y + 16, MARGIN + 14, y + 30], fill=accent)
                fp = font(32)
                pt_lines = _wrap_rich(d, pt, fp, fp, inner_w - 44)
                for i, ln in enumerate(pt_lines[:2]):
                    seg_w = sum(d.textlength(c, font=fp) for c, s in ln)
                    _draw_rich_line(d, int(MARGIN + 44), y, ln, fp, fp, ink, accent)
                    y += 50
                y += 14

        # 真实截图面板（贴在正文下方）
        if shot:
            panel_h = 420
            panel_y = min(y + 20, PAGE_H - 260 - panel_h)
            if panel_y > MARGIN:
                self._shot_panel(im, shot, (MARGIN, panel_y, w - MARGIN * 2, panel_h))

        out = self.out_dir / out_name
        im.save(out, "JPEG", quality=92)
        return out

    def render_cover(
        self,
        title: str,
        subtitle: str = "",
        kicker: str = "",
        theme: str = "warm",
        out_name: str = "01-cover.jpg",
    ):
        w, h = COVER_W, COVER_H
        im, ink, accent = self._background(theme, w, h)
        d = ImageDraw.Draw(im)

        self._chip(im, kicker, accent, ink)
        self._brand_bar(im, ink, accent)

        inner_w = w - MARGIN * 2
        size, lines, line_h = _fit_rich(d, title, inner_w, 760, [116, 106, 96, 86, 76, 66, 58, 50])
        total_h = len(lines) * line_h
        y = int((h - total_h) / 2) - 90
        for ln in lines:
            seg_w = sum(d.textlength(c, font=font(size, bold=s)) for c, s in ln)
            x = MARGIN + (inner_w - seg_w) / 2
            _draw_rich_line(d, int(x), y, ln, font(size, bold=False), font(size, bold=True), ink, accent)
            y += line_h

        if subtitle:
            d = ImageDraw.Draw(im)
            fs = font(38)
            sub_lines = _wrap_rich(d, subtitle, fs, fs, inner_w)
            sy = y + 52
            for ln in sub_lines[:3]:
                seg_w = sum(d.textlength(c, font=fs) for c, s in ln)
                x = MARGIN + (inner_w - seg_w) / 2
                _draw_rich_line(d, int(x), sy, ln, fs, fs, _mix(ink, (255, 255, 255), 0.3), accent)
                sy += 56

        out = self.out_dir / out_name
        im.save(out, "JPEG", quality=92)
        return out
