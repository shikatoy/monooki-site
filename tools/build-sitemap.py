#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sitemap.xml / sitemap.txt を、実際に存在するファイルから作り直す。

これまで size/ と products/ の追加を手で足していたため、ページを増やしても
sitemap に載らないことがあった（2026-09-17：サイズ帯ページを8本増やしたが
1本も登録されず、size/index.html は最初から抜けていた）。

  lastmod はファイルの更新日。priority は下の RULES で決める。

    python3 tools/build-sitemap.py
"""
import os, io, glob, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = "https://monooki-erabi.com/"

# (対象, priority, changefreq)。上から順に当てはめる
RULES = [
    ("index.html",              "1.0", "weekly"),
    ("articles/index.html",     "0.8", "weekly"),
    ("articles/*.html",         "0.9", "monthly"),
    ("products/index.html",     "0.8", "weekly"),
    ("products/codes.html",     "0.8", "monthly"),
    ("products/*.html",         "0.7", "monthly"),
    ("size/index.html",         "0.8", "weekly"),
    ("size/*.html",             "0.8", "monthly"),
    ("about.html",              "0.3", "yearly"),
    ("contact.html",            "0.3", "yearly"),
    ("privacy.html",            "0.3", "yearly"),
]

SKIP = {"404.html"}


def main():
    seen, rows = set(), []
    for pat, pri, freq in RULES:
        for p in sorted(glob.glob(os.path.join(ROOT, pat))):
            rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
            if rel in seen or os.path.basename(rel) in SKIP:
                continue
            seen.add(rel)
            mt = datetime.date.fromtimestamp(os.path.getmtime(p)).isoformat()
            loc = SITE + ("" if rel == "index.html" else rel)
            rows.append((loc, mt, freq, pri))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mt, freq, pri in rows:
        xml += ["  <url>",
                "    <loc>%s</loc>" % loc,
                "    <lastmod>%s</lastmod>" % mt,
                "    <changefreq>%s</changefreq>" % freq,
                "    <priority>%s</priority>" % pri,
                "  </url>"]
    xml.append("</urlset>")
    io.open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(xml) + "\n")
    io.open(os.path.join(ROOT, "sitemap.txt"), "w", encoding="utf-8").write(
        "\n".join(r[0] for r in rows) + "\n")

    import collections
    c = collections.Counter(r[0].replace(SITE, "").split("/")[0] or "(直下)" for r in rows)
    print("[sitemap] %d URL  %s" % (len(rows), dict(c)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
