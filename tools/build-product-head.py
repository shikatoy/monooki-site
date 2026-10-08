#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
製品ページの見出し情報（title・description・OG・JSON-LD・パンくず・リード）を
index.html の PRODUCTS から作り直す。無いページは雛形から作る。

これまで手で書いていたため、PRODUCTS を直してもページの頭が古いまま残った。
2026-10-06 時点で実際に起きていたズレ：
  ・宅配ボックス … 10/04 に区分を小型物置から宅配ボックスへ変えたのに、
                   description と肩書きが「小型物置」のまま
  ・Mr.ストックマン ダンディ … 51型番あるのに description が「全7型番」
サイズ表（build-product-sizes.py）と仕様・特徴（build-product-spec.py）は
すでに生成に移してあるので、残っていた頭の部分をここで引き取る。

    python3 tools/build-product-head.py
"""
import importlib.util, io, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

TEMPLATE = os.path.join(HERE, "_product_template.html")
SITE = "https://monooki-erabi.com/"
NAME = "物置どれがいい？"


def fmt(n):
    return "{:,}".format(int(n))


def rng(vals, unit="mm"):
    lo, hi = min(vals), max(vals)
    return "%s%s" % (fmt(lo), unit) if lo == hi else "%s〜%s%s" % (fmt(lo), fmt(hi), unit)


def field_of(raw, key):
    m = re.search(key + r":'((?:[^'\\]|\\.)*)'", raw)
    return m.group(1).replace("\\'", "'") if m else ""


def base_of(p, raw):
    """description の後半。pageDesc があればそちらを使う。
    base はトップの索引カードの文で、ページの説明としては言い足りないことがある
    （例 エルモシャッター：高さの段が1つしかないことを書いていた）。
    PRODUCTS に pageDesc を置けば、その機種だけ差し替えられる。"""
    return field_of(raw, "pageDesc") or field_of(raw, "base")


def raws():
    """PRODUCTS の各要素のソースを id ごとに返す（base を取るため）。"""
    s = io.open(os.path.join(C.ROOT, "index.html"), encoding="utf-8").read()
    i = s.index("const PRODUCTS"); i = s.index("[", i)
    out, depth, st = {}, 0, None
    for k in range(i, len(s)):
        ch = s[k]
        if ch == "{":
            if depth == 0: st = k
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                e = s[st:k + 1]
                m = re.match(r"\{ id:'([^']+)'", e)
                if m: out[m.group(1)] = e
        elif ch == "]" and depth == 0:
            break
    return out


def fields(p, raw):
    mk = C.MAKER_JP[p["maker"]]
    nm, cat = p["name"], p["cat"]
    ws = [s[1] for s in p["sizes"]]
    ds = [s[2] for s in p["sizes"]]
    n = len(p["sizes"])
    base = base_of(p, raw)
    dims = ("間口%s・奥行%s、全%d型番。" % (rng(ws), rng(ds), n)) if n else ""
    # 「宅配ボックス（宅配ボックス）」のような重複を避ける
    kind = "" if cat == nm else "（%s）" % cat
    return dict(
        title="%s %s｜サイズ一覧と仕様｜%s" % (mk, nm, NAME),
        ogtitle="%s %s｜サイズ一覧と仕様" % (mk, nm),
        desc="%sの%s%sのサイズ一覧と仕様。%s%s" % (mk, nm, kind, dims, base),
        keywords="%s %s, %s 寸法, %s サイズ, %s %s, 物置 %s" % (mk, nm, nm, nm, mk, cat, cat),
        url=SITE + p["page"].replace(os.sep, "/"),
        kicker="%s — %s" % (mk, cat),
        h1="%s %s" % (mk, nm),
        lead=base,
        crumb=nm,
        brand=mk,
    )


def sub1(s, pat, new, where):
    out, k = re.subn(pat, lambda m: m.group(0).replace(m.group(1), new, 1), s, count=1)
    if k != 1:
        raise SystemExit("[中止] %s が見つかりません（雛形を変えたなら、このスクリプトも直してください）" % where)
    return out


def apply(s, f):
    e = C.esc
    s = sub1(s, r"<title>(.*?)</title>", e(f["title"]), "title")
    s = sub1(s, r'<meta name="description" content="(.*?)"', e(f["desc"]), "description")
    s = sub1(s, r'<meta name="keywords" content="(.*?)"', e(f["keywords"]), "keywords")
    s = sub1(s, r'<link rel="canonical" href="(.*?)"', f["url"], "canonical")
    s = sub1(s, r'<meta property="og:title" content="(.*?)"', e(f["ogtitle"]), "og:title")
    s = sub1(s, r'<meta property="og:description" content="(.*?)"', e(f["desc"]), "og:description")
    s = sub1(s, r'<meta property="og:url" content="(.*?)"', f["url"], "og:url")
    # JSON-LD（WebPage）
    s = sub1(s, r'"@type": "WebPage",\s*\n\s*"name": (".*?")', json.dumps(f["ogtitle"], ensure_ascii=False), "JSON-LD name")
    s = sub1(s, r'"url": (".*?"),\n  "inLanguage"', json.dumps(f["url"], ensure_ascii=False), "JSON-LD url")
    s = sub1(s, r'"description": (".*?"),\n  "url"', json.dumps(f["desc"], ensure_ascii=False), "JSON-LD description")
    s = sub1(s, r'"@type": "Brand",\s*\n\s*"name": (".*?")', json.dumps(f["brand"], ensure_ascii=False), "JSON-LD brand")
    s = sub1(s, r'"keywords": (".*?")\n\}', json.dumps(f["keywords"], ensure_ascii=False), "JSON-LD keywords")
    # パンくず（JSON-LD の3番目と、本文の nav）
    s = sub1(s, r'"position": 3,\s*\n\s*"name": (".*?")', json.dumps(f["crumb"], ensure_ascii=False), "パンくず(JSON-LD)")
    s = sub1(s, r'<a href="\./">製品</a><span>/</span>(.*?)\n', e(f["crumb"]), "パンくず(本文)")
    s = sub1(s, r'<p class="article-kicker">(.*?)</p>', e(f["kicker"]), "肩書き")
    s = sub1(s, r'<h1 class="article-title">(.*?)</h1>', e(f["h1"]), "見出し")
    s = sub1(s, r'<p class="article-lead">(.*?)</p>', e(f["lead"]), "リード")
    return s


def main():
    src = raws()
    made, upd = 0, 0
    for p in C.load_products():
        if not p["page"]:
            raise SystemExit("[中止] %s に製品ページの対応がありません。index.html の PRODUCT_PAGES に足してください。" % p["id"])
        path = os.path.join(C.ROOT, p["page"])
        if not os.path.exists(path):
            shutil.copyfile(TEMPLATE, path)
            made += 1
            print("  新規作成 %s" % p["page"])
        s = io.open(path, encoding="utf-8").read()
        s2 = apply(s, fields(p, src.get(p["id"], "")))
        if s2 != s:
            io.open(path, "w", encoding="utf-8").write(s2)
            upd += 1
            print("  %-36s 見出し情報を更新" % os.path.basename(p["page"]))
    print("[製品ページの見出し情報] 新規 %d / 更新 %d" % (made, upd))
    return 0


if __name__ == "__main__":
    sys.exit(main())
