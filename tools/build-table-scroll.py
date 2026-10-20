#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列の多い表が画面からはみ出し、ページごと横にずれるのを防ぐ指定を、全ページに入れる。

2026-10-19 に tools/_common_page.py へ同じ指定を入れたが、それが効くのは
そこから生成しているページ（サイズ帯・型番索引・廃盤）だけだった。
製品ページは products/index.html の style を持つ手書きのページで、指定が届いていなかった。
実際、イナバ フォルタのページは画面幅360pxで「近い他社型番」の表がはみ出していた
（ページ全体が横に385pxへ広がっていた）。

対象は .tbl と .sizes の2つ。
.spec は「扉：引き戸2枚・片開き（右側固定パネル）＋…」のような長い文章が入る2列の表で、
折り返さないと読めなくなるため入れない。

publish.sh から自動で呼ばれる。何度実行しても同じ結果になる。
"""
import glob, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BEG, END = "/* TABLESCROLL_START */", "/* TABLESCROLL_END */"

CSS = BEG + """
  /* 画面が狭いとき、表は自分の箱の中で横に流す。ページごと横にずれるのを防ぐ。
     折り返さないのは、折り返すとシリーズ名や型番が1文字ずつ縦に並ぶため。
     .spec は長い文章が入るので対象にしない */
  @media (max-width: 860px) {
    .tbl, .sizes { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }
    .tbl th, .tbl td, .sizes th, .sizes td { white-space: nowrap; }
  }
""" + END + "\n"


def main():
    pages = sorted(set(glob.glob(os.path.join(ROOT, "*.html"))
                       + glob.glob(os.path.join(ROOT, "*", "*.html"))))
    n = 0
    for p in pages:
        s = io.open(p, encoding="utf-8").read()
        orig = s
        s = re.sub(re.escape(BEG) + r".*?" + re.escape(END) + r"\n?", "", s, flags=re.S)
        need = ('class="tbl"' in s or 'class="sizes"' in s
                or "class='tbl'" in s or "class='sizes'" in s)
        if need:
            i = s.find("</style>")
            if i < 0:
                print("  飛ばす（styleが無い）:", os.path.relpath(p, ROOT)); continue
            s = s[:i] + CSS + s[i:]
        if s != orig:
            io.open(p, "w", encoding="utf-8").write(s)
            n += 1
    have = sum(1 for p in pages
               if BEG in io.open(p, encoding="utf-8").read())
    print("[表の横流し] %d ページを更新（指定あり %d ページ）" % (n, have))
    return 0


if __name__ == "__main__":
    sys.exit(main())
