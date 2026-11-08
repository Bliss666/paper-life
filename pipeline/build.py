#!/usr/bin/env python3
"""图文构建器：选题 + 草稿 → 渲染图文卡片 → 可直接发布。

草稿优先级（从高到低）
----------------------
1. content/drafts/<id>.json   —— 手写/我写好的成品稿，最高质量
2. .cache/<id>.json            —— 之前 LLM 生成的缓存稿
3. 选题 yml 里的 fallback      —— 保底骨架
4. LLM 实时生成                —— 装了 API key 且以上都没有时

用法：
  python pipeline/build.py                  # 构建全部
  python pipeline/build.py --topic ai-003   # 只构建一篇
  python pipeline/build.py --ai             # 让 LLM 批量补全新稿
  python pipeline/build.py --list
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
DRAFTS_DIR = CONTENT_DIR / "drafts"
ASSETS_DIR = ROOT / "assets"
OUT_DIR = ROOT / "out"
CACHE_DIR = ROOT / ".cache"

if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from llm import LLMClient, write_draft  # noqa: E402
from poster import PosterRenderer, pick_theme  # noqa: E402

CONFIG_PATH = ROOT / "config.yml"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return {}


def load_topics() -> list[dict]:
    topics: list[dict] = []
    for f in sorted(CONTENT_DIR.glob("*.yml")):
        if f.name.startswith("_"):
            continue
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or []
        if isinstance(data, list):
            topics.extend(data)
    return topics


def load_draft(tid: str) -> dict | None:
    """读取成品草稿（content/drafts/<id>.json）。"""
    p = DRAFTS_DIR / f"{tid}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"  [warn] 草稿解析失败 {p.name}: {exc}")
        return None


def save_draft(tid: str, draft: dict) -> None:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    (DRAFTS_DIR / f"{tid}.json").write_text(
        json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def resolve_draft(topic: dict, client: LLMClient, use_ai: bool = False) -> dict:
    """按优先级拿到最终稿。"""
    tid = topic.get("id", "topic")

    if not use_ai:
        d = load_draft(tid)
        if d:
            print(f"  稿源: 成品草稿 content/drafts/{tid}.json")
            return d

    cache = CACHE_DIR / f"{tid}.json"
    if cache.exists():
        try:
            d = json.loads(cache.read_text(encoding="utf-8"))
            print(f"  稿源: 缓存稿 .cache/{tid}.json")
            if use_ai:
                save_draft(tid, d)
            return d
        except json.JSONDecodeError:
            pass

    print("  稿源: 生成中…")
    draft = write_draft(topic, client, cache_dir=CACHE_DIR)
    if use_ai:
        save_draft(tid, draft)
    return draft


def build_article_md(draft: dict, images: list[str], topic: dict) -> str:
    """配文：图插在对应段落前，点线列表跟着走。"""
    lines = [f"# {draft['title']}", ""]
    if draft.get("subtitle"):
        lines += [f"> {draft['subtitle']}", ""]
    lines += [f"![封面](images/{images[0]})", ""]

    for i, page in enumerate(draft["pages"]):
        if i + 1 < len(images):
            lines += [f"![图 {i + 1}](images/{images[i + 1]})", ""]
        if page.get("note"):
            lines += [page["note"], ""]
        if page.get("points"):
            lines += [f"- {pt}" for pt in page["points"]]
            lines += [""]

    lines += ["---", "", topic.get("cta") or "用 ThinkNote 边聊边记：thinknote.pro", ""]
    lines += [f"<!-- id: {topic.get('id')} -->"]
    return "\n".join(lines) + "\n"


def build_topic(topic: dict, client: LLMClient, use_ai: bool = False) -> Path | None:
    tid = topic.get("id")
    if not tid:
        return None
    print(f"\n=== {tid} · {topic.get('topic', '')}")

    draft = resolve_draft(topic, client, use_ai=use_ai)
    if not draft.get("pages"):
        print("  skip: 无页面内容")
        return None

    out = OUT_DIR / tid
    if out.exists():
        shutil.rmtree(out)
    img_dir = out / "images"
    img_dir.mkdir(parents=True)

    theme = topic.get("theme") or pick_theme(tid)
    renderer = PosterRenderer(out, ASSETS_DIR)

    cover = renderer.render_cover(
        title=draft["title"],
        subtitle=draft["subtitle"],
        kicker=draft.get("kicker", ""),
        theme=theme,
        out_name="01-cover.jpg",
    )
    shutil.copy(cover, img_dir / cover.name)
    images = [cover.name]

    shot = topic.get("shot") or ""
    n = len(draft["pages"])
    for i, page in enumerate(draft["pages"], start=1):
        name = f"{i + 1:02d}-page{i}.jpg"
        p = renderer.render_page(
            headline=page["headline"],
            note=page.get("note", ""),
            points=page.get("points", []),
            kicker=page.get("kicker") or draft.get("kicker", ""),
            shot=shot if (shot and i == n) else "",
            theme=theme,
            page_label=f"{i}/{n}",
            out_name=name,
        )
        shutil.copy(p, img_dir / p.name)
        images.append(p.name)

    (out / "draft.json").write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "article.md").write_text(build_article_md(draft, images, topic), encoding="utf-8")

    print(f"  -> {out}  ({len(images)} 张图)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="构建图解风微信图文")
    ap.add_argument("--topic", help="只构建指定选题 id")
    ap.add_argument("--ai", action="store_true", help="用 LLM 生成/覆盖草稿并存为成品稿")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    topics = load_topics()
    if args.list:
        for t in topics:
            has = "✓稿" if (DRAFTS_DIR / f"{t['id']}.json").exists() else " 待写"
            print(f"{t['id']:<10} [{t.get('kicker','')}] {has}  {t.get('topic','')}")
        return

    if args.topic:
        topics = [t for t in topics if t.get("id") == args.topic]
        if not topics:
            raise SystemExit(f"找不到选题：{args.topic}")

    cfg = load_config()
    client = LLMClient(cfg.get("llm") or {})
    if args.ai and not client.available:
        print("! 未配置 API key，无法用 --ai。请先跑 pipeline/setup_key.py")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for t in topics:
        try:
            if build_topic(t, client, use_ai=args.ai):
                ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  !! 失败：{exc}")
    print(f"\n完成：{ok}/{len(topics)} 篇 → {OUT_DIR}")


if __name__ == "__main__":
    main()
