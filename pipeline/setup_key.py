#!/usr/bin/env python3
"""一次性导入 LLM 配置 → config.yml。

用法（三种任选）：
  1) 直接粘贴：python pipeline/setup_key.py
  2) 从剪贴板：python pipeline/setup_key.py --clipboard
  3) 已在环境变量：python pipeline/setup_key.py --from-env

设计：key 只写入本机 config.yml，不打印明文，日志只显示掩码。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.yml"
EXAMPLE = ROOT / "config.example.yml"


def mask(s: str) -> str:
    if not s:
        return "(空)"
    return f"{s[:6]}…{s[-4:]}" if len(s) > 12 else "***"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clipboard", action="store_true", help="从剪贴板读取 key")
    ap.add_argument("--from-env", action="store_true", help="从环境变量读取 key")
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    cfg = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8")) if EXAMPLE.exists() else {}
    llm = cfg.setdefault("llm", {})

    if args.from_env:
        key = os.environ.get("GRAPHICS_LLM_API_KEY", "") or os.environ.get("LLM_API_KEY", "")
    elif args.clipboard:
        try:
            import subprocess

            key = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=10,
            ).stdout.strip()
        except Exception as exc:  # noqa: BLE001
            print(f"读取剪贴板失败：{exc}")
            return
    else:
        print("请粘贴 API Key（输入不回显，直接粘贴后回车）:")
        import getpass

        key = getpass.getpass("").strip()

    if not key:
        print("没有拿到 key，配置未写入。")
        return

    llm["api_key"] = key
    if args.base_url:
        llm["base_url"] = args.base_url
    if args.model:
        llm["model"] = args.model

    CONFIG.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"已写入 {CONFIG}")
    print(f"  base_url = {llm.get('base_url')}")
    print(f"  model    = {llm.get('model')}")
    print(f"  api_key  = {mask(llm['api_key'])}")
    print("\n下一步：python pipeline/build.py --topic ai-001 --force")


if __name__ == "__main__":
    main()
