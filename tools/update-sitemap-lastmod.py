#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sitemap.xml の <lastmod> を自動更新し、あわせて sitemap.txt を書き出す。

publish.sh から自動で呼ばれるので、手で触る必要はない。
・<loc> のURLをローカルのファイルに対応させ、そのファイルの更新日を入れる
・ファイルが存在しないURLは書き換えず、警告として名前を出す（404の作り込みを防ぐ）
・sitemap.txt（1行1URLのテキスト形式サイトマップ）も同時に生成する
  GitHub Pages は .xml を text/html として配信してしまう既知の不具合があり、
  Google Search Console が sitemap.xml を取得できない。.txt なら正しく配信される。
  sitemap.xml も Bing 等のために残す。
"""
import os, re, sys, datetime

BASE    = "https://monooki-erabi.com/"
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP = os.path.join(ROOT, "sitemap.xml")

def local_path(loc):
    rel = loc[len(BASE):] if loc.startswith(BASE) else loc.lstrip("/")
    if rel == "" or rel.endswith("/"):
        rel += "index.html"
    return os.path.join(ROOT, rel)

if not os.path.exists(SITEMAP):
    print("[sitemap] sitemap.xml が見つかりません"); sys.exit(0)

s = open(SITEMAP, encoding="utf-8").read()
orig = s
missing, updated = [], 0

def repl(m):
    global updated
    loc = m.group(1).strip()
    p = local_path(loc)
    if not os.path.exists(p):
        missing.append(loc)
        return m.group(0)
    d = datetime.date.fromtimestamp(os.path.getmtime(p)).isoformat()
    updated += 1
    return "<loc>%s</loc>\n    <lastmod>%s</lastmod>\n    " % (loc, d)

s = re.sub(r"<loc>(.*?)</loc>\s*(?:<lastmod>.*?</lastmod>\s*)?", repl, s, flags=re.S)

if s != orig:
    open(SITEMAP, "w", encoding="utf-8").write(s)
    print("[sitemap] lastmod を更新しました（%d URL）" % updated)
else:
    print("[sitemap] lastmod に変更はありません（%d URL）" % updated)

# ── テキスト形式サイトマップ（1行1URL・URL以外は書かない）──
locs = re.findall(r"<loc>(.*?)</loc>", s, flags=re.S)
locs = [x.strip() for x in locs]
txt = os.path.join(ROOT, "sitemap.txt")
body = "\n".join(locs) + "\n"
before = open(txt, encoding="utf-8").read() if os.path.exists(txt) else None
if before != body:
    open(txt, "w", encoding="utf-8").write(body)
    print("[sitemap] sitemap.txt を書き出しました（%d URL）" % len(locs))
else:
    print("[sitemap] sitemap.txt に変更はありません（%d URL）" % len(locs))

if missing:
    print("[sitemap][注意] 次のURLは、対応するファイルがローカルにありません。")
    print("                サイトマップに書いてあるのに404になります。")
    for u in missing:
        print("                " + u)
