# -*- coding: utf-8 -*-
"""生成一个本地画廊页，用来在浏览器里一次看完多期产物。

用法：
    python pipeline/make_gallery.py            # 生成 out/_gallery.html
    python pipeline/make_gallery.py --issue sk-03 sk-07   # 只看指定几期
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"

TPL = """<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>《纸上人生》产物画廊</title>
<style>
 body{margin:0;background:#1b1b1f;color:#eee;font-family:"Microsoft YaHei",sans-serif}
 h2{margin:28px 20px 8px;font-size:18px;font-weight:600}
 .row{display:flex;gap:10px;overflow-x:auto;padding:0 20px 18px}
 .card{flex:0 0 220px}
 .card img{width:220px;border-radius:8px;display:block;background:#000}
 .cap{font-size:12px;color:#aaa;margin-top:4px}
</style></head><body>
<h1 style="padding:20px">《纸上人生》产物画廊 · 共 {n} 期</h1>
{body}
</body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", nargs="*", help="只看指定期次")
    args = ap.parse_args()

    dirs = sorted(d for d in OUT.glob("sk-*") if d.is_dir())
    if args.issue:
        want = set(args.issue)
        dirs = [d for d in dirs if d.name in want]

    body = []
    for d in dirs:
        imgs = sorted((d / "images").glob("*.jpg"))
        if not imgs:
            continue
        cards = "".join(
            f'<div class="card"><img src="{d.name}/images/{p.name}">'
            f'<div class="cap">{p.name}</div></div>'
            for p in imgs
        )
        body.append(f"<h2>{d.name}</h2><div class=\"row\">{cards}</div>")

    out = OUT / "_gallery.html"
    out.write_text(TPL.replace("{n}", str(len(dirs))).replace("{body}", "\n".join(body)),
                   encoding="utf-8")
    print(f"-> {out}  ({len(dirs)} 期)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
