#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自動生成のCSSブロックを、決めた順に並べ直す。

なぜ要るか（2026-10-31）。

CSSを足す生成器が8本ある。どれも `s.replace("</style>", CSS + "</style>", 1)` で、
自分のブロックを剥がして </style> の直前に入れ直す。つまり**最後に走った生成器の
ブロックが一番下に来る**。publish.sh は決まった順に全部走らせるので揃うが、
生成器を1本だけ手で走らせると、そのブロックだけ下に移動する。

実害が出た。2026-10-31、build-product-mentions.py を1本だけ走らせたところ、
記事16本に差分が出た。中身は1文字も変わっておらず、CSSブロックが40行下に
動いただけだった。そのせいで git status を読み違えて、直したばかりの記事が
取り消されたと一瞬思った。差分が本物かどうか見分けられなくなる、という害。

ここで並べ直しておけば、どの生成器を走らせたあとでも同じ並びに戻る。

使い方:
    python3 tools/tidy-css-order.py            並べ直す
    python3 tools/tidy-css-order.py --check    並びが崩れていたら 1 を返す（直さない）

ブロックを足す生成器を作ったら、ORDER にも足すこと。
ORDER に無いブロックが見つかったら中止する（黙って置き去りにしない）。
"""
import io, os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 並べる順。publish.sh が生成器を走らせる順に合わせている。
# 名前だけ置いた行（ARTREL）は、印の次の行から、次のコメント行までをひとまとめに見る。
ORDER = [
    ("AUTO_DOORFIG_CSS",  "pair"),    # build-door-figure.py
    ("AUTO_PEINTE_CSS",   "pair"),    # build-peinte-patterns.py
    ("AUTO_SHOP_CSS",     "pair"),    # build-shop-links.py
    ("AUTO_PLINK_CSS",    "pair"),    # build-product-mentions.py
    ("AUTO_XLINK_CSS",    "pair"),    # build-crosslinks.py
    ("AUTO_RELATED_CSS",  "pair"),    # build-article-links.py
    ("AUTO_ARTREL_CSS",   "lone"),    # build-article-related.py
    ("TABLESCROLL",       "pair"),    # build-table-scroll.py
]
KNOWN = {n for n, _ in ORDER}

# 自動生成のCSSブロックらしきものを見つける網。ORDER の取りこぼしを見つけるために使う。
ANY = re.compile(r"/\* (AUTO_[A-Z0-9_]*CSS|TABLESCROLL)(_START|_END)? \*/")


def pat(name, kind):
    if kind == "pair":
        return re.compile(r"/\* %s_START \*/.*?/\* %s_END \*/\n?" % (name, name), re.S)
    # 印の行＋次のコメント行か </style> までの行
    return re.compile(r"/\* %s \*/\n(?:(?![ \t]*/\*)(?![ \t]*</style>)[^\n]*\n)*" % name)


def tidy(s, rel):
    """(新しい中身, 直すところがあったか) を返す。異常は例外。"""
    m = re.search(r"<style>(.*?)</style>", s, re.S)
    if not m:
        return s, False
    css = m.group(1)

    # ORDER に無いブロックが混ざっていないか
    for g in ANY.finditer(css):
        if g.group(1) not in KNOWN:
            raise ValueError("%s: 並び順の表に無いブロック %s" % (rel, g.group(1)))

    blocks, rest = [], css
    for name, kind in ORDER:
        p = pat(name, kind)
        hits = [g.group(0) for g in p.finditer(rest)]
        if len(hits) > 1:
            raise ValueError("%s: %s が %d 個あります" % (rel, name, len(hits)))
        if hits:
            blocks.append(hits[0].rstrip("\n") + "\n")
            rest = p.sub("", rest, count=1)
    if not blocks:
        return s, False

    new_css = rest.rstrip("\n") + "\n" + "".join(blocks)
    if new_css == css:
        return s, False
    return s[:m.start(1)] + new_css + s[m.end(1):], True


def main():
    check = "--check" in sys.argv
    pages = sorted(set(glob.glob(os.path.join(ROOT, "*.html"))
                       + glob.glob(os.path.join(ROOT, "*", "*.html"))))
    moved, bad = [], []
    for p in pages:
        rel = os.path.relpath(p, ROOT)
        s = io.open(p, encoding="utf-8").read()
        try:
            new, changed = tidy(s, rel)
        except ValueError as e:
            bad.append(str(e))
            continue
        if changed:
            moved.append(rel)
            if not check:
                io.open(p, "w", encoding="utf-8").write(new)

    for b in bad:
        print("[中止]", b)
    if bad:
        return 1
    if check:
        if moved:
            print("[CSSの並び] %d ページで崩れています（tools/tidy-css-order.py で直せます）"
                  % len(moved))
            for r in moved[:8]:
                print("   ", r)
            return 1
        print("[CSSの並び] %d ページ／崩れなし" % len(pages))
        return 0
    print("[CSSの並び] %d ページを並べ直しました（全 %d ページ）" % (len(moved), len(pages)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
