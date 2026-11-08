# -*- coding: utf-8 -*-
"""把 content/skills.yml 的技巧池展开成可渲染的选题。

技巧池（skills） → 合集（topics） → 页面（pages）

每个技巧自动补齐：
  · 背景场景（优先用 bd，其次按文案关键词匹配）
  · 上下格配色（上格偏闷 / 下格偏亮，按 cat 换色系）
  · 角色（表情、发型、姿势按技巧序号轮换，避免每页一样）
  · 小元素（按文案关键词）

用法：
    python pipeline/build_skills.py               # 全量
    python pipeline/build_skills.py --topic sk-01 # 单个
    python pipeline/build_skills.py --list
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml

PIPELINE_DIR = Path(__file__).resolve().parent
ROOT = PIPELINE_DIR.parent
CONTENT_DIR = ROOT / "content"
ASSETS_DIR = ROOT / "assets"
OUT_DIR = ROOT / "out"

if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from backdrops import pick_scene, pick_props  # noqa: E402
from panels import AnimeRenderer, pick_paper  # noqa: E402

SKILLS_YML = CONTENT_DIR / "skills.yml"

# 色调 → 配色系（上格 / 下格）
TONE_COLORS = {
    "warm": ("warm_bad", "warm_good"),
    "cool": ("cool_bad", "cool_good"),
    "green": ("green_bad", "green_good"),
    "violet": ("violet_bad", "violet_good"),
    "pink": ("pink_bad", "pink_good"),
}

# 上格角色：走神 / 犯愁 / 疲惫 / 着急 / 茫然
TOP_MOODS = [
    {"mood": "think", "pose": "think", "hair": "short"},
    {"mood": "sad", "pose": "sit", "hair": "bun"},
    {"mood": "tired", "pose": "desk", "hair": "middle"},
    {"mood": "rage", "pose": "headache", "hair": "curly"},
    {"mood": "cold", "pose": "stand", "hair": "pony"},
    {"mood": "cry", "pose": "lie", "hair": "short"},
]

# 下格角色：豁然开朗 / 得意 / 开心 / 稳 / 专注
BOTTOM_MOODS = [
    {"mood": "joy", "pose": "armsup", "hair": "short"},
    {"mood": "smug", "pose": "stand", "hair": "bun"},
    {"mood": "happy", "pose": "stand", "hair": "middle"},
    {"mood": "neutral", "pose": "stand", "hair": "curly"},
    {"mood": "neutral", "pose": "walk", "hair": "pony"},
    {"mood": "happy", "pose": "wave", "hair": "short"},
]

TOP_SHIRT = [198, 88, 68]
BOTTOM_SHIRT = [96, 142, 82]


def load_pool() -> tuple[dict, list[dict]]:
    if not SKILLS_YML.exists():
        raise SystemExit(f"找不到 {SKILLS_YML}")
    data = yaml.safe_load(SKILLS_YML.read_text(encoding="utf-8")) or {}
    skills = {s["id"]: s for s in (data.get("skills") or [])}
    topics = data.get("topics") or []
    return skills, topics


def expand(skill: dict, idx: int, total: int) -> dict:
    """一条技巧 → 一个页面（上下两格）。"""
    tone = skill.get("tone", "warm")
    top_scene, bottom_scene = TONE_COLORS.get(tone, TONE_COLORS["warm"])

    top = skill["top"]
    bottom = skill["bottom"]

    # 背景：优先手写，其次按文案匹配
    bd = skill.get("bd")
    top_bd = bd or pick_scene(top, "office")
    bottom_bd = skill.get("bbd") or pick_scene(bottom, top_bd)

    # 角色：按序号轮换
    tm = TOP_MOODS[idx % len(TOP_MOODS)]
    bm = BOTTOM_MOODS[idx % len(BOTTOM_MOODS)]

    def actor(cfg, shirt, bubble, kind, tail):
        a = {
            "pose": cfg["pose"],
            "mood": cfg["mood"],
            "hair": cfg["hair"],
            "shirt": list(shirt),
        }
        if bubble:
            a["bubble"] = bubble
            a["bubble_kind"] = kind
            a["bubble_tail"] = tail
        return a

    top_actor = actor(tm, TOP_SHIRT, skill.get("bt"), "think", "right")
    bottom_actor = actor(bm, BOTTOM_SHIRT, skill.get("bb"), "speech", "left")

    return {
        "top": top,
        "bottom": bottom,
        "top_backdrop": top_bd,
        "bottom_backdrop": bottom_bd,
        "top_actor": top_actor,
        "bottom_actor": bottom_actor,
        "top_scene": top_scene,
        "bottom_scene": bottom_scene,
        "cat": skill.get("cat", ""),
    }


def build_article(topic: dict, images: list[str]) -> str:
    lines = [f"# {topic.get('title', '')}", ""]
    if topic.get("subtitle"):
        lines += [f"> {topic['subtitle']}", ""]
    lines += [f"![封面](images/{images[0]})", ""]
    for i, page in enumerate(topic.get("pages", [])):
        if i + 1 < len(images):
            lines += [f"![图 {i + 1}](images/{images[i + 1]})", ""]
        lines += [f"❌ {page.get('top', '')}", ""]
        lines += [f"✅ {page.get('bottom', '')}", ""]
    lines += [
        "---",
        "",
        "**ThinkNote** —— 深度笔记 · 知识管理 · 效率工具。",
        "",
        "把想到的记下来，把记住的用起来。随手记 · 随时看 · 越用越懂你。",
        "",
        "> 知道你在改变，让我们一同努力。",
        "",
        "thinknote.pro",
        "",
        f"<!-- id: {topic.get('id')} -->",
    ]
    return "\n".join(lines) + "\n"


def build_topic(topic: dict, skills: dict) -> Path | None:
    tid = topic.get("id")
    if not tid:
        return None
    ids = topic.get("skills") or []
    if not ids:
        print(f"  skip {tid}: 没有技巧")
        return None

    print(f"\n=== {tid} · {topic.get('title', '')}")
    pages = []
    for i, sid in enumerate(ids):
        s = skills.get(sid)
        if not s:
            print(f"  !! 找不到技巧 {sid}")
            continue
        pages.append(expand(s, i, len(ids)))

    out = OUT_DIR / tid
    if out.exists():
        shutil.rmtree(out)
    img_dir = out / "images"
    img_dir.mkdir(parents=True)

    theme = topic.get("theme") or pick_paper(tid)
    r = AnimeRenderer(out, ASSETS_DIR, theme=theme)

    first = pages[0]
    cover = r.render_cover(
        title=topic.get("title", ""),
        subtitle=topic.get("subtitle", ""),
        actor_cfg=first["bottom_actor"],
        scene=first["bottom_scene"],
        backdrop=first["bottom_backdrop"],
        caption=topic.get("title", "") + " " + topic.get("subtitle", ""),
        out_name="01-cover.jpg",
    )
    shutil.copy(cover, img_dir / cover.name)
    images = [cover.name]

    n = len(pages)
    for i, p in enumerate(pages, start=1):
        name = f"{i + 1:02d}-page{i}.jpg"
        img = r.render_page(
            top_caption=p["top"],
            bottom_caption=p["bottom"],
            top_actor=p["top_actor"],
            bottom_actor=p["bottom_actor"],
            top_scene=p["top_scene"],
            bottom_scene=p["bottom_scene"],
            top_backdrop=p["top_backdrop"],
            bottom_backdrop=p["bottom_backdrop"],
            page_label=f"{i}/{n}",
            out_name=name,
        )
        shutil.copy(img, img_dir / img.name)
        images.append(img.name)

    (out / "topic.json").write_text(json.dumps(topic, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
    (out / "article.md").write_text(build_article(topic, images), encoding="utf-8")
    print(f"  -> {out}  ({len(images)} 张图)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="技巧池 → 图文")
    ap.add_argument("--topic", help="只构建指定 id")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    skills, topics = load_pool()
    if args.list:
        print(f"技巧池 {len(skills)} 条，合集 {len(topics)} 个")
        for t in topics:
            print(f"  {t['id']:<8} {len(t.get('skills', [])):>2} 页  {t.get('title', '')}")
        return

    if args.topic:
        topics = [t for t in topics if t.get("id") == args.topic]
        if not topics:
            raise SystemExit(f"找不到：{args.topic}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for t in topics:
        try:
            if build_topic(t, skills):
                ok += 1
        except Exception as exc:  # noqa: BLE001
            import traceback
            print(f"  !! 失败：{exc}")
            traceback.print_exc()
    print(f"\n完成：{ok}/{len(topics)} 篇 → {OUT_DIR}")


if __name__ == "__main__":
    main()
