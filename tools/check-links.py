#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# サイト内リンクが実在するファイルを指しているかを確かめる。
#
# 2026-09-27：記事を1本取り下げたあと、製品ページ18枚に残った
# その記事へのリンクが3週間そのままになっていた。取り下げ側で
# 流入リンクを消していなかったのが原因。以後は publish.sh で毎回見る。
#
#     python3 tools/check-links.py
import os, re, io, glob, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html"))
                   + glob.glob(os.path.join(ROOT, "*", "*.html")))
    bad = {}
    for p in pages:
        s = io.open(p, encoding="utf-8").read()
        # HTMLコメント内は書き方の見本（{slug}.html など）が入るので外す
        s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
        base = os.path.dirname(p)
        for href in re.findall(r'href="([^"#?]*?\.html)(?:[#?][^"]*)?"', s):
            if href.startswith(("http://", "https://", "//", "mailto:")):
                continue
            t = os.path.normpath(os.path.join(ROOT if href.startswith("/") else base,
                                              href.lstrip("/")))
            if not os.path.exists(t):
                bad.setdefault(href, []).append(os.path.relpath(p, ROOT))
    if not bad:
        print("[リンク] %d ページ／切れリンクなし" % len(pages))
        return 0
    for href, where in sorted(bad.items()):
        print("[中止] リンク切れ %s（%d 箇所）" % (href, len(where)))
        for w in where[:10]:
            print("         ", w)
        if len(where) > 10:
            print("          ... 他 %d 箇所" % (len(where) - 10))
    print("リンク切れ %d 種類。直すまで公開しない。" % len(bad))
    return 1


if __name__ == "__main__":
    sys.exit(main())
