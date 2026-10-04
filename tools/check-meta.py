#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ページの見出し情報（description・canonical・OG）の取りこぼしとズレを見る。

記事の説明文は「ページの meta」「og」「JSON-LD」「記事一覧のカード」の
4か所に同じものが書かれている。このうちカードだけは記事を公開したときにしか
更新されないため、あとから本文を直すと1か所だけ古いまま残る
（2026-10-04 に実際に発生）。

ここで止めるのは次の4つ。どれも「正しい/正しくない」が一意に決まるものだけ。
  1. 記事一覧のカード文と、その記事の meta description が違う
  2. description / og:description / og:title / og:image / canonical が無い
  3. canonical が自分のURLを指していない
  4. 記事ファイルと記事一覧のカードの数が合わない

meta と og の文面が違うことは咎めない。トップページのように、
検索結果向けとSNS向けで長さを変えているのは意図したもの。
"""
import glob, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = "https://monooki-erabi.com/"
SKIP_DIRS = ("tools",)          # テンプレートなど、配信しないもの


def pages():
    out = []
    for f in sorted(set(glob.glob(os.path.join(ROOT, "*.html"))
                        + glob.glob(os.path.join(ROOT, "*", "*.html")))):
        rel = os.path.relpath(f, ROOT)
        if rel.split(os.sep)[0] in SKIP_DIRS:
            continue
        out.append(rel)
    return out


def txt(s, pat):
    m = re.search(pat, s, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else None


def canonical_for(rel):
    u = rel.replace(os.sep, "/")
    if u == "index.html":
        return SITE
    if u.endswith("/index.html"):
        return SITE + u[: -len("index.html")]
    return SITE + u


def main():
    bad = []
    rels = pages()

    for rel in rels:
        s = io.open(os.path.join(ROOT, rel), encoding="utf-8").read()
        need = {
            "description": r'<meta name="description" content="(.*?)"',
            "og:description": r'<meta property="og:description" content="(.*?)"',
            "og:title": r'<meta property="og:title" content="(.*?)"',
            "og:image": r'<meta property="og:image" content="(.*?)"',
            "canonical": r'<link rel="canonical" href="(.*?)"',
        }
        got = {k: txt(s, p) for k, p in need.items()}
        for k, v in got.items():
            if not v:
                bad.append((rel, "%s が無い" % k))
        if got["canonical"]:
            exp = canonical_for(rel)
            if got["canonical"] != exp:
                bad.append((rel, "canonical が %s（自分は %s）" % (got["canonical"], exp)))
        if got["og:image"]:
            local = got["og:image"].replace(SITE, "")
            if not os.path.exists(os.path.join(ROOT, local)):
                bad.append((rel, "og:image の画像が無い: " + local))

    # 記事一覧のカード文 ↔ 記事の description
    idxp = os.path.join(ROOT, "articles", "index.html")
    if os.path.exists(idxp):
        idx = io.open(idxp, encoding="utf-8").read()
        cards = re.findall(r'href="([a-z0-9-]+)\.html"(?:(?!</li>).)*?'
                           r'<p class="card-desc">(.*?)</p>', idx, re.S)
        seen = set()
        for slug, desc in cards:
            seen.add(slug)
            ap = os.path.join(ROOT, "articles", slug + ".html")
            if not os.path.exists(ap):
                bad.append(("articles/index.html", "カードはあるが記事が無い: " + slug))
                continue
            d = txt(io.open(ap, encoding="utf-8").read(),
                    r'<meta name="description" content="(.*?)"')
            card = re.sub(r"\s+", " ", re.sub("<[^>]+>", "", desc)).strip()
            if d and card != d:
                bad.append(("articles/index.html",
                            "カード文が記事の description と違う: %s\n        カード : %s\n        記事   : %s"
                            % (slug, card[:70], d[:70])))
        have = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, "articles", "*.html"))
                if not p.endswith("index.html")}
        for slug in sorted(have - seen):
            bad.append(("articles/index.html", "記事はあるがカードが無い: " + slug))

    if bad:
        print("[中止] ページの見出し情報に問題があります。")
        for rel, msg in bad:
            print("   %-42s %s" % (rel, msg))
        return 1
    print("[見出し情報の検査] %d ページ／記事カードの食い違いなし" % len(rels))
    return 0


if __name__ == "__main__":
    sys.exit(main())
