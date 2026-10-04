#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llms.txt の自動生成部分を作り直す。

対象は2か所。
  1. 「## 主なコンテンツ」の中の記事一覧（index.html の ARTICLES から）
  2. 「## ページ」より下すべて（記事・寸法ページ・索引のURL地図）

記事の取り下げを行単位でやると、llms.txt に空行だけが残って
次の公開の差し込み位置が見つからなくなる（2026-09-10 に発生）。
一覧は毎回まるごと作り直す方式にして、その事故を起こらなくする。

寸法ページ（size/）は AI 検索からの流入が実際にある一方で
llms.txt に1本も載っていなかった（2026-10-04 に発覚）。
生成済みの size/*.html と tools/_bands.json から毎回書き出す。
そのため publish.sh では build-size-pages / build-bands より後に呼ぶこと。

    python3 tools/build-llms.py
"""
import glob, io, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 「## ページ」に固定で並べるもの（寸法ページと記事は自動で足す）
STATIC_PAGES = [
    ("トップ（診断・索引・メーカー解説・コラム・更新履歴）", "/"),
    ("製品一覧（製品ごとのページ・型番ごとのサイズ表）", "/products/"),
    ("型番から探す（3社の全型番の索引。見積書やカタログの型番から間口・奥行・高さを引く）",
     "/products/codes.html"),
    ("廃盤・生産終了した機種", "/products/discontinued.html"),
    ("寸法から探す（置ける寸法から絞り込む入口）", "/size/"),
    ("記事一覧", "/articles/"),
]
TAIL_PAGES = [
    ("運営者情報", "/about.html"),
    ("プライバシーポリシー", "/privacy.html"),
    ("お問い合わせ", "/contact.html"),
]


def articles():
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    i = s.index("const ARTICLES")
    blk = s[i:s.index("];", i)]
    out = []
    for m in re.finditer(
            r"\{\s*date:'([^']+)',[^}]*?title:'([^']*)',\s*lead:'([^']*)',\s*url:'articles/([^']+)\.html'",
            blk, re.S):
        out.append(dict(date=m.group(1), title=m.group(2), lead=m.group(3), slug=m.group(4)))
    return out


def _h1_and_rows(path):
    s = io.open(path, encoding="utf-8").read()
    m = re.search(r"(?s)<h1[^>]*>(.*?)</h1>", s)
    h1 = re.sub(r"\s+", " ", re.sub("<[^>]+>", "", m.group(1))).strip() if m else ""
    n = len(re.findall(r"<tr>", re.search(r"(?s)<tbody>(.*?)</tbody>", s).group(1))) \
        if re.search(r"(?s)<tbody>", s) else 0
    return h1, n


def axis_pages():
    """しきい値で絞るページ（band- 以外）。生成済みHTMLから読む。"""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "size", "*.html"))):
        b = os.path.basename(p)
        if b.startswith("band-") or b == "index.html":
            continue
        h1, n = _h1_and_rows(p)
        out.append((h1, "/size/" + b, n))
    return out


def band_pages():
    """サイズ帯ページ。build-bands.py が書き出す _bands.json から読む。"""
    p = os.path.join(HERE, "_bands.json")
    if not os.path.exists(p):
        return []
    return [(b["title"], "/size/%s.html" % b["slug"], b["n"], b["nm"])
            for b in json.load(io.open(p, encoding="utf-8"))]


def main():
    arts = articles()
    axes = axis_pages()
    bands = band_pages()
    p = os.path.join(ROOT, "llms.txt")
    s = io.open(p, encoding="utf-8").read()

    # 1. 「## 主なコンテンツ」の中の記事一覧
    listing = "\n".join(
        "  - 「%s」(/articles/%s.html, %s): %s" % (a["title"], a["slug"], a["date"], a["lead"])
        for a in arts)
    head = "- 記事: 物置の設置と選び方にまつわる読みもの。掲載中の記事は以下のとおり"
    tail = "- コラム:"
    i, j = s.index(head), s.index(tail)
    s = s[:i] + head + "\n" + listing + "\n" + s[j:]

    # 2. 「## ページ」以降をまるごと作り直す
    out = ["## ページ", ""]
    out += ["- %s: %s" % (t, u) for t, u in STATIC_PAGES]
    out += ["- 記事「%s」: /articles/%s.html" % (a["title"], a["slug"]) for a in arts]
    out += ["- %s: %s" % (t, u) for t, u in TAIL_PAGES]

    if axes:
        out += ["", "### 寸法から探す — 間口・奥行・高さのしきい値で絞る", ""]
        out += ["- %s（%d型番）: %s" % (h1, n, u) for h1, u, n in axes]
    if bands:
        out += ["", "### 寸法から探す — 同じサイズ帯で複数メーカーを並べる（間口×奥行を300mm刻みで区切ったもの）", ""]
        out += ["- %s（%dメーカー%d型番）: %s" % (t, nm, n, u) for t, u, n, nm in bands]
    out.append("")

    k = s.index("## ページ")
    s = s[:k] + "\n".join(out)

    io.open(p, "w", encoding="utf-8").write(s)
    print("[llms.txt] 記事 %d 本 / しきい値ページ %d / サイズ帯 %d を書き出しました"
          % (len(arts), len(axes), len(bands)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
