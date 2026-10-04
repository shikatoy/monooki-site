#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事に手で書いた「データから出した数」が、今のデータと合っているか確かめる。

記事は生成物ではないので、PRODUCTS が増えても本文の数字は古いまま残る。
2026-10-04 に「物置527型番／升目102」と書いた記事が実際は566／104に
なっていたのを見つけたため、この検査を入れた。

使い方：記事側で、データから出した数を span で包んで id を付ける。

    物置<span data-claim="total">566</span>型番が埋めている升目は
    <span data-claim="cells">104</span>ありました

付けられる id
    total          物置（CAT_OK）の型番の総数
    cells          間口×奥行を300mm刻みにした升目のうち、埋まっている数
    cells1/2/3     そのうち1社だけ／2社／3社がそろう升目の数
    d<数>          奥行がその値の型番数（例 d448）
    w<数>          間口がその値の型番数
    h<数>          高さがその値の型番数
    dmakers<数>    奥行がその値に入るメーカー数
    wmakers<数>    間口がその値に入るメーカー数

id が無い数字は見ない。包んだものだけを見る。
"""
import glob, importlib.util, io, os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

STEP = 300


def dataset():
    rows = []
    for p in C.load_products():
        if p["cat"] not in C.CAT_OK:
            continue
        for code, w, d, h in p["sizes"]:
            rows.append(dict(maker=p["maker"], w=w, d=d, h=h))
    return rows


def expected(cid, rows):
    """id から今の正しい数を出す。分からない id は None。"""
    if cid == "total":
        return len(rows)
    if cid.startswith("cells"):
        cell = defaultdict(set)
        for r in rows:
            cell[(r["w"] // STEP, r["d"] // STEP)].add(r["maker"])
        if cid == "cells":
            return len(cell)
        m = re.fullmatch(r"cells([123])", cid)
        if m:
            return sum(1 for v in cell.values() if len(v) == int(m.group(1)))
        return None
    m = re.fullmatch(r"([dwh])(\d+)", cid)
    if m:
        return sum(1 for r in rows if r[m.group(1)] == int(m.group(2)))
    m = re.fullmatch(r"([dw])makers(\d+)", cid)
    if m:
        k, v = m.group(1), int(m.group(2))
        return len({r["maker"] for r in rows if r[k] == v})
    return None


def main():
    rows = dataset()
    pat = re.compile(r'data-claim="([a-z0-9]+)"[^>]*>\s*([0-9,]+)\s*<')
    bad, unknown, n = [], [], 0
    files = sorted(set(glob.glob(os.path.join(ROOT, "*.html"))
                       + glob.glob(os.path.join(ROOT, "*", "*.html"))))
    for f in files:
        s = io.open(f, encoding="utf-8").read()
        for m in pat.finditer(s):
            cid, got = m.group(1), int(m.group(2).replace(",", ""))
            exp = expected(cid, rows)
            rel = os.path.relpath(f, ROOT)
            if exp is None:
                unknown.append((rel, cid)); continue
            n += 1
            if exp != got:
                bad.append((rel, cid, got, exp))

    for rel, cid in unknown:
        print("[注意] %s: 知らない claim id 「%s」。check-claims.py に足すか、綴りを直してください。" % (rel, cid))
    if bad:
        print("[中止] 本文の数字が今のデータと合っていません。")
        for rel, cid, got, exp in bad:
            print("   %-44s %-10s 本文 %s → 正しくは %s" % (rel, cid, "{:,}".format(got), "{:,}".format(exp)))
        print("   数字を直すか、記述そのものを見直してから公開してください。")
        return 1
    print("[数字の検査] %d 件すべて現在のデータと一致" % n)
    return 1 if unknown else 0


if __name__ == "__main__":
    sys.exit(main())
