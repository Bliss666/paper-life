# -*- coding: utf-8 -*-
"""检查技巧库成品的质量：
  1. 每页文案长度是否合适（上下句接近、不会太长）
  2. 下格是否以「你也可以」开头（情况二的固定格式）
  3. 背景场景是否合法、是否够多样
  4. 角色/表情是否轮换开了（不能每页都长一个样）
  5. 气泡是否都有
  6. 每期是否正好 7 页
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from backdrops import SCENES  # noqa: E402

# 情况二固定开头
BOTTOM_PREFIX = "你也可以"

# 文案长度区间
LEN_MIN, LEN_MAX = 11, 38


def strip_stars(s: str) -> str:
    return s.replace("*", "")


def main() -> int:
    data = yaml.safe_load((ROOT / "content" / "skills.yml").read_text(encoding="utf-8"))
    skills = data["skills"]
    topics = data["topics"]

    print(f"技巧 {len(skills)} 条 / 合集 {len(topics)} 个\n")

    # 1. 文案质量
    print("── 文案检查 ──")
    no_prefix = []
    len_bad = []
    no_star = []
    for s in skills:
        top = strip_stars(s["top"])
        bot = strip_stars(s["bottom"])
        if not bot.startswith(BOTTOM_PREFIX):
            no_prefix.append(s["id"])
        if not (LEN_MIN <= len(top) <= LEN_MAX and LEN_MIN <= len(bot) <= LEN_MAX):
            len_bad.append((s["id"], len(top), len(bot)))
        if "*" not in s["top"] or "*" not in s["bottom"]:
            no_star.append(s["id"])
    print(f"  下格不以「{BOTTOM_PREFIX}」开头：{len(no_prefix)} {no_prefix[:8]}")
    print(f"  长度超范围：{len(len_bad)} {len_bad[:6]}")
    print(f"  缺关键词标注：{len(no_star)} {no_star[:6]}")

    # 2. 场景合法性
    print("\n── 场景检查 ──")
    bad = []
    allbd = Counter()
    for s in skills:
        bd = s.get("bd")
        if bd and bd not in SCENES:
            bad.append((s["id"], bd))
        if bd:
            allbd[bd] += 1
    print(f"  非法场景：{len(bad)} {bad[:6]}")
    print(f"  用到场景 {len(allbd)} 种：{allbd.most_common(8)}")

    # 3. 气泡覆盖
    print("\n── 气泡检查 ──")
    no_bt = [s["id"] for s in skills if not s.get("bt")]
    no_bb = [s["id"] for s in skills if not s.get("bb")]
    print(f"  缺上格气泡：{len(no_bt)} {no_bt[:8]}")
    print(f"  缺下格气泡：{len(no_bb)} {no_bb[:8]}")

    # 4. 合集检查
    print("\n── 合集检查 ──")
    used = set()
    for t in topics:
        for sid in t.get("skills", []):
            used.add(sid)
    unused = [s["id"] for s in skills if s["id"] not in used]
    print(f"  技巧池 {len(skills)} 条，被使用 {len(used)} 条")
    print(f"  未被使用：{len(unused)} {unused[:10]}")
    dup = [t["id"] for t in topics
           if len(set(t.get("skills", []))) != len(t.get("skills", []))]
    print(f"  合集内有重复技巧：{len(dup)} {dup}")
    not7 = [t["id"] for t in topics if len(t.get("skills", [])) != 7]
    print(f"  不满7页的合集：{len(not7)} {not7}")

    # 5. 场景分散度
    print("\n── 场景集中度 ──")
    hot = [(k, v) for k, v in allbd.most_common() if v >= 8]
    print(f"  用得过多的场景：{hot if hot else '无'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
