#!/usr/bin/env python3
"""双格对比图文构建器：人生道理赛道。

产物（out/<id>/）：
  01-cover.jpg      封面（单格大画面 + 大标题）
  02..NN-pageN.jpg  正文（上下双格 + 字幕条）
  article.md        可直接发布的配文
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

from panels import AnimeRenderer, pick_paper  # noqa: E402

LIFE_YML = CONTENT_DIR / "life_topics.yml"


def load_topics() -> list[dict]:
    if not LIFE_YML.exists():
        return []
    return yaml.safe_load(LIFE_YML.read_text(encoding="utf-8")) or []


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


def build_topic(topic: dict) -> Path | None:
    tid = topic.get("id")
    if not tid:
        return None
    print(f"\n=== {tid} · {topic.get('topic', '')}")

    pages = topic.get("pages") or []
    if not pages:
        print("  skip: 无页面")
        return None

    out = OUT_DIR / tid
    if out.exists():
        shutil.rmtree(out)
    img_dir = out / "images"
    img_dir.mkdir(parents=True)

    theme = topic.get("theme") or pick_paper(tid)
    r = AnimeRenderer(out, ASSETS_DIR, theme=theme)

    cover = r.render_cover(
        title=topic.get("title", ""),
        subtitle=topic.get("subtitle", ""),
        actor_cfg=pages[0].get("bottom_actor"),
        scene=pages[0].get("bottom_scene", "warm_good"),
        backdrop=topic.get("backdrop") or pages[0].get("bottom_backdrop"),
        caption=topic.get("title", "") + " " + topic.get("subtitle", ""),
        out_name="01-cover.jpg",
    )
    shutil.copy(cover, img_dir / cover.name)
    images = [cover.name]

    n = len(pages)
    for i, p in enumerate(pages, start=1):
        name = f"{i + 1:02d}-page{i}.jpg"
        img = r.render_page(
            top_caption=p.get("top", ""),
            bottom_caption=p.get("bottom", ""),
            top_actor=p.get("top_actor"),
            bottom_actor=p.get("bottom_actor"),
            top_scene=p.get("top_scene", "warm_bad"),
            bottom_scene=p.get("bottom_scene", "warm_good"),
            top_backdrop=p.get("top_backdrop"),
            bottom_backdrop=p.get("bottom_backdrop"),
            top_props=p.get("top_props"),
            bottom_props=p.get("bottom_props"),
            page_label=f"{i}/{n}",
            out_name=name,
        )
        shutil.copy(img, img_dir / img.name)
        images.append(img.name)

    (out / "topic.json").write_text(json.dumps(topic, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "article.md").write_text(build_article(topic, images), encoding="utf-8")
    print(f"  -> {out}  ({len(images)} 张图)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="构建双格对比图文（人生道理赛道）")
    ap.add_argument("--topic", help="只构建指定 id")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    topics = load_topics()
    if args.list:
        for t in topics:
            print(f"{t['id']:<10} [{t.get('theme','')}] {t.get('topic','')}")
        return

    if args.topic:
        topics = [t for t in topics if t.get("id") == args.topic]
        if not topics:
            raise SystemExit(f"找不到：{args.topic}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for t in topics:
        try:
            if build_topic(t):
                ok += 1
        except Exception as exc:  # noqa: BLE001
            import traceback
            print(f"  !! 失败：{exc}")
            traceback.print_exc()
    print(f"\n完成：{ok}/{len(topics)} 篇 → {OUT_DIR}")


if __name__ == "__main__":
    main()
