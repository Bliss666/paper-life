# -*- coding: utf-8 -*-
"""AI 写稿：把一个选题扩写成「图解万物」风格的多页图文稿。

设计要点
--------
· 走 OpenAI 兼容接口（DeepSeek / Kimi / 通义 / 智谱 都行），配置在 config.yml
· 严格 JSON 输出，容错解析（模型偶尔会裹 markdown 代码块）
· 无 API / 调用失败时 → 自动降级到「本地模板引擎」，管线永不中断
· 同一选题默认走缓存，避免重复烧 token
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import requests

PIPELINE_DIR = Path(__file__).resolve().parent
ROOT = PIPELINE_DIR.parent

# ── 提示词 ──────────────────────────────────────────────
SYSTEM_PROMPT = """你是一名擅长中文新媒体爆款图文的资深操盘手，风格对标「图解万物」「樊登读书」这类知识类图文号。

你的任务：为一款叫 ThinkNote 的 AI 工具写一组「图解风」图文卡片文案。

ThinkNote 是什么：
一个浏览器扩展（也有桌面版），把 ChatGPT / Claude / Gemini / DeepSeek / 豆包 等 AI 的回答，
一键变成 Word/WPS 里「还能编辑」的内容——公式是真正的 Word 公式不是图片，表格不散架，代码块保留缩进。
还能边聊边记笔记、选中文本精准追问。核心一句话：AI 回答不再只是复制粘贴，而是直接接着往下干活。

写作铁律：
1. 每页一个观点，观点必须具体、可执行，拒绝空话套话。
2. 标题是整篇的钩子，短、狠、有张力，允许用「*星号*」标出要强调的词（渲染成强调色）。
3. 不许吹牛，不许编造数据，不许写「震惊」「必看」这类低质标题党。
4. 语气像一个真正用过的人在讲经验，不是品牌公关稿。
5. 最后一段必须自然带出 ThinkNote 的价值，落点要轻，不要硬广。

输出格式（严格 JSON，不要任何额外文字、不要 markdown 代码块）：
{
  "title": "整篇标题，一句话，12-20字",
  "subtitle": "副标题，一句话，15-30字",
  "kicker": "分类标签，2-6字，如：AI效率 / 认知觉醒 / 职场干货",
  "pages": [
    {
      "kicker": "本页小标签，2-6字，可为空",
      "headline": "本页主标题，10-24字，用 *星号* 标出强调词",
      "note": "本页补充说明，20-45字，一到两句",
      "points": ["要点1", "要点2", "要点3"]
    }
  ]
}

pages 数量：4-7 页。points 每页 2-4 条，每条不超过 20 字。"""


class Draft(dict):
    """一份图文稿。"""


# ── LLM 客户端 ──────────────────────────────────────────
class LLMClient:
    def __init__(self, cfg: dict):
        self.api_key = cfg.get("api_key") or os.environ.get("GRAPHICS_LLM_API_KEY", "")
        self.base_url = (cfg.get("base_url") or "https://api.deepseek.com/v1").rstrip("/")
        self.model = cfg.get("model") or "deepseek-chat"
        self.timeout = int(cfg.get("timeout", 90))
        self.temperature = float(cfg.get("temperature", 0.9))

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def chat(self, system: str, user: str) -> str:
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": self.temperature,
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ── JSON 容错解析 ───────────────────────────────────────
def parse_json(raw: str) -> dict:
    text = raw.strip()
    # 去掉 ```json ... ``` 包裹
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    # 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 抓最外层 {...}
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"无法解析模型输出：{raw[:200]}")


# ── 校验与规整 ──────────────────────────────────────────
def normalize(draft: dict, topic: dict) -> Draft:
    """把模型输出规整成稳定结构，字段缺失就补齐。"""
    out = Draft()
    out["title"] = (draft.get("title") or topic.get("title") or "").strip()
    out["subtitle"] = (draft.get("subtitle") or topic.get("subtitle") or "").strip()
    out["kicker"] = (draft.get("kicker") or topic.get("kicker") or "").strip()

    pages = []
    for p in draft.get("pages") or []:
        if not isinstance(p, dict):
            continue
        headline = (p.get("headline") or p.get("title") or "").strip()
        if not headline:
            continue
        points = [str(x).strip() for x in (p.get("points") or []) if str(x).strip()]
        pages.append(
            {
                "kicker": (p.get("kicker") or "").strip(),
                "headline": headline,
                "note": (p.get("note") or "").strip(),
                "points": points[:4],
            }
        )
    out["pages"] = pages
    return out


# ── 本地降级模板引擎 ────────────────────────────────────
def local_draft(topic: dict) -> Draft:
    """无 API 时的兜底：把选题里的预设文案直接组装成稿。

    选题 yml 里可以带 `fallback:` 段（pages 数组），没带就用通用骨架。
    """
    fb = topic.get("fallback") or {}
    pages = fb.get("pages")
    if not pages:
        pages = [
            {
                "kicker": topic.get("kicker", ""),
                "headline": topic.get("title", ""),
                "note": topic.get("subtitle", ""),
                "points": [],
            }
        ]
    return normalize(
        {
            "title": fb.get("title") or topic.get("title", ""),
            "subtitle": fb.get("subtitle") or topic.get("subtitle", ""),
            "kicker": fb.get("kicker") or topic.get("kicker", ""),
            "pages": pages,
        },
        topic,
    )


# ── 对外入口 ────────────────────────────────────────────
def write_draft(topic: dict, client: LLMClient, cache_dir: Path | None = None, use_cache: bool = True) -> Draft:
    """为一个选题生成图文稿。优先用缓存 → 调 LLM → 降级本地模板。"""
    tid = topic.get("id", "topic")
    cache_path = (cache_dir / f"{tid}.json") if cache_dir else None

    if use_cache and cache_path and cache_path.exists():
        try:
            return normalize(json.loads(cache_path.read_text(encoding="utf-8")), topic)
        except Exception:
            pass

    if client.available:
        user = (
            f"请为下面这个选题写一组图文卡片。\n\n"
            f"选题：{topic.get('topic') or topic.get('title')}\n"
            f"补充要求：{topic.get('brief', '') or '无'}\n"
            f"目标读者：{topic.get('audience', '经常用 AI 的职场人 / 大学生 / 内容创作者')}\n"
        )
        for attempt in range(3):
            try:
                raw = client.chat(SYSTEM_PROMPT, user)
                draft = normalize(parse_json(raw), topic)
                if draft["pages"]:
                    if cache_path:
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        cache_path.write_text(
                            json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
                        )
                    return draft
                raise ValueError("模型返回了空的 pages")
            except Exception as exc:  # noqa: BLE001
                print(f"  [llm] 第 {attempt + 1} 次失败：{exc}")
                time.sleep(2 * (attempt + 1))

    print("  [llm] 降级到本地模板引擎")
    return local_draft(topic)
