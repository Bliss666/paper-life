#!/usr/bin/env python3
"""发布队列管理器：决定「下一次该出哪几篇」。

核心价值
--------
· 选题库有 10+ 条，按天/按次轮转，保证内容不重复
· 记录已发布状态（state.json），发布后标记，下次自动跳到新的
· 支持「今天出什么」的预览，以及一次性批量出 7 天库存

用法：
  python pipeline/publisher.py --status          # 看当前状态
  python pipeline/publisher.py --next             # 预览下一批要出什么（不构建）
  python pipeline/publisher.py --batch 7          # 批量构建 7 篇库存（跳过已发布的）
  python pipeline/publisher.py --mark ai-002      # 标记某篇已发布
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

PIPELINE_DIR = Path(__file__).resolve().parent
ROOT = PIPELINE_DIR.parent
CONTENT_DIR = ROOT / "content"
OUT_DIR = ROOT / "out"
STATE_PATH = ROOT / "state.json"

if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from build import build_topic, load_config  # noqa: E402
from llm import LLMClient  # noqa: E402


def load_topics() -> list[dict]:
    topics: list[dict] = []
    for f in sorted(CONTENT_DIR.glob("*.yml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or []
        if isinstance(data, list):
            topics.extend(data)
    return topics


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"published": [], "last_built": None}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def pick_next(topics: list[dict], state: dict, n: int = 1) -> list[dict]:
    published = set(state.get("published", []))
    pending = [t for t in topics if t.get("id") not in published]
    if not pending:
        # 全发过了，重置轮转
        pending = list(topics)
    return pending[:n]


def main() -> None:
    ap = argparse.ArgumentParser(description="发布队列管理")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--next", action="store_true")
    ap.add_argument("--batch", type=int, default=0, help="批量构建 N 篇")
    ap.add_argument("--mark", help="标记选题为已发布")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    topics = load_topics()
    state = load_state()

    if args.mark:
        if args.mark not in state["published"]:
            state["published"].append(args.mark)
        save_state(state)
        print(f"已标记发布：{args.mark}")
        return

    if args.status:
        print(f"选题总数：{len(topics)}")
        print(f"已发布：{len(state['published'])} → {state['published']}")
        print(f"待发布：{len([t for t in topics if t.get('id') not in state['published']])}")
        print(f"上次构建：{state.get('last_built')}")
        return

    if args.next:
        for t in pick_next(topics, state, args.batch or 1):
            print(f"{t['id']:<10} [{t.get('kicker', '')}] {t.get('topic', '')}")
        return

    if args.batch:
        cfg = load_config()
        client = LLMClient(cfg.get("llm") or {})
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        picked = pick_next(topics, state, args.batch)
        for t in picked:
            try:
                build_topic(t, client, force=args.force)
                state.setdefault("built", []).append(t["id"])
            except Exception as exc:  # noqa: BLE001
                print(f"  !! {t.get('id')} 失败：{exc}")
        state["last_built"] = date.today().isoformat()
        save_state(state)
        print(f"\n完成 {len(picked)} 篇 → {OUT_DIR}")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
