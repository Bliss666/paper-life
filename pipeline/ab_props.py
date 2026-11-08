# -*- coding: utf-8 -*-
"""A/B 对比：同一页带 props / 不带 props 的墨线差异，确认小元素真的画上去了。"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from backdrops import SCENES, draw_props, pick_props, pick_scene  # noqa: E402
from panels import (SCENE_SKY, VERMILION, FLOOR_COLORS, backdrop_palette,  # noqa: E402
                    screentone_bg, W, H)

PW, PH = 976, 560


def render(props_on: bool, caption: str, scene: str) -> Image.Image:
    sky = SCENE_SKY.get("warm_good", SCENE_SKY["warm_bad"])
    im = Image.new("RGB", (PW, PH))
    d = ImageDraw.Draw(im)
    top, bot = sky
    for y in range(PH):
        t = y / (PH - 1)
        d.line([(0, y), (PW, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    bd = SCENES.get(scene)
    if bd:
        layer = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
        bd(ImageDraw.Draw(layer), PW, PH, backdrop_palette(sky, good=True))
        im = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
    d = ImageDraw.Draw(im)
    if props_on:
        names = pick_props(caption, limit=4, scene=scene)
        pl = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
        draw_props(ImageDraw.Draw(pl), PW, PH, names, backdrop_palette(sky, good=True))
        im = Image.alpha_composite(im.convert("RGBA"), pl).convert("RGB")
    return im


def ink(im: Image.Image) -> int:
    g = im.convert("L")
    px = g.load()
    return sum(1 for y in range(0, g.height, 2) for x in range(0, g.width, 2)
               if px[x, y] < 120)


CASES = [
    ("别人*一个一个翻菜单*，翻了十分钟", "phone"),
    ("出门前你*翻遍口袋*找钥匙", "door"),
    ("你说：我*还没想清楚*自己要什么", "bulb"),
    ("事情没按你想的来，你*当场崩了*", "rain"),
]


def main() -> int:
    print("文案 / 场景 / 元素 / 墨线增量")
    for cap, sc in CASES:
        names = pick_props(cap, limit=4, scene=sc)
        a = ink(render(False, cap, sc))
        b = ink(render(True, cap, sc))
        print(f"  {sc:<8} {str(names):<48} {a} -> {b}  (+{b - a})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
