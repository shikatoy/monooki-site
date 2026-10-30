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

RETIRED = "<!-- RETIRED_PAGE -->"   # 取り下げページ。記事向けの自動生成は入れない


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
                if not p.endswith("index.html")
                and RETIRED not in io.open(p, encoding="utf-8").read()}
        for slug in sorted(have - seen):
            bad.append(("articles/index.html", "記事はあるがカードが無い: " + slug))

    # index.html の ARTICLES ↔ 記事ページ（2026-10-30 に追加）
    #
    # カードと description は上で見ているが、トップの記事一覧（ARTICLES）は
    # どの検査も見ていなかった。そのため ARTICLES だけが古いまま残り、
    # 扉の向きの記事では「置き換えられる前の記事の見出しと説明文」が
    # そのまま出ていた（日付も2か月ずれていた）。同じものが他に5本あった。
    # 記事ページを正とする。直すのは tools/retitle-article.py の --sync。
    ip = os.path.join(ROOT, "index.html")
    if os.path.exists(ip):
        src = io.open(ip, encoding="utf-8").read()
        i = src.find("const ARTICLES")
        if i >= 0:
            blk = src[i:src.index("];", i)]
            # 同じURLが2回入っていないか。2026-10-30 に1件見つかった
            # （publish-article.py が古い行を消し損ねていた）
            urls = re.findall(r"url:'articles/([^']+)\.html'", blk)
            for slug in sorted({u for u in urls if urls.count(u) > 1}):
                bad.append(("index.html", "ARTICLES に同じ記事が %d 回入っています: %s"
                            % (urls.count(slug), slug)))
            for date, _tag, title, lead, slug in re.findall(
                    r"\{ date:'([^']*)', tag:'([^']*)',\s*title:'([^']*)',\s*"
                    r"lead:'([^']*)',\s*url:'articles/([^']+)\.html' \}", blk, re.S):
                ap = os.path.join(ROOT, "articles", slug + ".html")
                if not os.path.exists(ap):
                    bad.append(("index.html", "ARTICLES にあるが記事が無い: " + slug))
                    continue
                a = io.open(ap, encoding="utf-8").read()
                m = re.search(r"<title>(.*?)</title>", a, re.S)
                # 見出し自体に ｜ が入るものがあるので、最後の ｜ で切る
                ptitle = m.group(1).rsplit("｜", 1)[0].strip() if m else ""
                pdesc = txt(a, r'<meta name="description" content="(.*?)"')
                m = re.search(r'<time datetime="([^"]*)"', a)
                pdate = m.group(1) if m else ""
                if pdate and pdate != date:
                    bad.append(("index.html", "ARTICLES の日付が記事と違う: %s（一覧 %s／記事 %s）"
                                % (slug, date, pdate)))
                if ptitle and ptitle != title:
                    bad.append(("index.html", "ARTICLES の見出しが記事と違う: %s\n        一覧 : %s\n        記事 : %s"
                                % (slug, title[:60], ptitle[:60])))
                if pdesc and not pdesc.startswith(lead[:18]):
                    bad.append(("index.html", "ARTICLES の説明文が記事と違う: %s\n        一覧 : %s\n        記事 : %s"
                                % (slug, lead[:60], pdesc[:60])))

    if bad:
        print("[中止] ページの見出し情報に問題があります。")
        for rel, msg in bad:
            print("   %-42s %s" % (rel, msg))
        return 1
    print("[見出し情報の検査] %d ページ／記事カードの食い違いなし" % len(rels))
    return 0


if __name__ == "__main__":
    sys.exit(main())
