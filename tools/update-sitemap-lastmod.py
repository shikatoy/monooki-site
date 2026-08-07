#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sitemap.xml の <lastmod> を、各ページのファイル更新日で自動的に書き換える。

publish.sh から自動で呼ばれるので、手で日付を直す必要はない。
・<loc> のURLをローカルのファイルに対応させ、そのファイルの更新日を入れる
・ファイルが存在しないURLは書き換えず、警告として名前を出す（404の作り込みを防ぐ）
"""
import os, re, sys, datetime

BASE    = "https://shikatoy.github.io/monooki-site/"
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

if missing:
    print("[sitemap][注意] 次のURLは、対応するファイルがローカルにありません。")
    print("                サイトマップに書いてあるのに404になります。")
    for u in missing:
        print("                " + u)
