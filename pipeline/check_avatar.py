# -*- coding: utf-8 -*-
"""校验头像在「微信列表小尺寸」下是否依然可辨认。

检查项：
  1. 脸部区域是否有足够的肤色（角色真的画出来了）
  2. 眼睛区域是否有眼白 + 深色瞳孔（小尺寸下还能看出是"脸"）
  3. 头部占比（脸要够大）
  4. 安全区内关键元素不越界（微信按圆裁切）
  5. 缩到 48px 后的对比度（缩略图不清爽 = 白做）
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageStat

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "_avatar"
SAFE_R = 490


def skin_ratio(im: Image.Image, box) -> float:
    crop = im.crop(box).convert("RGB")
    px = crop.load()
    n = hit = 0
    for y in range(0, crop.height, 2):
        for x in range(0, crop.width, 2):
            r, g, b = px[x, y]
            n += 1
            if r > 225 and g > 185 and 140 < b < 225:
                hit += 1
    return hit / max(1, n)


def eye_check(im: Image.Image, box) -> tuple[float, float]:
    """返回 (眼白占比, 深色瞳孔占比)。"""
    crop = im.crop(box).convert("L")
    px = crop.load()
    n = white = dark = 0
    for y in range(0, crop.height, 1):
        for x in range(0, crop.width, 1):
            v = px[x, y]
            n += 1
            if v > 235:
                white += 1
            elif v < 70:
                dark += 1
    return white / n, dark / n


def in_circle(im: Image.Image, cx: int, cy: int, r: int) -> bool:
    """品牌条是否落在安全圆内。"""
    px = im.load()
    # 取品牌条左右端点
    for x in (cx - 320, cx + 320):
        for y in (790, 880):
            if (x - cx) ** 2 + (y - cy) ** 2 > r * r:
                return False
    return True


def small_contrast(im: Image.Image, size: int = 48) -> float:
    small = im.resize((size, size), Image.LANCZOS).convert("L")
    stat = ImageStat.Stat(small)
    return stat.stddev[0]


def main() -> int:
    files = sorted(OUT.glob("avatar-*.jpg"))
    if not files:
        print("没有找到头像文件")
        return 1
    print(f"{'变体':<6}{'肤色':>8}{'眼白':>8}{'瞳孔':>8}{'小图对比':>10}{'安全圆':>8}")
    for f in files:
        im = Image.open(f).convert("RGB")
        W, H = im.size
        cx = cy = W // 2
        # 脸在 (cx, 0.435H)，头半径 0.245W
        head_cy = int(H * 0.435)
        head_r = int(W * 0.245)
        face_box = (cx - head_r * 0.7, head_cy - head_r * 0.35,
                    cx + head_r * 0.7, head_cy + head_r * 0.6)
        sr = skin_ratio(im, face_box)
        # 眼睛在 head_cy + 0.12r
        eye_y = int(head_cy + head_r * 0.12)
        ew = int(head_r * 0.44)
        eye_box = (cx - ew, eye_y - int(head_r * 0.26), cx + ew, eye_y + int(head_r * 0.26))
        wh, dk = eye_check(im, eye_box)
        sc = small_contrast(im)
        ok = in_circle(im, cx, cy, SAFE_R)
        print(f"{f.stem[-1]:<6}{sr:>8.3f}{wh:>8.3f}{dk:>8.3f}{sc:>10.1f}{'  OK' if ok else '  越界':>8}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
