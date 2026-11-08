# -*- coding: utf-8 -*-
"""把 content/skills.yml 的合集排成「每期 8 张」= 封面 + 7 个技巧页。

排布规则
--------
1. 前 13 期是手写合集（标题/主题/编排意图不动），不足 7 条的用补位技巧填满
2. 剩下的技巧按领域（cat）归类，切成 7 条一期；各领域的尾巴跨领域拼成「混搭」期
3. 所有技巧都用上、不重复，且每一期都正好 7 页

182 条技巧 ÷ 7 = 26 期，正好排满，不多不少。

用法：
    python pipeline/retune_8pages.py            # 只看分配结果
    python pipeline/retune_8pages.py --write     # 写回 skills.yml
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

PAGES_PER_ISSUE = 7   # 封面 + 7 页 = 8 张

# 手写合集（前 13 期），保留原标题与编排意图
HAND_IDS = [f"sk-{i:02d}" for i in range(1, 14)]

# 手写合集不足 7 页时的补位技巧（按顺序取）
PAD_SKILLS = {
    "sk-11": ["sl-038", "dg-020", "sl-033"],
}

# 剩余技巧按领域切分；{n} 会被替换成实际条数
CAT_TITLES = {
    "生活": ("生活里的{n}个实在技巧", "都是今天就能用上的动作"),
    "学习": ("学习上的{n}个笨办法", "方法比努力重要"),
    "工作": ("工作里的{n}个实在做法", "不用卷，做对就行"),
    "沟通": ("把话说清楚的{n}个技巧", "意思到了，话也就到了"),
    "数码": ("数码里的{n}个省事办法", "会用一个功能，胜过分头学十个"),
    "混搭": ("混搭的{n}个技巧", "不属于哪一类，但都管用"),
}
CAT_ORDER = ["生活", "学习", "工作", "沟通", "数码", "混搭"]

# 合法纸底色（见 pipeline/panels.py 的 PAPER_TINTS）
THEMES = ["sage", "blush", "dusk", "ivory", "cream"]


def renum(title: str, n: int) -> str:
    """把标题里的"十二个/12个"改成实际条数。"""
    return re.sub(r"[一二三四五六七八九十百\d]+个", f"{n}个", title)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    data = yaml.safe_load(YML.read_text(encoding="utf-8"))
    skills = data["skills"]
    topics = data["topics"]
    by_id = {s["id"]: s for s in skills}
    hand = {t["id"]: t for t in topics if t["id"] in HAND_IDS}

    used: set[str] = set()
    new_topics: list[dict] = []

    # ── 1. 手写合集：保留原意，不足 7 条的补位 ──
    for tid in HAND_IDS:
        t = hand.get(tid)
        if not t:
            continue
        chunk = [s for s in t.get("skills", []) if s not in used][:PAGES_PER_ISSUE]
        for sid in PAD_SKILLS.get(tid, []):
            if len(chunk) >= PAGES_PER_ISSUE:
                break
            if sid not in used and sid in by_id:
                chunk.append(sid)
        if not chunk:
            continue
        used.update(chunk)
        new_topics.append({
            "id": tid,
            "title": renum(t["title"], len(chunk)),
            "subtitle": t.get("subtitle", ""),
            "theme": t.get("theme", "sage"),
            "skills": chunk,
        })

    # ── 2. 剩下的技巧按领域切 7 条一期 ──
    leftovers = [s["id"] for s in skills if s["id"] not in used]
    by_cat: dict[str, list[str]] = defaultdict(list)
    for sid in leftovers:
        by_cat[by_id[sid].get("cat", "生活")].append(sid)

    full: dict[str, list[list[str]]] = {}
    tails: list[str] = []
    for cat in CAT_ORDER[:-1]:
        ids = by_cat.get(cat, [])
        if not ids:
            continue
        chunks = [ids[j:j + PAGES_PER_ISSUE] for j in range(0, len(ids), PAGES_PER_ISSUE)]
        if len(chunks[-1]) < PAGES_PER_ISSUE:
            tails.extend(chunks.pop())
        full[cat] = chunks

    # 尾巴跨领域拼成「混搭」期
    if tails:
        for j in range(0, len(tails), PAGES_PER_ISSUE):
            full.setdefault("混搭", []).append(tails[j:j + PAGES_PER_ISSUE])

    seq = len(new_topics)
    for cat in CAT_ORDER:
        chunks = full.get(cat, [])
        if not chunks:
            continue
        tpl, sub = CAT_TITLES[cat]
        for j, chunk in enumerate(chunks):
            seq += 1
            title = tpl.format(n=len(chunk))
            if j > 0:
                title = f"{title}·{j + 1}"
            new_topics.append({
                "id": f"sk-{seq:02d}",
                "title": title,
                "subtitle": sub,
                "theme": THEMES[seq % len(THEMES)],
                "skills": chunk,
            })

    # ── 校验 ──
    all_used = [s for t in new_topics for s in t["skills"]]
    assert len(all_used) == len(set(all_used)), "有技巧被重复使用"
    assert len(all_used) == len(skills), f"技巧没用完：{len(all_used)}/{len(skills)}"
    assert all(len(t["skills"]) == PAGES_PER_ISSUE for t in new_topics), \
        "有合集页数不足：" + str([(t["id"], len(t["skills"])) for t in new_topics
                                  if len(t["skills"]) != PAGES_PER_ISSUE])

    print(f"技巧 {len(skills)} 条 → {len(new_topics)} 期，每期 {PAGES_PER_ISSUE} 页"
          f"（+封面 = {PAGES_PER_ISSUE + 1} 张）\n")
    for t in new_topics:
        cats = sorted({by_id[s].get("cat") for s in t["skills"]})
        print(f"  {t['id']}  {len(t['skills'])} 页  {t['title']:<22} 领域: {cats}")
    print(f"\n校验通过：技巧全部使用且不重复（{len(all_used)}/{len(skills)}），"
          f"每期均 {PAGES_PER_ISSUE} 页")

    if args.write:
        data["topics"] = new_topics
        header = (
            "# 《纸上人生》· 技巧库（Skills Pool）\n"
            "#\n"
            "# skills 技巧池：一页 = 一个独立技巧，上下两格 = 做法一 / 做法二\n"
            "# topics 合集：一份作品 = 一组技巧，每页独立，领域可跨\n"
            "# 每期 = 封面 + 7 个技巧页 = 8 张\n"
            "#\n"
            "# 文案铁律：\n"
            "#   1. top 写\"大家都在做的事\"，bottom 写\"你其实可以怎么做\"，中间有转折连词\n"
            "#   2. 上下句都要有具体动作，不要\"高效\"\"优化\"这种空词\n"
            "#   3. bottom 给的动作要小到今天就能做\n"
            "#   4. *星号* 里只标一个关键词，会被渲染成朱红\n"
        )
        YML.write_text(header + yaml.safe_dump(data, allow_unicode=True, sort_keys=False,
                                                width=100, default_flow_style=False),
                        encoding="utf-8")
        print(f"已写回 {YML}")
    else:
        print("\n（加 --write 才会写回文件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
