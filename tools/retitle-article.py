#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公開済みの記事の見出しと説明文だけを書き換える。本文は触らない。

なぜ必要か（2026-10-30）
  見出しと説明文は、記事ページの中だけで7か所、ほかに index.html の ARTICLES と
  記事一覧のカードにも入っている。手で直すと必ずどこかが残る。
  publish-article.py で出し直せば全部そろうが、それは本文を md から作り直す。
  図や表を手で足した記事は、作り直すと失われる。
  「本文はそのままで、検索結果に出る文字だけ直したい」ときのための道具。

  実際、扉の向きの記事は index.html の ARTICLES だけが古いままだった。
  日付が 2026-08-23（ページは 2026-09-10）、説明文が
  「小型か中型・大型かの区分で決まります」という、本文と違う内容だった。

    python3 tools/retitle-article.py <slug> --title "…" --description "…"
    python3 tools/retitle-article.py <slug> --check     # 変えずに今の値を出す

直すところ
  articles/<slug>.html … title / meta description / og:title / og:description /
                         JSON-LD の headline と description / h1 / リード文
  index.html           … ARTICLES の title・lead・date
  articles/index.html  … カードの見出しと説明文
llms.txt とサイトマップは publish.sh の生成で付いてくるので触らない。
"""
import argparse
import importlib.util
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_s = importlib.util.spec_from_file_location("pub", os.path.join(HERE, "publish-article.py"))
PUB = importlib.util.module_from_spec(_s)
_s.loader.exec_module(PUB)


def one(s, pat, rep, label, path):
    n = len(re.findall(pat, s, flags=re.S))
    if n != 1:
        raise SystemExit("[中止] %s の「%s」が %d 件です。直せません。" % (path, label, n))
    return re.sub(pat, lambda _m: rep, s, count=1, flags=re.S)


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, s):
    io.open(p, "w", encoding="utf-8").write(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--title")
    ap.add_argument("--description")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--sync", action="store_true",
                    help="記事ページを正として、ARTICLES とカードをそろえる")
    a = ap.parse_args()

    art = os.path.join(ROOT, "articles", a.slug + ".html")
    if not os.path.exists(art):
        raise SystemExit("[中止] 記事がありません: articles/%s.html" % a.slug)
    s = read(art)

    # <title> は「見出し｜サイト名」。見出し自体に｜が入るものがあるので、
    # 最初の｜で切ってはいけない（2026-10-30 に点検スクリプトでこれを間違えた）
    cur_title = re.search(r"<title>(.*?)</title>", s, re.S)
    if cur_title:
        cur_title = re.match("(.*)", cur_title.group(1).rsplit("｜", 1)[0].strip())
    cur_desc = re.search(r'<meta name="description" content="(.*?)">', s, re.S)
    cur_date = re.search(r'<time datetime="([^"]*)"', s)
    print("いまの見出し : %s" % (cur_title.group(1) if cur_title else "（読めません）"))
    print("いまの説明文 : %s" % (cur_desc.group(1) if cur_desc else "（読めません）"))
    print("ページの日付 : %s" % (cur_date.group(1) if cur_date else "（読めません）"))

    idx = read(os.path.join(ROOT, "index.html"))
    ent = re.search(r"\{ date:'([^']*)', tag:'([^']*)',\s*title:'([^']*)',\s*lead:'([^']*)',\s*"
                    r"url:'articles/%s\.html' \}" % re.escape(a.slug), idx, re.S)
    if not ent:
        raise SystemExit("[中止] index.html の ARTICLES に %s がありません。" % a.slug)
    print("一覧の日付   : %s" % ent.group(1))
    print("一覧の見出し : %s" % ent.group(3))
    print("一覧の説明文 : %s" % ent.group(4))

    if a.check:
        return 0

    if a.sync:
        # 記事ページを正として、ARTICLES とカードをそろえる。記事ページは触らない。
        # 2026-10-30、ARTICLES だけが古い記事が5本見つかった。中には、置き換えられた
        # 前の記事の見出しと説明文がそのまま残っているものもあった。
        if a.title or a.description:
            raise SystemExit("[中止] --sync のときは --title / --description を渡さないでください。")
        if not cur_title or not cur_desc:
            raise SystemExit("[中止] 記事ページから見出しか説明文を読めませんでした。")
        a.title, a.description = cur_title.group(1), cur_desc.group(1)
        if ("'" in a.title) or ("'" in a.description):
            raise SystemExit("[中止] 記事ページの見出しか説明文に半角のアポストロフィが入っています。"
                             "index.html の中で文字列を囲っているため、そのままでは入れられません。")
        print("\n  （--sync）記事ページの値で ARTICLES とカードをそろえます。")

    if not a.title or not a.description:
        raise SystemExit("[中止] --title と --description の両方を渡してください。")
    if "'" in a.title or "'" in a.description:
        raise SystemExit("[中止] 見出しと説明文に半角のアポストロフィは使えません"
                         "（index.html の中で文字列を囲っているため）。")

    title, desc = a.title, a.description
    date = cur_date.group(1) if cur_date else ent.group(1)

    # 1. 記事ページ（--sync のときは正なので触らない）
    if a.sync:
        print("  飛ばす: articles/%s.html （--sync では触りません）" % a.slug)
    else:
        s = one(s, r"<title>.*?</title>",
                "<title>%s｜%s</title>" % (PUB.esc(title), PUB.NAME), "title", art)
        s = one(s, r'<meta name="description" content=".*?">',
                '<meta name="description" content="%s">' % PUB.esc_attr(desc), "description", art)
        s = one(s, r'<meta property="og:title" content=".*?">',
                '<meta property="og:title" content="%s">' % PUB.esc_attr(title), "og:title", art)
        s = one(s, r'<meta property="og:description" content=".*?">',
                '<meta property="og:description" content="%s">' % PUB.esc_attr(desc),
                "og:description", art)
        s = one(s, r'"headline": ".*?",', '"headline": "%s",' % PUB.esc_attr(title),
                "JSON-LD の headline", art)
        s = one(s, r'"description": ".*?",', '"description": "%s",' % PUB.esc_attr(desc),
                "JSON-LD の description", art)
        # 見出しは素の文字で置く。文節の区切り（.pb）は build-headline-breaks.py が付け直す
        s = one(s, r'<h1 class="article-title">.*?</h1>',
                '<h1 class="article-title">%s</h1>' % PUB.esc(title), "h1", art)
        s = one(s, r'<p class="article-lead">.*?</p>',
                '<p class="article-lead">%s</p>' % PUB.esc(desc), "リード文", art)
        write(art, s)
        print("\n  更新: articles/%s.html （8か所）" % a.slug)

    # 2. index.html の ARTICLES
    lead = PUB.short_lead(desc)
    new_ent = ("{ date:'%s', tag:'%s',\n    title:'%s',\n    lead:'%s',\n"
               "    url:'articles/%s.html' }" % (date, ent.group(2), title, lead, a.slug))
    idx = idx[:ent.start()] + new_ent + idx[ent.end():]
    write(os.path.join(ROOT, "index.html"), idx)
    print("  更新: index.html （ARTICLES の日付・見出し・説明文）")

    # 3. 記事一覧のカード
    p = os.path.join(ROOT, "articles", "index.html")
    c = read(p)
    m = re.search(r'<li class="card">\s*<a class="card-inner" href="%s\.html">.*?</li>'
                  % re.escape(a.slug), c, re.S)
    if not m:
        raise SystemExit("[中止] articles/index.html にカードがありません: %s" % a.slug)
    card = m.group(0)
    card = one(card, r'<h2 class="card-title">.*?</h2>',
               '<h2 class="card-title">%s</h2>' % PUB.esc(title), "カードの見出し", p)
    card = one(card, r'<p class="card-desc">.*?</p>',
               '<p class="card-desc">%s</p>' % PUB.esc(desc), "カードの説明文", p)
    write(p, c[:m.start()] + card + c[m.end():])
    print("  更新: articles/index.html （カードの見出しと説明文）")

    print("\n[完了] このあと publish.sh を流してください。"
          "見出しの折り返しと llms.txt は、そこで付き直します。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
