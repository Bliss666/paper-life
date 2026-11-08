# -*- coding: utf-8 -*-
"""实用性质检：判断技巧是不是「今天就能用的具体动作」。

三条硬标准
----------
1. 下格必须以「你也可以」开头，且给出可执行动作
2. 上下句长度接近，不能上面敷衍、下面注水
3. 同一期里不能出现两条「做法几乎一样」的技巧（凑数）

用法：
    python pipeline/check_practical.py            # 只报告
    python pipeline/check_practical.py --verbose  # 打印每一条的判定
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
YML = ROOT / "content" / "skills.yml"

# 情况二固定开头
BOTTOM_PREFIX = "你也可以"

# 讲道理 / 心态调整 —— 出现就说明这条不实用
EMPTY_PATTERNS = [
    r"不是一回事",
    r"不代表",
    r"别比",
    r"心态",
    r"要相信",
    r"关键在于",
    r"本质是",
    r"你得先接受",
]

STRIP = re.compile(r"[\s，。、！？：；\"'（）()\[\]【】…—\-~·,.!?:;\*]+")


def norm(s: str) -> str:
    return STRIP.sub("", s.replace("*", ""))


def jaccard(a: str, b: str) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    data = yaml.safe_load(YML.read_text(encoding="utf-8"))
    skills = data["skills"]
    topics = data["topics"]
    by_id = {s["id"]: s for s in skills}

    weak: list[tuple[str, str, str]] = []
    for s in skills:
        top = s["top"].replace("*", "")
        bot = s["bottom"].replace("*", "")
        reasons = []

        if not bot.startswith(BOTTOM_PREFIX):
            reasons.append(f"下格不以「{BOTTOM_PREFIX}」开头")
        for pat in EMPTY_PATTERNS:
            if re.search(pat, bot):
                reasons.append(f"下格在讲道理（{pat}）")
                break
        if len(bot) < 16:
            reasons.append(f"下格太短（{len(bot)} 字），动作说得不够具体")
        if len(top) > len(bot) + 8:
            reasons.append(f"上格比下格长太多（{len(top)} vs {len(bot)}）")
        if not s.get("bt") or not s.get("bb"):
            reasons.append("缺气泡")

        if reasons:
            weak.append((s["id"], "；".join(reasons), s["bottom"]))

    # 同一期内的近似重复
    dups: list[tuple[str, str, str, float]] = []
    for t in topics:
        ids = t.get("skills", [])
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = by_id.get(ids[i]), by_id.get(ids[j])
                if not a or not b:
                    continue
                sim = max(jaccard(norm(a["bottom"]), norm(b["bottom"])),
                          jaccard(norm(a["top"]), norm(b["top"])))
                if sim >= 0.62:
                    dups.append((t["id"], a["id"], b["id"], sim))

    scene_cnt: dict[str, int] = defaultdict(int)
    for s in skills:
        scene_cnt[s.get("bd")] += 1
    ranked = sorted(scene_cnt.items(), key=lambda kv: -kv[1])

    print(f"技巧 {len(skills)} 条 / 合集 {len(topics)} 个\n")

    print("── 实用性 ──")
    print(f"  不够实用的技巧：{len(weak)}")
    for sid, why, bot in weak:
        print(f"    {sid}  {why}")
        if args.verbose:
            print(f"       {bot}")

    print("\n── 同期近似重复 ──")
    print(f"  疑似凑数：{len(dups)}")
    for tid, a, b, sim in dups:
        print(f"    {tid}: {a} ≈ {b}  (相似度 {sim:.2f})")

    print("\n── 场景集中度 ──")
    hot = [(k, v) for k, v in ranked[:5] if v >= 15]
    print(f"  过度集中：{hot if hot else '无'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
