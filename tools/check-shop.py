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
・ページに書き出された行き先が、EXSHOP の値から作ったものと一致するか
  （2026-10-26 に、build-shop-links.py が自前でURLを組み立てていたせいで、
    ペインタの製品ページのリンクが se_series=series:word:ペインタ という
    存在しないシリーズを指していた。index.html 側だけが正しかった）
"""
import glob, io, os, re, sys
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
        if not re.fullmatch(r"(mo:|wh:|xz:)?([a-z]+_s\d+|word:.+|item:\d+)", code):
            bad.append("%s の書き方が分かりません（%s）" % (pid, code))

    seen = defaultdict(list)
    for pid, code in ex.items():
        if ":word:" in code or code.startswith("word:"):
            continue
        seen[code].append(prods.get(pid, {}).get("name", pid))
    for code, names in sorted(seen.items()):
        if len(names) > 1:
            bad.append("%s を %s が同時に指しています（押した先が別のシリーズになります）"
                       % (code, "・".join(sorted(names))))

    # ページに書き出された行き先を、EXSHOP の値から作ったものと突き合わせる
    allowed = set(C.aff_url(c) for c in set(ex.values()))
    pat = re.compile(r'href="(//ck\.jp\.ap\.valuecommerce\.com[^"]*)"')
    mine = "pid=%s" % C.PID                       # 自分のMyLink。別pidの公式バナーは対象外
    n_link = 0
    for f in sorted(glob.glob(os.path.join(C.ROOT, "**", "*.html"), recursive=True)):
        rel = os.path.relpath(f, C.ROOT)
        if rel.startswith("tools" + os.sep):
            continue
        with io.open(f, encoding="utf-8") as fh:
            body = fh.read()
        for h in sorted(set(pat.findall(body))):
            if mine not in h:
                continue
            n_link += 1
            if h not in allowed:
                bad.append("%s の行き先が EXSHOP から作れない形です（%s…）" % (rel, h[:110]))

    # 製品ページは、その製品の行き先が1本だけ出ているか
    for p in C.load_products():
        page = p.get("page")
        if not page:
            continue
        with io.open(os.path.join(C.ROOT, page), encoding="utf-8") as fh:
            body = fh.read()
        hs = sorted(set(h for h in pat.findall(body) if mine in h))
        code = ex.get(p["id"])
        if code is None:
            if hs:
                bad.append("%s は行き先が無いのに提携リンクが出ています" % page)
        elif hs != [C.aff_url(code)]:
            bad.append("%s の提携リンクが EXSHOP の %s と合っていません" % (page, code))

    if bad:
        print("[中止] 提携先リンクに問題があります")
        for b in bad:
            print("   -", b)
        return 1

    n_wh = sum(1 for c in ex.values() if c.startswith("wh:"))
    n_xz = sum(1 for c in ex.values() if c.startswith("xz:"))
    n_wd = sum(1 for c in ex.values() if c.startswith("word:"))
    print("[提携先リンク] ページ上のリンク %d 本を EXSHOP と突き合わせました" % n_link)
    print("[提携先リンク] %d シリーズ"
          "（物置・収納 %d / 倉庫・ガレージ %d / お問い合わせ商品 %d / 商品名で絞る %d）"
          % (len(ex), len(ex) - n_wh - n_xz - n_wd, n_wh, n_xz, n_wd))
    return 0


if __name__ == "__main__":
    sys.exit(main())
