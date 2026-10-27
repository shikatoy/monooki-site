#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# サイト内リンクが実在するファイルを指しているかを確かめる。
#
# 2026-09-27：記事を1本取り下げたあと、製品ページ18枚に残った
# その記事へのリンクが3週間そのままになっていた。取り下げ側で
# 流入リンクを消していなかったのが原因。以後は publish.sh で毎回見る。
#
# 2026-10-26：スクリプトの中に書いた文字列も見るようにした。
# 計測タグの判定に書いていた文字列を Google が URL として拾い、
# 存在しないページをクロールして404にしていた。
# 画面に出るリンクではないので、上の検査では見つからなかった。
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
    # スクリプトの中の、パスに見える文字列。Googleはここも URL の候補として拾う
    jsbad = {}
    jspat = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S)
    strpat = re.compile(r"""['"](/[A-Za-z0-9._/-]*)['"]""")
    for p in pages:
        s = io.open(p, encoding="utf-8").read()
        for body in jspat.findall(s):
            for v in set(strpat.findall(body)):
                if v == "/" or v.startswith("//"):
                    continue
                t = os.path.join(ROOT, v.lstrip("/"))
                if os.path.exists(t) or os.path.exists(t.rstrip("/")):
                    continue
                jsbad.setdefault(v, []).append(os.path.relpath(p, ROOT))

    if not bad and not jsbad:
        print("[リンク] %d ページ／切れリンクなし" % len(pages))
        return 0
    for v, where in sorted(jsbad.items()):
        print("[中止] スクリプトの中に、実在しないパスの文字列があります: %s（%d ページ）"
              % (v, len(where)))
        for w in where[:5]:
            print("         ", w)
        print("          Google がこれを URL として拾い、404 をクロールします。"
              "パスを文字列で書かない形に直してください。")
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
