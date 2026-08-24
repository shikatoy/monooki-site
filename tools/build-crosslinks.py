#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
記事どうしを本文中でつなぐ。

記事末尾の「製品ページへの導線」は build-article-links.py が作るが、
記事から記事への行き先が無いままだった（10本中1本）。読者が1本読んで帰ってしまう。

・下の MAP に書いた言葉が本文に出てきたら、対応する記事へリンクする
・自分自身にはリンクしない／同じ行き先は1記事に1回まで／1記事あたり最大3本
・見出しの中、すでにリンクがある段落には手を出さない
・何度実行しても同じ結果になる（前回付けたリンクを外してから付け直す）
"""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "articles")
CSSBEG, CSSEND = "/* AUTO_XLINK_CSS_START */", "/* AUTO_XLINK_CSS_END */"
MAX_PER_PAGE = 3
# この語がすぐ後ろに続くときは、複合語の一部なのでリンクしない（例：組み立て説明書）
NG_AFTER = ("説明", "工事", "費用", "方法", "時間", "作業", "手順", "業者")

# 言葉 → 行き先。長い言葉から順に見るので、並びは気にしなくてよい
MAP = [
    ("水平出し", "monooki-level-blocks"),
    ("基礎ブロック", "monooki-level-blocks"),
    ("ブロックの水平", "monooki-level-blocks"),
    ("アンカー工事", "monooki-options-and-anchor"),
    ("転倒防止", "monooki-options-and-anchor"),
    ("アンカー", "monooki-options-and-anchor"),
    ("自分で組み立て", "monooki-diy-assembly"),
    ("組み立てられる", "monooki-diy-assembly"),
    ("整地", "monooki-diy-assembly"),
    ("組みやすさ", "monooki-maker-assembly"),
    ("小型（収納庫）", "kogata-chugata-ogata-chigai"),
    ("小型と中型・大型", "kogata-chugata-ogata-chigai"),
    ("片開き", "monooki-door-opening-side"),
    ("両開き", "monooki-door-opening-side"),
    ("扉の開き方", "monooki-door-opening-side"),
    ("買い替え", "monooki-removal-and-replacement"),
    ("解体", "monooki-removal-and-replacement"),
    ("撤去", "monooki-removal-and-replacement"),
    ("通り道", "monooki-okenai-basho"),
    ("置けない", "monooki-okenai-basho"),
    ("設置場所", "monooki-size-and-placement"),
    ("サイズ選び", "monooki-size-and-placement"),
    ("土台のブロック", "monooki-level-blocks"),
    ("組み立て", "monooki-diy-assembly"),
    ("ホームセンター", "homecenter-monooki-vs-major3"),
    ("OEM", "homecenter-monooki-vs-major3"),
]

CSS = CSSBEG + """
  /* ───── 記事どうしのリンク（tools/build-crosslinks.py が生成） ───── */
  .x-link { border-bottom: 1px dotted var(--rust); text-decoration: none; }
  .x-link:hover { color: var(--rust); border-bottom-style: solid; }
""" + CSSEND + "\n"


def strip_old(s):
    s = re.sub(r'<a class="x-link" href="[^"]*">([^<]*)</a>', r"\1", s)
    s = re.sub(re.escape(CSSBEG) + r".*?" + re.escape(CSSEND) + r"\n?", "", s, flags=re.S)
    return s


def link_body(body, slug):
    """<p> と <li> の中だけを対象に、最初の1回だけリンクにする"""
    used, count = set(), [0]
    pairs = sorted(MAP, key=lambda x: -len(x[0]))

    def do_block(m):
        tag, inner = m.group(1), m.group(2)
        if "<a " in inner:            # すでにリンクがある段落は触らない
            return m.group(0)
        for word, target in pairs:
            if count[0] >= MAX_PER_PAGE:
                break
            if target == slug or target in used:
                continue
            i, ln = -1, len(word)
            for j in [x.start() for x in re.finditer(re.escape(word), inner)]:
                if not inner[j + ln:j + ln + 2].startswith(NG_AFTER):
                    i = j; break
            if i < 0:
                continue
            inner = (inner[:i] + '<a class="x-link" href="%s.html">%s</a>' % (target, word)
                     + inner[i + len(word):])
            used.add(target); count[0] += 1
        return "<%s>%s</%s>" % (tag, inner, tag)

    return re.sub(r"<(p|li)>(.*?)</\1>", do_block, body, flags=re.S), count[0], used


def main():
    total = 0
    for f in sorted(glob.glob(os.path.join(ART, "*.html"))):
        slug = os.path.basename(f)[:-5]
        if slug == "index":
            continue
        s = open(f, encoding="utf-8").read()
        orig = s
        s = strip_old(s)
        m = re.search(r'(<div class="article-body">)(.*?)(</div>\s*</article>)', s, re.S)
        if not m:
            print("  飛ばす（本文が見つからない）:", slug); continue
        # 末尾の自動生成ブロックは対象外にする
        body = m.group(2)
        cut = body.find("<!-- AUTO_")
        head, tail = (body[:cut], body[cut:]) if cut > 0 else (body, "")
        head, n, used = link_body(head, slug)
        if n:
            s = s[:m.start()] + m.group(1) + head + tail + m.group(3) + s[m.end():]
            if "</style>" in s:
                s = s.replace("</style>", CSS + "</style>", 1)
        if s != orig:
            open(f, "w", encoding="utf-8").write(s)
        total += n
        print("  %-40s %d 本  %s" % (slug[:38], n, "／".join(sorted(used))))
    print("[記事どうしのリンク] 合計 %d 本" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
