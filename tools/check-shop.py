#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提携先リンク（index.html の EXSHOP）を公開前に検査する。

行き先が別のシリーズになっていても、画面上は普通のリンクに見える。
読者は押した先で違う商品を見ることになるので、ここで止める。

・同じカテゴリで、2つのシリーズが同じ識別子を指していないか
  （2026-10-19 に、ペインタがグランプレステージ ジャンプの識別子を
    指しているのを、この検査を書く過程で見つけた）
・知らない書き方が混じっていないか
・EXSHOP の id が PRODUCTS にあるか
"""
import os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _common_page as C                                   # noqa: E402


def main():
    ex = C.load_exshop()
    if not ex:
        print("[中止] index.html の EXSHOP を読めませんでした")
        return 1
    prods = {p["id"]: p for p in C.load_products()}
    bad = []

    for pid, code in sorted(ex.items()):
        if pid not in prods:
            bad.append("%s は PRODUCTS にありません" % pid)
        if not re.fullmatch(r"(wh:)?[a-z]+_s\d+|word:.+", code):
            bad.append("%s の書き方が分かりません（%s）" % (pid, code))

    seen = defaultdict(list)
    for pid, code in ex.items():
        if code.startswith("word:"):
            continue
        seen[code].append(prods.get(pid, {}).get("name", pid))
    for code, names in sorted(seen.items()):
        if len(names) > 1:
            bad.append("%s を %s が同時に指しています（押した先が別のシリーズになります）"
                       % (code, "・".join(sorted(names))))

    if bad:
        print("[中止] 提携先リンクに問題があります")
        for b in bad:
            print("   -", b)
        return 1

    n_wh = sum(1 for c in ex.values() if c.startswith("wh:"))
    n_wd = sum(1 for c in ex.values() if c.startswith("word:"))
    print("[提携先リンク] %d シリーズ（物置・収納 %d / 倉庫・ガレージ %d / 商品名で絞る %d）"
          % (len(ex), len(ex) - n_wh - n_wd, n_wh, n_wd))
    return 0


if __name__ == "__main__":
    sys.exit(main())
