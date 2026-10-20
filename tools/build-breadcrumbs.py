#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""画面に出ているパンくずから、BreadcrumbList の構造化データを作って入れる。

Search Console のパンくずリストのレポートは「有効16・無効0」だったが、
記事28ページのうちマークアップがあるのは5ページだけだった（取り下げページのみ）。
記事はクリックの65%を生んでいるページ群なので、ここが抜けているのはもったいない。

原因は tools/publish-article.py が Article しか出していなかったこと。
製品ページやサイズ帯は _common_page.shell() 経由なので入っている。

・画面に出ている <nav class="crumbs"> をそのまま構造化データにする
  （表示と構造化データが食い違うと、Googleの要件から外れるため）
・すでに BreadcrumbList があるページには手を出さない
・何度実行しても同じ結果になる

publish.sh から自動で呼ばれる。
"""
import glob, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = "https://monooki-erabi.com/"
BEG, END = "<!-- AUTO_CRUMB_LD_START -->", "<!-- AUTO_CRUMB_LD_END -->"


def unesc(t):
    return (t.replace("&amp;", "&").replace("&lt;", "<")
             .replace("&gt;", ">").replace("&quot;", '"'))


def items(nav_html, page_url):
    """<nav class="crumbs"> の中身を [(名前, URL または None)] にほどく"""
    out = []
    for m in re.finditer(r'<a href="([^"]+)">(.*?)</a>|<span>/</span>|([^<>]+)', nav_html, re.S):
        href, label, plain = m.group(1), m.group(2), m.group(3)
        if href is not None:
            name = unesc(re.sub(r"<[^>]+>", "", label)).strip()
            if name:
                out.append((name, href))
        elif plain:
            name = unesc(plain).strip()
            if name and name != "/":
                out.append((name, None))
    return out


def abs_url(href, page_rel):
    if href.startswith("http"):
        return href
    base = os.path.dirname(page_rel)
    p = os.path.normpath(os.path.join(base, href)).replace(os.sep, "/")
    if p == ".":
        p = ""
    if href.endswith("/") and p and not p.endswith("/"):
        p += "/"
    return SITE + ("" if p in ("", "/") else p)


def main():
    pages = sorted(set(glob.glob(os.path.join(ROOT, "*.html"))
                       + glob.glob(os.path.join(ROOT, "*", "*.html"))))
    added, skipped = 0, 0
    for p in pages:
        s = io.open(p, encoding="utf-8").read()
        orig = s
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        s = re.sub(re.escape(BEG) + r".*?" + re.escape(END) + r"\n?", "", s, flags=re.S)
        nav = re.search(r'<nav class="crumbs"[^>]*>(.*?)</nav>', s, re.S)
        if not nav:
            if s != orig:
                io.open(p, "w", encoding="utf-8").write(s)
            continue
        if "BreadcrumbList" in s:
            skipped += 1
            if s != orig:
                io.open(p, "w", encoding="utf-8").write(s)
            continue
        got = items(nav.group(1), rel)
        if len(got) < 2:
            continue
        lst = []
        for i, (name, href) in enumerate(got, 1):
            e = {"@type": "ListItem", "position": i, "name": name}
            if href:
                e["item"] = abs_url(href, rel)
            lst.append(e)
        ld = {"@context": "https://schema.org", "@type": "BreadcrumbList",
              "itemListElement": lst}
        blk = (BEG + '\n<script type="application/ld+json">\n'
               + json.dumps(ld, ensure_ascii=False, indent=2)
               + "\n</script>\n" + END + "\n")
        i = s.find("</head>")
        if i < 0:
            print("  飛ばす（</head> が無い）:", rel); continue
        s = s[:i] + blk + s[i:]
        added += 1
        io.open(p, "w", encoding="utf-8").write(s)
    have = sum(1 for p in pages if "BreadcrumbList" in io.open(p, encoding="utf-8").read())
    print("[パンくずの構造化データ] 新しく %d ページに追加（既にあった %d ページ／合計 %d ページ）"
          % (added, skipped, have))
    return 0


if __name__ == "__main__":
    sys.exit(main())
