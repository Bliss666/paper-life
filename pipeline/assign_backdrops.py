# -*- coding: utf-8 -*-
"""给 life_topics.yml 的每个分镜指定对应背景场景。

用法：python pipeline/assign_backdrops.py
会就地改写 content/life_topics.yml，为每页加上 top_backdrop / bottom_backdrop。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YML = ROOT / "content" / "life_topics.yml"

# (topic_id, page_index) -> (top_backdrop, bottom_backdrop)
# page_index 从 1 开始
MAP: dict[tuple[str, int], tuple[str, str]] = {
    # ── tip-001 五个被低估的技巧 ──
    ("tip-001", 1): ("phone", "chat"),
    ("tip-001", 2): ("phone", "phone"),
    ("tip-001", 3): ("cabinet", "cabinet"),
    ("tip-001", 4): ("chat", "desk"),
    ("tip-001", 5): ("door", "door"),
    # ── tip-002 三个野方法记住任何东西 ──
    ("tip-002", 1): ("books", "radio"),
    ("tip-002", 2): ("books", "checklist"),
    ("tip-002", 3): ("books", "bulb"),
    ("tip-002", 4): ("books", "voice"),
    ("tip-002", 5): ("night", "bulb"),
    # ── tip-003 打字不用看键盘 ──
    ("tip-003", 1): ("keyboard", "keyboard"),
    ("tip-003", 2): ("keyboard", "keyboard"),
    ("tip-003", 3): ("keyboard", "desk"),
    ("tip-003", 4): ("night", "road"),
    ("tip-003", 5): ("keyboard", "keyboard"),
    # ── tip-004 拍照构图 ──
    ("tip-004", 1): ("camera", "camera"),
    ("tip-004", 2): ("camera", "camera"),
    ("tip-004", 3): ("camera", "camera"),
    ("tip-004", 4): ("camera", "camera"),
    ("tip-004", 5): ("camera", "mirror"),
    # ── tip-005 开会记不住重点 ──
    ("tip-005", 1): ("meeting", "meeting"),
    ("tip-005", 2): ("meeting", "checklist"),
    ("tip-005", 3): ("meeting", "meeting"),
    ("tip-005", 4): ("meeting", "road"),
    # ── tip-006 回消息 ──
    ("tip-006", 1): ("chat", "chat"),
    ("tip-006", 2): ("chat", "chat"),
    ("tip-006", 3): ("chat", "voice"),
    ("tip-006", 4): ("chat", "chat"),
    # ── tip-007 出门前十件事 ──
    ("tip-007", 1): ("commute", "commute"),
    ("tip-007", 2): ("commute", "kitchen"),
    ("tip-007", 3): ("desk", "checklist"),
    ("tip-007", 4): ("office", "cabinet"),
    # ── tip-008 房间变高级 ──
    ("tip-008", 1): ("living", "living"),
    ("tip-008", 2): ("living", "living"),
    ("tip-008", 3): ("living", "living"),
    # ── tip-009 读长文三步 ──
    ("tip-009", 1): ("books", "books"),
    ("tip-009", 2): ("books", "books"),
    ("tip-009", 3): ("books", "radio"),
    # ── tip-010 求人办事怎么说 ──
    ("tip-010", 1): ("voice", "cards"),
    ("tip-010", 2): ("voice", "voice"),
    ("tip-010", 3): ("voice", "cards"),
    ("tip-010", 4): ("cards", "office"),
    # ── tip-011 记账只记三类 ──
    ("tip-011", 1): ("money", "money"),
    ("tip-011", 2): ("night", "money"),
    ("tip-011", 3): ("money", "wallet"),
    # ── tip-012 拖延的解药 ──
    ("tip-012", 1): ("night", "road"),
    ("tip-012", 2): ("checklist", "desk"),
    ("tip-012", 3): ("mountain", "checklist"),
    ("tip-012", 4): ("chat", "desk"),
    # ── tip-013 文件夹这样建 ──
    ("tip-013", 1): ("cabinet", "cabinet"),
    ("tip-013", 2): ("drawer", "drawer"),
    ("tip-013", 3): ("cabinet", "cabinet"),
    # ── tip-014 让人秒回的消息 ──
    ("tip-014", 1): ("chat", "chat"),
    ("tip-014", 2): ("chat", "chat"),
    ("tip-014", 3): ("chat", "chat"),
    # ── tip-015 存钱只做一件事 ──
    ("tip-015", 1): ("wallet", "wallet"),
    ("tip-015", 2): ("money", "money"),
    ("tip-015", 3): ("money", "money"),
    # ── life-001 别为不重要的人解释自己 ──
    ("life-001", 1): ("voice", "voice"),
    ("life-001", 2): ("voice", "rain"),
    ("life-001", 3): ("chat", "chat"),
    ("life-001", 4): ("rain", "mountain"),
    ("life-001", 5): ("voice", "door"),
    # ── life-002 二十几岁存款没那么重要 ──
    ("life-002", 1): ("money", "mountain"),
    ("life-002", 2): ("office", "office"),
    ("life-002", 3): ("money", "road"),
    ("life-002", 4): ("bulb", "cards"),
    ("life-002", 5): ("map", "road"),
    # ── life-003 允许一切发生 ──
    ("life-003", 1): ("rain", "road"),
    ("life-003", 2): ("rain", "map"),
    ("life-003", 3): ("rain", "road"),
    ("life-003", 4): ("rain", "mountain"),
    ("life-003", 5): ("night", "road"),
    # ── life-004 情绪稳定的人不解释 ──
    ("life-004", 1): ("rain", "voice"),
    ("life-004", 2): ("voice", "voice"),
    ("life-004", 3): ("rain", "night"),
    ("life-004", 4): ("night", "bulb"),
    ("life-004", 5): ("crowd", "road"),
    # ── life-005 圈子比努力值钱 ──
    ("life-005", 1): ("night", "office"),
    ("life-005", 2): ("office", "crowd"),
    ("life-005", 3): ("night", "crowd"),
    ("life-005", 4): ("kitchen", "crowd"),
    ("life-005", 5): ("crowd", "cards"),
}


def main() -> int:
    text = YML.read_text(encoding="utf-8")
    lines = text.split("\n")

    cur_topic = None
    page_no = 0
    out: list[str] = []
    changed = 0

    for ln in lines:
        m = re.match(r"^- id:\s*(\S+)", ln)
        if m:
            cur_topic = m.group(1)
            page_no = 0
            out.append(ln)
            continue

        # 新的一页（以 "    - top:" 开头）
        if re.match(r"^    - top:", ln):
            page_no += 1
            key = (cur_topic, page_no)
            if key in MAP:
                top_bd, bot_bd = MAP[key]
                out.append(ln)
                out.append(f"      top_backdrop: {top_bd}")
                out.append(f"      bottom_backdrop: {bot_bd}")
                changed += 1
                continue
            out.append(ln)
            continue

        out.append(ln)

    YML.write_text("\n".join(out), encoding="utf-8")
    print(f"已写入 {changed} 组背景场景 → {YML}")
    missing = [k for k in MAP if k[1] > 5]
    if missing:
        print("警告：页码超出范围的映射：", missing)
    return 0


if __name__ == "__main__":
    sys.exit(main())
