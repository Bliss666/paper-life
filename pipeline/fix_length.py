# -*- coding: utf-8 -*-
"""修技巧库里的文案长度问题：把偏短的上下句补到 11~38 字，并修正非法场景名。

用法：
    python pipeline/fix_length.py            # 只看改动
    python pipeline/fix_length.py --write    # 写回 skills.yml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
YML = ROOT / "content" / "skills.yml"

# 非法场景名 → 合法场景名
SCENE_FIX = {
    "clockwallwall": "clockwall",
}

# id → (新 top, 新 bottom)
TEXT_FIX = {
    "st-005": ("你的错题本上*抄了一遍整道题*", "可是你只写*为什么错*和*下次怎么避*"),
    "st-011": ("你读论文*从第一页读到最后一页*", "可是你先读*摘要和结论*，再回头看推导"),
    "st-016": ("你记笔记时*全抄别人写的原话*", "可是你*用自己的话*再写一遍"),
    "st-017": ("你总是等*状态好了*再开始学", "可是你*先做五分钟*，状态是做出来的"),
    "st-021": ("你啃专业书*从第一章开始*", "可是你先读*目录和序言*，再看正文"),
    "st-025": ("上课你*边听边记*，笔记和脑子抢注意力", "可是你*先听完再写*，别两边都抓"),
    "wk-007": ("你夸人只会说一句*你真棒*", "可是你夸*具体的那一点*，说得出才算夸"),
    "wk-008": ("你提意见*绕三圈*才说到点上", "可是你*直接说影响*，别绕弯子"),
    "wk-011": ("你总是按*谁催得急*来排优先级", "可是你按*哪件事最值钱*排"),
    "wk-012": ("你把*重要的事*留到下午，然后没时间了", "可是你*上午先啃硬骨头*，别留到晚上"),
    "wk-015": ("出了问题你*第一反应是自证清白*", "可是你*先给解决方案*，再谈责任"),
    "cm-003": ("你总把情绪*发泄给最亲的人*", "可是你*先还给自己*消化，再开口"),
    "cm-004": ("你以为*不解释的冷漠*就是成熟", "可是*清楚*和*冷漠*不是一回事"),
    "cm-015": ("对方说*「随便」*，你当真了", "可是你*给两个具体选项*让他挑"),
    "dg-018": ("你估*大概要多久*，估出来总是差一半", "可是你*真掐一次表*，下次就有数了"),
    "dg-020": ("你输入密码*每次都要翻记录*", "可是你*让浏览器记住*，只在手机上手动"),
    "st-028": ("你背单词*盯着中文想英文*", "可是你*看着英文想中文*，反过来背"),
    "st-031": ("你复习*一上来就做新题*，跳过错题", "可是你先*把昨天的错题重做一遍*"),
    "st-035": ("你总拿自己和别人*比谁学得久*", "可是你*比谁学得进脑子*，别比时长"),
    "st-036": ("你把公式*背成了一串死文字*", "可是你*画一遍图*，公式自然长出来"),
    "wk-033": ("你的电脑桌面*堆了三十个窗口*", "可是你*开完一个关一个*，十个就够"),
    "cm-017": ("你在聊天里*连发五条*，对方来不及回", "可是你*合并成一条*发出去"),
    "cm-019": ("你*替对方说完*，结果说错了", "可是你*让他自己讲完*再接话"),
    "cm-020": ("你总爱问*「你懂我意思吧」*", "可是你*把话说明白*，别让他猜"),
    "cm-022": ("你说话*太客气*，对方听不出你态度", "可是你*把态度说清楚*，别让他猜"),
    "cm-023": ("你*发消息问在吗*，没人回", "可是你*一次把事说完*，别问在吗"),
    "cm-024": ("你和人在争执*争执到一半*，开始翻旧账", "可是你*只谈眼前这一件*，别的先放"),
    "dg-021": ("你搜索时*打一整句话*，全搜不到", "可是你*只打两三个关键词*"),
    "dg-023": ("你把重要文件*只堆在桌面上*", "可是你*存进一个专用文件夹*并同步"),
    "dg-031": ("你录视频时*声音总是忽大忽小*", "可是你*嘴离麦克风近一点*，别调音量"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    data = yaml.safe_load(YML.read_text(encoding="utf-8"))
    skills = data["skills"]

    n_text = 0
    n_scene = 0
    for s in skills:
        if s["id"] in TEXT_FIX:
            top, bottom = TEXT_FIX[s["id"]]
            if s["top"] != top or s["bottom"] != bottom:
                n_text += 1
            s["top"], s["bottom"] = top, bottom
        bd = s.get("bd")
        if bd in SCENE_FIX:
            s["bd"] = SCENE_FIX[bd]
            n_scene += 1

    print(f"文案修正 {n_text} 条，场景修正 {n_scene} 条")

    if args.write:
        header = "".join(
            line for line in YML.read_text(encoding="utf-8").splitlines(keepends=True)
            if line.startswith("#")
        )
        YML.write_text(header + yaml.safe_dump(data, allow_unicode=True, sort_keys=False,
                                                width=100, default_flow_style=False),
                        encoding="utf-8")
        print(f"已写回 {YML}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
