# -*- coding: utf-8 -*-
"""动漫风格图文渲染器 —— 《纸上人生》动漫版。

画面语言（自建）：
  · 纯色平涂背景 + 漫画网点（screentone）质感
  · 放射速度线（集中于角色），强化动势
  · 角色：赛璐璐动漫小人（大眼、双高光、块面发型）
  · 字幕：漫画方框 + 白底黑边 + 斜角，关键词用朱红
  · 对白气泡：白底黑边尖尾巴（经典漫画）
  · 品牌：右下角小字

色彩比"纸上人生"版更浓，动漫感更强。
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from actor import draw_actor
from backdrops import SCENES, pick_scene, draw_props, pick_props, PROPS

FONT_DIR = Path("C:/Windows/Fonts")
FONT_BOLD = FONT_DIR / "msyhbd.ttc"
FONT_REG = FONT_DIR / "msyh.ttc"

INK = (34, 30, 28)
VERMILION = (214, 62, 44)
GRAY = (146, 138, 128)

W, H = 1080, 1440

# 场景配色（动漫平涂，饱和度拉高）
SCENE_SKY = {
    "warm_bad": ((255, 172, 108), (244, 118, 104)),
    "warm_good": ((255, 210, 96), (250, 150, 74)),
    "cool_bad": ((132, 176, 246), (96, 130, 234)),
    "cool_good": ((118, 214, 238), (70, 166, 220)),
    "green_bad": ((150, 210, 148), (96, 176, 112)),
    "green_good": ((146, 222, 128), (88, 190, 96)),
    "violet_bad": ((194, 152, 244), (150, 104, 228)),
    "violet_good": ((180, 152, 246), (136, 100, 226)),
    "pink_bad": ((252, 162, 190), (240, 112, 152)),
    "pink_good": ((254, 186, 176), (246, 126, 130)),
}

FLOOR_COLORS = {
    "warm_bad": (196, 92, 72),
    "warm_good": (206, 132, 60),
    "cool_bad": (92, 108, 172),
    "cool_good": (72, 144, 176),
    "green_bad": (110, 154, 88),
    "green_good": (98, 166, 78),
    "violet_bad": (134, 96, 178),
    "violet_good": (122, 92, 186),
    "pink_bad": (184, 92, 122),
    "pink_good": (192, 100, 92),
}

ACCENTS = {
    "warm_bad": (222, 74, 52),
    "warm_good": (206, 132, 32),
    "cool_bad": (66, 96, 168),
    "cool_good": (32, 140, 160),
    "green_bad": (152, 112, 40),
    "green_good": (70, 138, 58),
    "violet_bad": (140, 84, 190),
    "violet_good": (112, 96, 190),
    "pink_bad": (204, 82, 112),
    "pink_good": (192, 116, 78),
}

# 主题（背景基调）
PAPER_TINTS = {
    "cream": (252, 246, 232),
    "ivory": (248, 244, 234),
    "sage": (244, 248, 238),
    "blush": (252, 242, 236),
    "dusk": (242, 244, 250),
}
PAPER_ORDER = list(PAPER_TINTS)


def logo_exists(assets_dir) -> bool:
    return (Path(assets_dir) / "ThinkNote-logo.png").exists()


# ── 背景场景调色板 ──────────────────────────────────────
def _mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def backdrop_palette(sky, good: bool = False) -> dict:
    """按分镜的渐变天空推导出背景场景配色。

    上格（错误做法）偏灰暗，下格（正确做法）偏明亮通透。
    """
    top, bot = sky
    if good:
        far = _mix(top, (255, 255, 255), 0.55)
        mid = _mix(bot, (255, 255, 255), 0.30)
        near = _mix(bot, (60, 50, 44), 0.30)
        glow = (255, 248, 214)
    else:
        far = _mix(top, (120, 112, 106), 0.28)
        mid = _mix(bot, (90, 84, 80), 0.22)
        near = _mix(bot, (48, 42, 38), 0.38)
        glow = (255, 250, 232)
    return {
        "far": far,
        "mid": mid,
        "near": near,
        "ink": (40, 34, 30),
        "glow": glow,
    }


def pick_paper(seed: str) -> str:
    return PAPER_ORDER[sum(ord(c) for c in seed) % len(PAPER_ORDER)]


def fb(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if FONT_BOLD.exists() else FONT_REG), size)


def fr(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_REG), size)


# ── 网点纸 ──────────────────────────────────────────────
def screentone_bg(w: int, h: int, tint=(252, 246, 232), seed=0) -> Image.Image:
    """漫画网点底：底色 + 斜排小网点。"""
    im = Image.new("RGB", (w, h), tint)
    rnd = random.Random(seed)
    d = ImageDraw.Draw(im)
    step = 11
    for yy in range(0, h + step, step):
        for xx in range(0, w + step, step):
            r = 1.1
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(224, 216, 200))
    return im


# ── 富文本（*关键词* 朱红） ────────────────────────────
def wrap_colored(draw, text: str, size: int, max_w: int):
    lines: list[list[tuple[str, bool]]] = []
    cur: list[tuple[str, bool]] = []
    cur_w = 0.0
    hl = False
    f = fb(size)
    for chunk in text.split("*"):
        for ch in chunk:
            if ch == "\n":
                lines.append(cur)
                cur, cur_w = [], 0.0
                continue
            cw = draw.textlength(ch, font=f)
            if cur_w + cw > max_w and cur:
                lines.append(cur)
                cur, cur_w = [], 0.0
            cur.append((ch, hl))
            cur_w += cw
        hl = not hl
    if cur:
        lines.append(cur)
    return lines


def draw_colored_line(draw, x, y, segs, size, ink, accent, stroke=0, stroke_color=(255, 255, 255)):
    f = fb(size)
    for ch, is_hl in segs:
        if stroke:
            draw.text((x, y), ch, fill=stroke_color, font=f, stroke_width=stroke, stroke_fill=stroke_color)
        draw.text((x, y), ch, fill=accent if is_hl else ink, font=f)
        x += draw.textlength(ch, font=f)
    return x


# ── 漫画速度线 ──────────────────────────────────────────
def speed_lines(draw, w, h, cx, cy, color=(255, 255, 255), count=46, alpha=54):
    """放射线（从角色中心向外），画在最底层。"""
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    rnd = random.Random(7)
    maxr = int(math.hypot(w, h) * 0.62)
    for i in range(count):
        a = (i / count) * math.tau + rnd.uniform(-0.03, 0.03)
        r0 = maxr * rnd.uniform(0.30, 0.46)
        r1 = maxr
        wdt = rnd.choice((2, 3, 4, 6))
        ld.line([
            (cx + math.cos(a) * r0, cy + math.sin(a) * r0),
            (cx + math.cos(a) * r1, cy + math.sin(a) * r1),
        ], fill=color + (alpha,), width=wdt)
    return layer


# ── 漫画拟声词（效果字） ────────────────────────────────
def draw_sfx(draw, text, x, y, size=64, color=(214, 62, 44), rot=0):
    """漫画效果字：粗描边 + 斜体感 + 阴影。"""
    if not text:
        return
    f = fb(size)
    # 阴影
    draw.text((x + 4, y + 4), text, fill=(40, 34, 30), font=f, stroke_width=int(size * 0.14), stroke_fill=(40, 34, 30))
    # 主体（白描边 + 彩色填充）
    draw.text((x, y), text, fill=color, font=f, stroke_width=int(size * 0.14), stroke_fill=(255, 255, 255))


def draw_sfx_layer(im, text, x, y, size=64, color=(214, 62, 44)):
    if not text:
        return
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    f = fb(size)
    ld.text((x + 4, y + 4), text, fill=(40, 34, 30, 255), font=f, stroke_width=int(size * 0.14), stroke_fill=(40, 34, 30, 255))
    ld.text((x, y), text, fill=color + (255,), font=f, stroke_width=int(size * 0.14), stroke_fill=(255, 255, 255, 255))
    im.alpha_composite(layer)


# ── 漫画分镜装饰 ────────────────────────────────────────
def draw_panel_deco(draw, w, h, style="corner"):
    """分镜角上的漫画装饰：斜切角 + 网点块。"""
    # 右上角斜切黑块
    draw.polygon([(w - 46, 0), (w, 0), (w, 46)], fill=(34, 30, 28))
    # 左下角网点小块
    for yy in range(h - 52, h - 6, 9):
        for xx in range(12, 58, 9):
            draw.ellipse([xx, yy, xx + 3, yy + 3], fill=(34, 30, 28))


# ── 漫画强化元素 ────────────────────────────────────────
def halftone_gradient(draw, w, h, color=(60, 54, 48), seed=3, top_h=None):
    """漫画网点渐变：越往下网点越密（模拟阴影/夜空过渡）。"""
    top_h = top_h or int(h * 0.42)
    rnd = random.Random(seed)
    step = 13
    for yy in range(0, top_h, step):
        t = yy / max(1, top_h)
        r = 0.6 + t * 2.4
        for xx in range(0, w, step):
            jx = xx + rnd.randint(-2, 2)
            draw.ellipse([jx - r, yy - r, jx + r, yy + r], fill=color)


def impact_burst(draw, cx, cy, r, fill=(255, 255, 255), outline=(34, 30, 28), n=16, seed=1):
    """漫画集中爆炸框：不规则锯齿多边形（背景冲击特效）。"""
    rnd = random.Random(seed)
    pts = []
    for i in range(n * 2):
        a = math.pi * i / n - math.pi / 2
        k = 1.0 if i % 2 == 0 else rnd.uniform(0.72, 0.86)
        px = cx + math.cos(a) * r * k
        py = cy + math.sin(a) * r * k * 0.92
        pts.append((px, py))
    draw.polygon(pts, fill=fill)
    draw.line(pts + [pts[0]], fill=outline, width=5, joint="curve")


def concentrate_lines(draw, cx, cy, r, color=(255, 255, 255), count=38, seed=5):
    """密集集中线（漫画「强调」笔法）：从角色向外发散的粗细不均短线。"""
    rnd = random.Random(seed)
    for i in range(count):
        a = (i / count) * math.tau + rnd.uniform(-0.05, 0.05)
        r0 = r * rnd.uniform(0.86, 1.05)
        r1 = r * rnd.uniform(1.55, 2.1)
        wdt = rnd.choice((3, 4, 5, 7))
        draw.line([
            (cx + math.cos(a) * r0, cy + math.sin(a) * r0),
            (cx + math.cos(a) * r1, cy + math.sin(a) * r1),
        ], fill=color, width=wdt)


def sparkle(draw, cx, cy, r, color=(255, 248, 210), outline=(214, 172, 60)):
    """四芒星闪光（漫画「好」面板）。"""
    draw.polygon([(cx, cy - r), (cx + r * 0.22, cy - r * 0.22), (cx + r, cy),
                  (cx + r * 0.22, cy + r * 0.22), (cx, cy + r),
                  (cx - r * 0.22, cy + r * 0.22), (cx - r, cy),
                  (cx - r * 0.22, cy - r * 0.22)], fill=color, outline=outline, width=3)


def exclaim_tag(draw, x, y, size=54, color=(222, 74, 48)):
    """漫画惊叹号标牌：黄底黑框的「！」，贴在角色头顶。"""
    w = int(size * 0.72)
    h = int(size * 1.5)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=int(size * 0.16),
                           fill=(255, 214, 66), outline=(34, 30, 28), width=5)
    f = fb(int(size * 0.9))
    tw = draw.textlength("!", font=f)
    draw.text((x + (w - tw) / 2, y + h * 0.12), "!", fill=color, font=f,
              stroke_width=max(2, int(size * 0.08)), stroke_fill=(34, 30, 28))


def draw_page_number(draw, x, y, text):
    """页码：黑底白字的小方块（漫画页脚感）。"""
    f = fb(22)
    w = int(draw.textlength(text, font=f)) + 20
    draw.rectangle([x, y, x + w, y + 30], fill=(34, 30, 28))
    draw.text((x + 10, y + 3), text, fill=(255, 255, 255), font=f)


# ── 场景元素 ────────────────────────────────────────────
def draw_floor(draw, w, h, color):
    # 地面线抬到 ph-44 处，与角色脚底对齐
    draw.rectangle([0, h - 44, w, h], fill=color)
    band = tuple(min(255, c + 70) for c in color)
    draw.rectangle([0, h - 44, w, h - 34], fill=band)


def draw_window(draw, box, sky):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rectangle([x0, y0, x1, y1], fill=(255, 252, 244), outline=(70, 62, 58), width=4)
    draw.rectangle([x0 + 9, y0 + 9, x1 - 9, y1 - 9], fill=sky)
    draw.line([(x0 + w // 2, y0), (x0 + w // 2, y1)], fill=(70, 62, 58), width=4)
    draw.line([(x0, y0 + h // 2), (x1, y0 + h // 2)], fill=(70, 62, 58), width=4)


def draw_plant(draw, cx, base_y, scale=1.0):
    s = scale
    draw.rectangle([cx - 20 * s, base_y - 46 * s, cx + 20 * s, base_y], fill=(206, 118, 74), outline=(70, 62, 58), width=3)
    draw.rectangle([cx - 22 * s, base_y - 50 * s, cx + 22 * s, base_y - 40 * s], fill=(228, 142, 92), outline=(70, 62, 58), width=3)
    for ang, ln in ((-42, 60), (-14, 72), (16, 68), (44, 54)):
        a = math.radians(ang)
        ex = cx + math.sin(a) * ln * s
        ey = base_y - 46 * s - math.cos(a) * ln * s
        draw.line([(cx, base_y - 46 * s), (ex, ey)], fill=(64, 148, 74), width=int(4 * s))
        draw.ellipse([ex - 14 * s, ey - 11 * s, ex + 14 * s, ey + 11 * s], fill=(96, 194, 88), outline=(56, 132, 68), width=2)


def draw_clock(draw, cx, cy, r=40):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 250, 238), outline=(70, 62, 58), width=4)
    draw.line([(cx, cy), (cx, cy - r * 0.55)], fill=(50, 44, 40), width=4)
    draw.line([(cx, cy), (cx + r * 0.38, cy + r * 0.22)], fill=(50, 44, 40), width=4)


# ── 分镜序号标签（情况一 / 情况二） ─────────────────────
def draw_panel_tag(im, box, text, accent=VERMILION):
    """贴在分镜左上角的斜切标签（漫画分镜编号感）。

    细节：黑色斜切底 + 主色描边 + 白色粗字 + 右侧小三角折角。
    """
    x0, y0, x1, _ = box
    d = ImageDraw.Draw(im)
    f = fb(31)
    tw = int(d.textlength(text, font=f))
    bw = tw + 52
    bh = 54
    # 硬投影
    d.polygon([(x0 + 5, y0 + 5), (x0 + bw + 5, y0 + 5),
               (x0 + bw - 16 + 5, y0 + bh + 5), (x0 - 16 + 5, y0 + bh + 5)],
              fill=(90, 80, 70))
    # 斜切平行四边形黑底
    d.polygon([(x0, y0), (x0 + bw, y0), (x0 + bw - 16, y0 + bh), (x0 - 16, y0 + bh)],
              fill=(34, 30, 28))
    # 主色描边
    d.line([(x0, y0), (x0 + bw, y0), (x0 + bw - 16, y0 + bh), (x0 - 16, y0 + bh), (x0, y0)],
           fill=accent, width=5)
    # 顶部高光条（印刷细节）
    d.polygon([(x0 + 3, y0 + 3), (x0 + bw - 4, y0 + 3), (x0 + bw - 8, y0 + 9), (x0 + 7, y0 + 9)],
              fill=accent)
    # 白字
    d.text((x0 + 24, y0 + 10), text, fill=(255, 255, 255), font=f)
    # 右侧折角小三角
    d.polygon([(x0 + bw - 16, y0 + bh), (x0 + bw, y0), (x0 + bw, y0 + bh)],
              fill=accent)


# ── 漫画方框字幕 ────────────────────────────────────────
def draw_caption_box(im, box, text, size=42, accent=VERMILION):
    """漫画分镜框：白底 + 粗黑边 + 底部硬投影 + 关键词朱红。"""
    x0, y0, x1, _ = box
    pad = int(24 * (size / 42))
    d = ImageDraw.Draw(im)
    max_w = x1 - x0 - pad * 2
    lines = wrap_colored(d, text, size, max_w)
    lh = int(size * 1.34)
    h = lh * len(lines) + pad * 2

    # 硬投影（漫画风，偏移而非模糊）
    d.rectangle([x0 + 8, y0 + 8, x1 + 8, y0 + h + 8], fill=(60, 52, 46))
    # 白底黑框
    d.rectangle([x0, y0, x1, y0 + h], fill=(255, 255, 255), outline=(34, 30, 28), width=6)
    # 左侧强调条（斜切）
    d.polygon([(x0, y0), (x0 + 14, y0), (x0 + 14, y0 + h), (x0, y0 + h)], fill=accent)
    # 顶部细色带（细节：分镜框的印刷色条）
    d.rectangle([x0 + 14, y0, x1, y0 + 7], fill=accent)

    y = y0 + pad
    for ln in lines:
        draw_colored_line(d, x0 + pad + 14, y, ln, size, INK, accent)
        y += lh
    return h


# ── 主渲染 ──────────────────────────────────────────────
class AnimeRenderer:
    def __init__(self, out_dir: Path, assets_dir: Path, site: str = "thinknote.pro", theme: str = "cream"):
        self.out_dir = Path(out_dir)
        self.assets_dir = Path(assets_dir)
        self.site = site
        self.theme = theme if theme in PAPER_TINTS else "cream"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def _paper(self, seed: int) -> Image.Image:
        return screentone_bg(W, H, tint=PAPER_TINTS[self.theme], seed=seed)

    def _scene(self, panel_box, sky, actor_cfg, decor=(), accent=VERMILION, scene="warm_bad",
               backdrop=None, caption="", good=False, props=None):
        x0, y0, x1, y1 = panel_box
        pw, ph = x1 - x0, y1 - y0
        im = Image.new("RGB", (pw, ph))
        d = ImageDraw.Draw(im)
        top, bot = sky
        for y in range(ph):
            t = y / max(1, ph - 1)
            d.line([(0, y), (pw, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))

        # ── 细腻度：天空的漫画网点渐变（底部更密，制造纵深） ──
        _tone = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        _td = ImageDraw.Draw(_tone)
        _rnd = random.Random(hash((scene, good)) & 0xFFFF)
        _step = 15
        for _yy in range(int(ph * 0.30), ph, _step):
            _t = (_yy - ph * 0.30) / max(1.0, ph * 0.70)
            _r = 0.5 + _t * 2.6
            for _xx in range(0, pw, _step):
                _jx = _xx + _rnd.randint(-3, 3)
                _td.ellipse([_jx - _r, _yy - _r, _jx + _r, _yy + _r],
                            fill=(60, 52, 46, int(18 + _t * 46)))
        im = Image.alpha_composite(im.convert("RGBA"), _tone).convert("RGB")
        d = ImageDraw.Draw(im)

        # ── 背景场景（填满大片空白，和文案语义对应） ──
        bd_name = backdrop or pick_scene(caption, default="office")
        bd_fn = SCENES.get(bd_name)
        if bd_fn:
            pal = backdrop_palette(sky, good=good)
            # 场景画在半透明层上，压住天空但保留氛围
            layer = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            try:
                bd_fn(ld, pw, ph, pal)
            except Exception:  # noqa: BLE001
                pass
            im = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
            d = ImageDraw.Draw(im)

        # 放射速度线（叠在背景上，漫画动感）
        has_bubble = "bubble" in actor_cfg
        sl = speed_lines(d, pw, ph, pw * 0.44, ph * 0.62, alpha=60, count=54)
        im = Image.alpha_composite(im.convert("RGBA"), sl).convert("RGB")
        d = ImageDraw.Draw(im)

        # ── 小元素：和文案对应的点缀道具 ──
        prop_names = props if props else pick_props(caption, limit=4, scene=bd_name)
        if prop_names:
            _pl = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            _pd = ImageDraw.Draw(_pl)
            draw_props(_pd, pw, ph, prop_names, backdrop_palette(sky, good=good),
                       avoid_x=0.42 if has_bubble else 0.5)
            im = Image.alpha_composite(im.convert("RGBA"), _pl).convert("RGB")
            d = ImageDraw.Draw(im)

        # 地面线：有背景场景时半透明，避免盖掉场景
        floor_col = FLOOR_COLORS.get(scene, (150, 132, 108))
        if bd_fn:
            fl = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            fd = ImageDraw.Draw(fl)
            draw_floor(fd, pw, ph, floor_col)
            fl = fl.filter(ImageFilter.GaussianBlur(0.6))
            im = Image.alpha_composite(im.convert("RGBA"), fl).convert("RGB")
            d = ImageDraw.Draw(im)
        else:
            draw_floor(d, pw, ph, floor_col)
        # 分镜角装饰
        draw_panel_deco(d, pw, ph)

        cfg = dict(actor_cfg)
        cfg.setdefault("scale", 1.5 if has_bubble else 1.75)
        # accent 是旧版参数，动漫版用 shirt 作为主色
        cfg.pop("accent", None)
        v = cfg.get("shirt")
        if isinstance(v, list):
            cfg["shirt"] = tuple(v)
        cfg.pop("rnd", None)
        sfx = cfg.pop("sfx", None)
        mood = cfg.get("mood", "neutral")

        # ── 漫画背景特效（按情绪自动） ──
        if mood in ("rage", "angry"):
            # 怒气：红色锯齿爆炸框 + 密集集中线
            im = im.convert("RGBA")
            bl = Image.new("RGBA", im.size, (0, 0, 0, 0))
            bd = ImageDraw.Draw(bl)
            impact_burst(bd, pw * 0.42, ph * 0.56, pw * 0.40, fill=(255, 236, 226), seed=11)
            concentrate_lines(bd, pw * 0.42, ph * 0.56, pw * 0.40, color=(255, 255, 255), count=44, seed=13)
            im = Image.alpha_composite(im, bl).convert("RGB")
            d = ImageDraw.Draw(im)
        elif mood in ("joy", "happy"):
            # 开心：金色闪光 + 放射光
            for (fx, fy, fr_) in ((0.14, 0.16, 26), (0.86, 0.24, 20), (0.20, 0.72, 18), (0.82, 0.76, 24)):
                sparkle(d, pw * fx, ph * fy, fr_)
        elif mood == "smug":
            # 得意：斜向光条
            for i in range(7):
                x0 = pw * (0.55 + i * 0.07)
                d.polygon([(x0, 0), (x0 + 26, 0), (x0 - 90, ph), (x0 - 116, ph)], fill=(255, 250, 220))
        elif mood in ("sad", "cry"):
            # 悲伤：斜雨线
            for i in range(26):
                x0 = (i * 97) % pw
                y0 = (i * 53) % int(ph * 0.75)
                d.line([(x0, y0), (x0 - 18, y0 + 46)], fill=(255, 255, 255), width=3)
        elif mood in ("tired", "sleep"):
            # 疲惫：灰色网点渐变
            halftone_gradient(d, pw, ph, color=(90, 84, 78), seed=17, top_h=int(ph * 0.5))

        # 只保留地面线和脚下投影 —— 画面干净，不抢角色
        for dec in decor:
            dec(d)
        cx_actor = int(pw * (0.42 if has_bubble else 0.5))
        sh_col = tuple(max(0, c - 52) for c in FLOOR_COLORS.get(scene, (150, 132, 108)))
        d.ellipse([cx_actor - 78, ph - 62, cx_actor + 78, ph - 34], fill=sh_col)
        cfg["bounds"] = (12, 12, pw - 12, ph - 12)
        # 气泡尾巴朝向画面外侧，让两格形成对称呼应
        if has_bubble and "bubble_tail" in cfg:
            if cfg["bubble_tail"] == "left":
                cfg["bubble_tail"] = "right"
            elif cfg["bubble_tail"] == "right":
                cfg["bubble_tail"] = "left"
        draw_actor(d, cx_actor, ph - 44, **cfg)

        # 拟声词（漫画效果字），贴在角色旁边的空白处
        if sfx:
            im = im.convert("RGBA")
            sfx_size = 56 if len(sfx) <= 3 else 42
            if len(sfx) > 5:
                sfx_size = 34
            sx = cx_actor + (110 if cx_actor < pw * 0.5 else -110)
            sx = max(16, min(pw - 200, sx))
            sy = int(ph * 0.18)
            draw_sfx_layer(im, sfx, sx, sy, sfx_size, (222, 70, 48))
            return im.convert("RGB")
        return im

    def _paste_panel(self, im, box, panel):
        d = ImageDraw.Draw(im)
        im.paste(panel, (box[0], box[1]))
        # 外黑框
        d.rectangle([box[0], box[1], box[2] - 1, box[3] - 1], outline=(34, 30, 28), width=6)
        # 内细白线（双线印刷感）
        d.rectangle([box[0] + 10, box[1] + 10, box[2] - 11, box[3] - 11],
                    outline=(255, 255, 255), width=2)
        # 内侧细黑线
        d.rectangle([box[0] + 15, box[1] + 15, box[2] - 16, box[3] - 16],
                    outline=(34, 30, 28), width=1)

    # ── 品牌页脚：定位 + 用途 + 精神内涵 ──
    def _footer(self, im, content_bottom=None):
        d = ImageDraw.Draw(im)
        band_top = int(content_bottom if content_bottom is not None else H - 300) + 18
        band_bottom = H - 34
        if band_bottom - band_top < 130:
            band_top = band_bottom - 130

        # 浅色底 + 上沿分割线
        d.rectangle([40, band_top, W - 40, band_bottom], fill=(250, 247, 240))
        d.line([(40, band_top), (W - 40, band_top)], fill=(204, 194, 180), width=2)

        lx = 64
        if logo_exists(self.assets_dir):
            lg = Image.open(self.assets_dir / "ThinkNote-logo.png").convert("RGBA").resize((52, 52), Image.LANCZOS)
            im.paste(lg, (lx, band_top + 20), lg)
            lx += 66

        # 第一行：品牌名 + 定位/用途
        d.text((lx, band_top + 16), "ThinkNote", fill=(44, 38, 34), font=fb(32))
        d.text((lx + 172, band_top + 24), "深度笔记 · 知识管理 · 效率工具",
               fill=(150, 140, 128), font=fr(22))

        # 第二行：精神内涵（主标语）
        d.text((lx, band_top + 62), "知道你在改变，让我们一同努力",
               fill=(206, 78, 56), font=fb(27))

        # 右侧网址
        site_w = int(d.textlength(self.site, font=fb(24)))
        d.text((W - 64 - site_w, band_top + 62), self.site, fill=(118, 110, 100), font=fb(24))

        # 第三行：细线 + 补充说明
        d.line([(64, band_top + 112), (W - 64, band_top + 112)], fill=(214, 206, 194), width=2)
        d.text((64, band_top + 124), "把想到的记下来，把记住的用起来",
               fill=(162, 152, 140), font=fr(20))
        tip = "随手记 · 随时看 · 越用越懂你"
        tw = int(d.textlength(tip, font=fr(20)))
        d.text((W - 64 - tw, band_top + 124), tip, fill=(162, 152, 140), font=fr(20))

    def render_page(
        self,
        top_caption: str,
        bottom_caption: str,
        top_actor: dict | None = None,
        bottom_actor: dict | None = None,
        top_scene: str = "warm_bad",
        bottom_scene: str = "warm_good",
        top_decor=(),
        bottom_decor=(),
        top_backdrop: str | None = None,
        bottom_backdrop: str | None = None,
        top_props: list[str] | None = None,
        bottom_props: list[str] | None = None,
        page_label: str = "",
        out_name: str = "page.jpg",
    ):
        im = self._paper(abs(hash(out_name)) % 9999)

        M = 52
        gap = 30
        cap_h = 118
        # 底部预留品牌页脚空间
        FOOTER_H = 200
        panel_h = int((H - M * 2 - gap - cap_h * 2 - FOOTER_H) / 2)

        specs = (
            (top_caption, top_actor or {}, top_scene, top_decor, top_backdrop, top_props, M, False),
            (bottom_caption, bottom_actor or {}, bottom_scene, bottom_decor, bottom_backdrop,
             bottom_props, M + panel_h + cap_h + gap, True),
        )
        for cap, actor_cfg, scene, decor, bd, pr, py, good in specs:
            box = (M, py, W - M, py + panel_h)
            sky = SCENE_SKY.get(scene, SCENE_SKY["warm_bad"])
            acc = ACCENTS.get(scene, VERMILION)
            panel = self._scene(box, sky, actor_cfg, decor, acc, scene,
                                backdrop=bd, caption=cap, good=good, props=pr)
            self._paste_panel(im, box, panel)
            # 分镜标签（情况一 / 情况二）
            draw_panel_tag(im, box, "情况二" if good else "情况一", acc)
            # 字幕框压在画面底边，角色脚留出空间
            draw_caption_box(im, (box[0], box[3] - cap_h + 6, box[2], box[3]), cap,
                             size=42, accent=acc)

        if page_label:
            d = ImageDraw.Draw(im)
            draw_page_number(d, W - 52 - 74, M - 4, page_label)

        self._footer(im, content_bottom=M + panel_h * 2 + cap_h * 2 + gap)
        out = self.out_dir / out_name
        im.save(out, "JPEG", quality=93)
        return out

    def render_cover(
        self,
        title: str,
        subtitle: str = "",
        actor_cfg: dict | None = None,
        scene: str = "warm_good",
        decor=(),
        backdrop: str | None = None,
        caption: str = "",
        props: list[str] | None = None,
        out_name: str = "01-cover.jpg",
    ):
        im = self._paper(11)
        d = ImageDraw.Draw(im)
        M = 52

        # ── 漫画标题 banner：黑底 + 黄字 + 斜切边 ──
        lines = wrap_colored(d, title, 84, W - M * 2 - 60)
        title_h = int(84 * 1.24) * len(lines) + 44
        by0 = M + 2
        bx0, bx1 = M, W - M
        # 斜切平行四边形黑底
        d.polygon([(bx0, by0), (bx1, by0), (bx1 - 26, by0 + title_h), (bx0 + 26, by0 + title_h)],
                  fill=(34, 30, 28))
        # 黄色偏移影（错版印刷感）
        d.polygon([(bx0 + 8, by0 + 8), (bx1 + 8, by0 + 8), (bx1 - 18, by0 + title_h + 8),
                   (bx0 + 34, by0 + title_h + 8)], fill=(240, 176, 32))
        d.polygon([(bx0, by0), (bx1, by0), (bx1 - 26, by0 + title_h), (bx0 + 26, by0 + title_h)],
                  fill=(34, 30, 28))
        # 黄字 + 黑底上的白描边
        y = by0 + 22
        for ln in lines[:3]:
            draw_colored_line(d, M + 42, y, ln, 84, (255, 214, 66), (255, 214, 66),
                              stroke=8, stroke_color=(255, 255, 255))
            y += int(84 * 1.24)
        # 副标题：白底黑边小条
        sy = by0 + title_h + 18
        if subtitle:
            for ln in wrap_colored(d, subtitle, 34, W - M * 2 - 40)[:2]:
                tw = d.textlength("".join(c for c, _ in ln), font=fb(34))
                d.rounded_rectangle([M + 6, sy - 6, M + 34 + tw + 18, sy + 40], radius=8,
                                    fill=(255, 255, 255), outline=(34, 30, 28), width=4)
                draw_colored_line(d, M + 22, sy, ln, 34, INK, INK)
                sy += 50

        box = (M, sy + 26 if subtitle else by0 + title_h + 26, W - M, H - M - 240)
        sky = SCENE_SKY.get(scene, SCENE_SKY["warm_good"])
        acc = ACCENTS.get(scene, VERMILION)
        cfg = dict(actor_cfg or {})
        cfg.setdefault("scale", 1.9)
        cfg.pop("accent", None)
        v = cfg.get("shirt")
        if isinstance(v, list):
            cfg["shirt"] = tuple(v)
        cfg.pop("rnd", None)
        panel = self._scene(box, sky, cfg, decor, acc, scene,
                            backdrop=backdrop, caption=caption, good=True, props=props)
        self._paste_panel(im, box, panel)

        self._footer(im, content_bottom=box[3])
        out = self.out_dir / out_name
        im.save(out, "JPEG", quality=93)
        return out
