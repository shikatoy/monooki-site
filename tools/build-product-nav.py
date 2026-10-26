#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
製品ページ下部のナビ（nav-links）を、その製品の正しい値に書き直す。

なぜ必要か（2026-10-26）
  新しい製品ページは tools/_product_template.html を丸ごと複製して作っている
  （build-product-head.py）。ひな形はイナバ 宅配ボックスのページから起こした
  もので、ナビの中に

      <a href="../#c=i-tbj">この製品を比較に追加 →</a>
      <a href="https://www.inaba-ss.co.jp/monooki/lineup/tbj/">メーカー公式 ↗</a>

  が直書きされていた。複製したページはこの2行をそのまま引き継ぐ。その結果、
  13枚が別の製品を指していた。タクボ Mr.シャッターマンのページで
  「メーカー公式」を押すとイナバの宅配ボックスに飛ぶ状態だった。

  このツールは publish のたびに全ページのナビを上書きする。ひな形を複製しても
  取り違えは残らない。

直すもの
  ・../#c=<製品ID>        … そのページの製品IDにそろえる
  ・メーカー公式 ↗ の飛び先 … tools/_official.json の値にそろえる
                             値が null のときは、その行ごと消す
                             行が無くて値があるときは、比較リンクの後ろに足す

ほかの場所は触らない。
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, "index.html")
OFFICIAL = os.path.join(HERE, "_official.json")

NAV_RE = re.compile(r'<nav class="nav-links">(.*?)</nav>', re.S)
CMP_RE = re.compile(r'(<a href="\.\./#c=)([a-z0-9-]+)(")')
OFF_RE = re.compile(r'[ \t]*<a href="[^"]*"[^>]*>\s*メーカー公式[^<]*</a>\n?')
CMP_LINE_RE = re.compile(r'([ \t]*<a href="\.\./#c=[a-z0-9-]+"[^>]*>[^<]*</a>\n?)')


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def product_pages(src):
    i = src.find("const PRODUCT_PAGES")
    if i < 0:
        return []
    j = src.find("};", i)
    return re.findall(r"'([a-z0-9-]+)':\s*'([^']+)'", src[i:j])


def official_anchor(url):
    return ('      <a href="%s" target="_blank" rel="noopener noreferrer">'
            'メーカー公式 ↗</a>\n' % url)


def main():
    src = read(INDEX)
    pages = product_pages(src)
    if not pages:
        print("[中止] index.html から PRODUCT_PAGES を読めませんでした。")
        return 1

    with io.open(OFFICIAL, encoding="utf-8") as f:
        table = json.load(f)
    table.pop("_meta", None)

    missing = [pid for pid, _ in pages if pid not in table]
    if missing:
        print("[中止] tools/_official.json に無い製品IDがあります: %s" % ", ".join(missing))
        print("       公式のラインナップ一覧でURLを確かめてから足してください。")
        return 1

    fixed_cmp = []
    fixed_off = []
    added_off = []
    removed_off = []
    problems = []

    for pid, rel in pages:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            problems.append("%s: ファイルがありません（%s）" % (pid, rel))
            continue

        html = read(path)
        m = NAV_RE.search(html)
        if not m:
            problems.append("%s: nav-links が見つかりません（%s）" % (pid, rel))
            continue

        nav = m.group(1)
        before = nav
        url = table[pid]

        # 1. 比較に追加のID
        cm = CMP_RE.search(nav)
        if not cm:
            problems.append("%s: 「比較に追加」のリンクが見つかりません" % pid)
            continue
        if cm.group(2) != pid:
            fixed_cmp.append("%s（%s → %s）" % (rel, cm.group(2), pid))
            nav = CMP_RE.sub(lambda x: x.group(1) + pid + x.group(3), nav, count=1)

        # 2. メーカー公式
        om = OFF_RE.search(nav)
        if url is None:
            if om:
                removed_off.append(rel)
                nav = OFF_RE.sub("", nav, count=1)
        elif om:
            cur = re.search(r'href="([^"]*)"', om.group(0)).group(1)
            if cur != url:
                fixed_off.append("%s（%s → %s）" % (rel, cur, url))
                nav = OFF_RE.sub(official_anchor(url), nav, count=1)
        else:
            lm = CMP_LINE_RE.search(nav)
            if not lm:
                problems.append("%s: 公式リンクを足す位置が決まりません" % pid)
                continue
            added_off.append("%s（%s）" % (rel, url))
            nav = nav[:lm.end()] + official_anchor(url) + nav[lm.end():]

        if nav != before:
            html = html[:m.start(1)] + nav + html[m.end(1):]
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(html)

    if problems:
        print("[中止] 製品ページのナビを直せませんでした。")
        for p in problems:
            print("       " + p)
        return 1

    total = len(fixed_cmp) + len(fixed_off) + len(added_off) + len(removed_off)
    if total == 0:
        print("製品ページのナビ: %d枚、直すところはありません。" % len(pages))
        return 0

    print("製品ページのナビを直しました（%d枚中 %d件）。" % (len(pages), total))
    for label, rows in (("比較に追加のID", fixed_cmp),
                        ("メーカー公式の飛び先", fixed_off),
                        ("メーカー公式を追加", added_off),
                        ("メーカー公式を削除", removed_off)):
        for r in rows:
            print("  [%s] %s" % (label, r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
