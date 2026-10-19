#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
記事の末尾に「この記事に出てくる物置」への導線を自動で作る。

・製品名は index.html の PRODUCTS から読む（二重管理をしない）
・本文に出てきた製品だけを、本文での初出順に並べる（紹介料で順番は変えない）
・製品名が1つも出てこない記事には、探し方への導線を置く
・何度実行しても同じ結果になる（前回の生成物を消してから作り直す）
"""
import os, re, glob, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _common_page as C                                  # noqa: E402

ROOT = os.path.dirname(HERE)
BEG, END = "<!-- AUTO_RELATED_START -->", "<!-- AUTO_RELATED_END -->"
CSSBEG, CSSEND = "/* AUTO_RELATED_CSS_START */", "/* AUTO_RELATED_CSS_END */"
MAX_ADS = 4          # 広告の出口は1記事4本まで。並べすぎると記事の末尾が広告の壁になる

CSS = CSSBEG + """
  /* ───── 記事末尾の導線（tools/build-article-links.py が生成） ───── */
  .rel { margin: 46px 0 0; border-top: 1px solid var(--line); padding-top: 26px; }
  .rel-label { margin: 0; font-family: 'IBM Plex Mono', monospace; font-size: 11px;
    letter-spacing: .22em; text-transform: uppercase; color: var(--mute); }
  .rel-note { margin: 10px 0 18px; font-size: 12.5px; line-height: 1.9; color: var(--mute); }
  .rel-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
  @media (min-width: 700px) { .rel-list { grid-template-columns: 1fr 1fr; } }
  .rel-list li { margin: 0; padding: 0; }
  .rel-list li::before { content: none; }
  .rel-list a { display: flex; align-items: center; gap: 12px; border: 1px solid var(--linesoft);
    background: #fff; padding: 12px 14px; text-decoration: none;
    transition: border-color .2s ease, box-shadow .2s ease; }
  .rel-list a:hover { border-color: var(--rust); box-shadow: 3px 3px 0 var(--rust); }
  .rel-txt { flex: 1; min-width: 0; }
  .rel-kicker { display: block; font-family: 'IBM Plex Mono', monospace; font-size: 11px;
    letter-spacing: .14em; color: var(--mute); }
  .rel-name { display: block; margin-top: 3px; font-family: 'Shippori Mincho B1', serif;
    font-weight: 700; font-size: 15px; line-height: 1.4; }
  .rel-go { flex: 0 0 auto; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: var(--rust); }
  /* 記事の末尾に置く、販売店への出口（広告）。本文の中には入れない */
  .rel-ad { margin: 22px 0 0; border-top: 1px solid var(--linesoft); padding-top: 16px; }
  .rel-ad-label { margin: 0; font-family: 'IBM Plex Mono', monospace; font-size: 11px;
    letter-spacing: .14em; color: var(--rust); }
  .rel-ad-list { list-style: none; margin: 10px 0 0; padding: 0; display: flex; flex-wrap: wrap; gap: 8px; }
  .rel-ad-list li { margin: 0; padding: 0; }
  .rel-ad-list li::before { content: none; }
  .rel-ad-list a { display: inline-flex; align-items: center; min-height: 24px;
    border: 1px solid var(--rust); color: var(--rust); padding: 6px 12px;
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: .08em;
    text-decoration: none; }
  .rel-ad-list a:hover { background: var(--rust); color: #fff; }
  .rel-ad-note { margin: 12px 0 0; font-size: 12.5px; line-height: 1.9; color: var(--mute); }
""" + CSSEND + "\n"


def load_products(root):
    """index.html の PRODUCTS と PRODUCT_PAGES から、製品の一覧を作る"""
    s = open(os.path.join(root, "index.html"), encoding="utf-8").read()
    makers = dict(re.findall(r"(\w+)\s*:\s*'([^']*?)\s*/\s*[A-Z]+'", s[s.find("const MAKERS"):s.find("const MAKERS") + 400]))
    pages = dict(re.findall(r"'([a-z\-]+)':\s*'(products/[^']+)'", s))
    out = []
    for m in re.finditer(r"id:'([a-z\-]+)',\s*maker:'(\w+)',\s*name:'([^']+)',\s*cat:'([^']+)'", s):
        pid, mk, name, cat = m.groups()
        if pid in pages:
            out.append({"id": pid, "maker": makers.get(mk, mk), "name": name, "cat": cat, "page": pages[pid]})
    return out


def strip_old(s):
    s = re.sub(re.escape(BEG) + r".*?" + re.escape(END) + r"\s*", "", s, flags=re.S)
    s = re.sub(re.escape(CSSBEG) + r".*?" + re.escape(CSSEND) + r"\n?", "", s, flags=re.S)
    return s


def plain_body(s):
    """本文だけを取り出す（script・タグ・自動生成部分を除く）"""
    b = re.sub(r"<script.*?</script>", " ", s, flags=re.S)
    b = re.sub(r"<style.*?</style>", " ", b, flags=re.S)
    b = re.sub(r"<nav.*?</nav>", " ", b, flags=re.S)
    b = re.sub(r"<footer.*?</footer>", " ", b, flags=re.S)
    return re.sub(r"<[^>]+>", " ", b)


def card(href, kicker, name):
    return ('<li><a href="%s"><span class="rel-txt">'
            '<span class="rel-kicker">%s</span>'
            '<span class="rel-name">%s</span></span>'
            '<span class="rel-go">&rarr;</span></a></li>') % (href, kicker, name)


FIND = [
    ("../#shindan", "3〜4問で結果が出ます", "物置マッチング診断"),
    ("../size/", "奥行・高さ・間口で絞り込む", "寸法から探す"),
    ("../products/", "掲載中の全機種", "製品一覧"),
    ("../products/codes.html", "手元の型番から引く", "型番索引"),
]


def ad_block(hits, ex):
    """販売店（広告）への出口。本文には入れず、記事を読み終えた位置にだけ置く。
       並びは本文での初出順で、紹介料では変えない。
       販売店に取り扱いの無いシリーズには出さない（無理にカテゴリ一覧へ逃がさない）"""
    rows = [(p, ex[p["id"]]) for p in hits if p["id"] in ex][:MAX_ADS]
    if not rows:
        return ""
    lis = "\n        ".join(
        '<li><a href="%s" rel="nofollow sponsored" target="_blank">%sの価格・見積もりを見る &rarr;</a></li>'
        % (C.aff_url(code), p["name"]) for p, code in rows)
    return ('      <div class="rel-ad">\n'
            '        <p class="rel-ad-label">広告 — 販売店（エクスショップ）で見る</p>\n'
            '        <ul class="rel-ad-list">\n        %s\n        </ul>\n'
            '        <p class="rel-ad-note">提携リンクです。ここから購入・お見積もりがあった場合に紹介料が'
            '支払われることがあります。並びは本文に出てきた順で、紹介料では変えていません。'
            '販売店に取り扱いの無いシリーズと、%d件を超えたぶんは出していません。'
            '上の一覧から、機種ごとのページへ行けます。</p>\n'
            '      </div>\n') % (lis, MAX_ADS)


def build_block(hits, ex=None):
    ex = ex or {}
    if hits:
        rows = "\n        ".join(card("../" + p["page"], "%s — %s" % (p["maker"], p["cat"]), p["name"]) for p in hits)
        return ('%s\n    <aside class="rel">\n'
                '      <p class="rel-label">Products — この記事に出てくる物置</p>\n'
                '      <p class="rel-note">本文に出てきた順に並べています。サイズ展開と仕様は、機種ごとのページにまとめてあります。</p>\n'
                '      <ul class="rel-list">\n        %s\n      </ul>\n'
                '%s'
                '    </aside>\n    %s\n') % (BEG, rows, ad_block(hits, ex), END)
    rows = "\n        ".join(card(h, k, n) for h, k, n in FIND)
    return ('%s\n    <aside class="rel">\n'
            '      <p class="rel-label">Find — 条件から物置をさがす</p>\n'
            '      <p class="rel-note">この記事には具体的な機種名は出てきません。実際の製品は、次のいずれかから探せます。</p>\n'
            '      <ul class="rel-list">\n        %s\n      </ul>\n'
            '    </aside>\n    %s\n') % (BEG, rows, END)


def main():
    products = load_products(ROOT)
    ex = C.load_exshop()        # 提携先リンクの出典は index.html の EXSHOP だけ
    if len(products) < 5:
        print("[中止] 製品データを読めませんでした（%d件）" % len(products)); return 1
    changed = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "articles", "*.html"))):
        if os.path.basename(f) == "index.html":
            continue
        s = open(f, encoding="utf-8").read()
        orig = s
        s = strip_old(s)
        body = plain_body(s)
        hits = sorted((p for p in products if p["name"] in body), key=lambda p: body.find(p["name"]))
        if "</style>" not in s or "</article>" not in s:
            print("[飛ばす] 構造が想定と違います:", os.path.basename(f)); continue
        s = s.replace("</style>", CSS + "</style>", 1)
        s = s.replace("</article>\n", "</article>\n\n    " + build_block(hits, ex), 1)
        if s != orig:
            open(f, "w", encoding="utf-8").write(s); changed += 1
        print("  %-42s %s" % (os.path.basename(f),
              "／".join(p["name"] for p in hits) if hits else "（機種名なし → 探し方への導線）"))
    print("[記事導線] %d ファイルを更新しました" % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
