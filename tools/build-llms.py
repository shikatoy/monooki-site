#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llms.txt の「記事」の一覧を、index.html の ARTICLES から作り直す。

記事の取り下げを行単位でやると、llms.txt に空行だけが残って
次の公開の差し込み位置が見つからなくなる（2026-09-10 に発生）。
一覧は毎回まるごと作り直す方式にして、その事故を起こらなくする。

    python3 tools/build-llms.py
"""
import os, re, io

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def articles():
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    i = s.index("const ARTICLES")
    blk = s[i:s.index("];", i)]
    out = []
    for m in re.finditer(
            r"\{\s*date:'([^']+)',[^}]*?title:'([^']*)',\s*lead:'([^']*)',\s*url:'articles/([^']+)\.html'",
            blk, re.S):
        out.append(dict(date=m.group(1), title=m.group(2), lead=m.group(3), slug=m.group(4)))
    return out


def main():
    arts = articles()
    p = os.path.join(ROOT, "llms.txt")
    s = io.open(p, encoding="utf-8").read()

    listing = "\n".join(
        "  - 「%s」(/articles/%s.html, %s): %s" % (a["title"], a["slug"], a["date"], a["lead"])
        for a in arts)

    # 1. 「## 主なコンテンツ」の中の記事一覧
    head = "- 記事: 物置の設置と選び方にまつわる読みもの。掲載中の記事は以下のとおり"
    tail = "- コラム:"
    i, j = s.index(head), s.index(tail)
    s = s[:i] + head + "\n" + listing + "\n" + s[j:]

    # 2. 「## ページ」の中の記事行
    s = re.sub(r"(?m)^- 記事「.*?$\n", "", s)
    anchor = "- 記事一覧: /articles/\n"
    pages = "".join("- 記事「%s」: /articles/%s.html\n" % (a["title"], a["slug"]) for a in arts)
    s = s.replace(anchor, anchor + pages, 1)

    io.open(p, "w", encoding="utf-8").write(s)
    print("[llms.txt] 記事 %d 本を書き出しました" % len(arts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
