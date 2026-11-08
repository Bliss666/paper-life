#!/usr/bin/env python3
"""发布调度器：每天定时自动出稿。

配合 Windows 任务计划程序使用（见 install_schedule.ps1）：
  · 每天定点自动构建当天要发的图文
  · 构建结果落到 out/<日期>/，附一份可直接粘贴的 article.md
  · 同一篇内容不会重复排期（轮转选题库）

用法：
  python pipeline/scheduler.py            # 构建「今天」那一期
  python pipeline/scheduler.py --date 2026-11-07
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
ROOT = PIPELINE_DIR.parent
sys.path.insert(0, str(PIPELINE_DIR))

from build import build_topic, load_config, load_topics  # noqa: E402
from llm import LLMClient  # noqa: E402
from publisher import load_state, pick_next, save_state  # noqa: E402
SCHEDULE_DIR = ROOT / "schedule"
SCHEDULE_PATH = SCHEDULE_DIR / "plan.json"


def load_plan() -> dict:
    if SCHEDULE_PATH.exists():
        return json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    return {"assigned": {}, "history": {}}


def save_plan(plan: dict) -> None:
    SCHEDULE_DIR.mkdir(parents=True, exist_ok=True)
    SCHEDULE_PATH.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


def topic_for(day: str, topics: list[dict], state: dict, plan: dict) -> dict | None:
    """按日期稳定地分配一个选题，同一天永远拿到同一个。"""
    if day in plan.get("assigned", {}):
        tid = plan["assigned"][day]
        return next((t for t in topics if t.get("id") == tid), None)

    picked = pick_next(topics, state, 1)
    if not picked:
        return None
    tid = picked[0]["id"]
    plan.setdefault("assigned", {})[day] = tid
    return picked[0]


def main() -> None:
    ap = argparse.ArgumentParser(description="定时出稿调度器")
    ap.add_argument("--date", help="指定日期 YYYY-MM-DD，默认今天")
    ap.add_argument("--list", action="store_true", help="查看排期表")
    args = ap.parse_args()

    topics = load_topics()
    plan = load_plan()
    state = load_state()

    if args.list:
        for day, tid in sorted(plan.get("assigned", {}).items()):
            t = next((x for x in topics if x.get("id") == tid), None)
            print(f"{day}  {tid:<10} {t.get('topic', '') if t else ''}")
        return

    day = args.date or date.today().isoformat()
    topic = topic_for(day, topics, state, plan)
    save_plan(plan)

    if topic is None:
        print("选题库为空")
        return

    print(f"=== {day} → {topic['id']} · {topic.get('topic', '')}")
    cfg = load_config()
    client = LLMClient(cfg.get("llm") or {})
    out = build_topic(topic, client)

    if out:
        print(f"  产物 → {out}")

    state.setdefault("built", []).append(topic["id"])
    state["last_built"] = day
    save_state(state)
    plan.setdefault("history", {})[day] = topic["id"]
    save_plan(plan)


if __name__ == "__main__":
    main()
