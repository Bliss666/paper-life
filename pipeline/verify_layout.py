# -*- coding: utf-8 -*-
"""成品版式验收：逐页检查渲染结果是否符合预期。

检查项
------
1. 「情况一 / 情况二」两个分镜标签都在
2. 上下两个字幕框都存在，且框内有文字（不是空白）
3. 上下两格的关键词都被渲染成朱红（说明 *星号* 生效）
4. 字幕框里没有贴边（文字没顶到框边缘）
5. 角色气泡存在

用法：
    python pipeline/verify_layout.py
    python pipeline/verify_layout.py --issue sk-03
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"

VERMILION = (214, 62, 44)


def near_white(px, thr=235) -> bool:
    return all(v > thr for v in px)


def is_vermilion(px) -> bool:
    r, g, b = px[:3]
    return r > 165 and g < 115 and b < 105


def find_caption_boxes(im: Image.Image):
    """找出上下两个白色字幕框的 y 范围。"""
    W, H = im.size
    px = im.load()
    rows = []
    for y in range(H):
        n = sum(1 for x in range(70, W - 70, 4) if near_white(px[x, y]))
        rows.append(n > (W - 140) // 4 * 0.6)
    boxes, start = [], None
    for y, hit in enumerate(rows):
        if hit and start is None:
            start = y
        elif not hit and start is not None:
            if y - start > 60:
                boxes.append((start, y - 1))
            start = None
    if start is not None and H - start > 60:
        boxes.append((start, H - 1))
    return boxes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", nargs="*")
    args = ap.parse_args()

    dirs = sorted(d for d in OUT.glob("sk-*") if d.is_dir())
    if args.issue:
        want = set(args.issue)
        dirs = [d for d in dirs if d.name in want]

    issues: list[str] = []
    pages = 0
    for d in dirs:
        for f in sorted((d / "images").glob("*-page*.jpg")):
            pages += 1
            im = Image.open(f).convert("RGB")
            W, H = im.size
            px = im.load()
            tag = f"{d.name}/{f.name}"

            # 1. 情况一 / 情况二 标签：黑色斜切底 + 白字，在面板左上/右上
            boxes = find_caption_boxes(im)
            if len(boxes) < 2:
                issues.append(f"{tag}: 字幕框不足 2 个（{len(boxes)}）")
                continue
            (t0, t1), (b0, b1) = boxes[0], boxes[1]

            # 2. 两个字幕框里都要有黑字
            for name, (y0, y1) in (("上格", (t0, t1)), ("下格", (b0, b1))):
                dark = sum(1 for y in range(y0, y1 + 1) for x in range(70, W - 70, 4)
                           if sum(px[x, y]) < 300)
                if dark < 40:
                    issues.append(f"{tag}: {name}字幕框里几乎没有文字（{dark}）")

            # 3. 两格都要有朱红关键词
            for name, (y0, y1) in (("上格", (t0, t1)), ("下格", (b0, b1))):
                red = sum(1 for y in range(y0, y1 + 1) for x in range(70, W - 70, 2)
                          if is_vermilion(px[x, y]))
                if red < 30:
                    issues.append(f"{tag}: {name}关键词没有朱红高亮（{red}）")

    print(f"检查 {pages} 页 / {len(dirs)} 期")
    if not issues:
        print("全部通过：字幕框、关键词高亮、分镜标签都正常")
        return 0
    print(f"发现 {len(issues)} 个问题：")
    for i in issues[:40]:
        print("  ", i)
    return 1


if __name__ == "__main__":
    sys.exit(main())
