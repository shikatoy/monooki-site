#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
記事の本文に出てくるシリーズ名・型番を、その製品ページへつなぐ。

記事末尾の導線（build-article-links.py）と記事どうしのリンク（build-crosslinks.py）はあるが、
本文中でシリーズ名や型番に触れても、そこから製品ページへ行けなかった。
読んだ直後がいちばん動く瞬間なので、本文の最初の1回だけをリンクにする。

・シリーズ名（PRODUCTS の name）と型番（sizes の code）が対象。行き先は製品ページ
・<p> と <li> の中だけ。すでにリンクがある段落、見出し、表には手を出さない
・同じ行き先は1記事に1回まで／1記事あたり最大4本
・長い語から先に見る（「フォルタ大型」を「フォルタ」より先に拾う）
・何度実行しても同じ結果になる（前回付けたリンクを外してから付け直す）
"""
import os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _common_page import load_products                      # noqa: E402

ART = os.path.join(ROOT, "articles")
CSSBEG, CSSEND = "/* AUTO_PLINK_CSS_START */", "/* AUTO_PLINK_CSS_END */"
MAX_PER_PAGE = 4

CSS = CSSBEG + """
  /* ───── 本文から製品ページへのリンク（tools/build-product-mentions.py が生成） ───── */
  .p-link { border-bottom: 1px solid var(--linesoft); text-decoration: none; }
  .p-link:hover { color: var(--rust); border-bottom-color: currentColor; }
""" + CSSEND + "\n"


def build_terms():
    """(語, 行き先URL) の一覧。長い順に並べる"""
    terms = []
    for p in load_products():
        page = p.get("page")
        if not page:
            continue
        url = "../" + page                      # articles/ から見た相対パス
        terms.append((p["name"], url))
        for row in p.get("sizes", []):
            code = row[0]
            if len(code) >= 5:                  # 短すぎる記号は拾わない
                terms.append((code, url))
    # 重複する語は先に出たほうを残す
    seen, out = set(), []
    for w, u in sorted(terms, key=lambda x: -len(x[0])):
        if w in seen:
            continue
        seen.add(w)
        out.append((w, u))
    return out


def strip_old(s):
    # 入れ子になっていた時代のものも剥がせるよう、変わらなくなるまで繰り返す
    while True:
        t = re.sub(r'<a class="p-link" href="[^"]*">([^<]*)</a>', r"\1", s)
        if t == s:
            break
        s = t
    s = re.sub(re.escape(CSSBEG) + r".*?" + re.escape(CSSEND) + r"\n?", "", s, flags=re.S)
    return s


def link_body(body, terms, longer):
    """本文に出てくる順にリンクする。同じ位置なら長い語を優先する"""
    used, count = set(), [0]

    def pick(inner):
        best = None
        for word, url in terms:
            if url in used:
                continue
            for cand in [x.start() for x in re.finditer(re.escape(word), inner)]:
                before = inner[:cand]
                if before.count("<a ") > before.count("</a>"):
                    continue                     # すでにリンクの中
                nxt = inner[cand + len(word):cand + len(word) + 1]
                if nxt and (nxt.isalnum() or nxt == "-"):
                    continue                     # 型番の途中で切らない
                if any(inner.startswith(t, cand) for t in longer.get(word, ())):
                    continue                     # 長い製品名の一部
                if best is None or (cand, -len(word)) < (best[0], -len(best[1])):
                    best = (cand, word, url)
                break
        return best

    def do_block(m):
        tag, inner = m.group(1), m.group(2)
        if "<a " in inner:
            return m.group(0)
        while count[0] < MAX_PER_PAGE:
            got = pick(inner)
            if not got:
                break
            i, word, url = got
            inner = (inner[:i] + '<a class="p-link" href="%s">%s</a>' % (url, word)
                     + inner[i + len(word):])
            used.add(url)
            count[0] += 1
        return "<%s>%s</%s>" % (tag, inner, tag)

    return re.sub(r"<(p|li)>(.*?)</\1>", do_block, body, flags=re.S), count[0], used


def main():
    terms = build_terms()
    if not terms:
        print("[中止] 製品データが読めませんでした")
        return 1
    # 「フォルタ」→「フォルタ ウィズ」のように、長いほうの一部になる語を控えておく
    words = [w for w, _ in terms]
    longer = {w: tuple(t for t in words if t != w and t.startswith(w)) for w in words}
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
            print("  飛ばす（本文が見つからない）:", slug)
            continue
        body = m.group(2)
        cut = body.find("<!-- AUTO_")
        head, tail = (body[:cut], body[cut:]) if cut > 0 else (body, "")
        head, n, used = link_body(head, terms, longer)
        if n:
            s = s[:m.start()] + m.group(1) + head + tail + m.group(3) + s[m.end():]
            if "</style>" in s:
                s = s.replace("</style>", CSS + "</style>", 1)
        if s != orig:
            open(f, "w", encoding="utf-8").write(s)
        total += n
        if n:
            print("  %-42s %d 本" % (slug[:40], n))
    print("[本文から製品ページへのリンク] 合計 %d 本" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
