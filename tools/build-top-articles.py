#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""index.html の ARTICLES を、記事一覧ページのカードから作り直す。

なぜ要るか（2026-11-01）。

ARTICLES はトップの記事一覧と、構造化データ（Blog / BlogPosting）の元になっている。
手で足す決まりだったが、publish-article.py の「古い分を消す」正規表現が
隣の記事まで巻き込んで消していた。

    r"\\n?  \\{ date:'[^']*', tag:'[^']*',\\n(?:[^\\n]*\\n)*?[^\\n]*url:'articles/<slug>\\.html' \\},\\n?"

`(?:[^\\n]*\\n)*?` に上限が無いため、目当ての記事が10番目にあると
1番目から10番目までが1つの塊として一致し、まとめて消える。
2026-11-01 時点で、生きている記事22本のうち ARTICLES に残っていたのは5本だった。
トップの「記事をすべて見る（5本）」も、構造化データの BlogPosting 5件も、
どちらも本当の数ではなかった。

誰も気づけなかったのは、check-meta.py が ARTICLES の各行について
「記事があるか・内容が合っているか」しか見ていなかったからである。
「記事はあるが ARTICLES に無い」は見ていなかった。カードについては
両方向を見ていたので、カードは22本すべて残っていた。

そこで、ARTICLES は手で足すものをやめ、カードから作り直すことにした。
カード文は check-meta.py が記事の description と突き合わせているので、
カードを正にすれば鎖がつながる。

・対象は取り下げページ（RETIRED_PAGE）を除いた記事
・並びは日付の新しい順。同じ日付はカードの並びのまま
・導入文は publish-article.py の short_lead と同じ詰め方
"""
import io, os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RETIRED = "<!-- RETIRED_PAGE -->"


def short_lead(desc, limit=120):
    """トップの一覧用に、説明文を最大2文・limit字までに詰める
    （publish-article.py と同じ規則。変えるときは両方）"""
    parts = [x for x in re.split(r"(?<=。)", desc) if x.strip()]
    s = ""
    for p in parts[:2]:
        if len(s) + len(p) > limit and s:
            break
        s += p
    return s or desc[:limit]


def plain(t):
    """タグを落として空白を詰める。見出しの折り返し用 <span class="pb"> を剥がす"""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()


def cards():
    """記事一覧ページのカードから (日付, 分類, 見出し, 説明文, slug) を読む"""
    p = os.path.join(ROOT, "articles", "index.html")
    s = io.open(p, encoding="utf-8").read()
    out = []
    for m in re.finditer(
            r'<li class="card">\s*<a class="card-inner" href="([a-z0-9-]+)\.html">'
            r'(?:(?!</li>).)*?<span class="card-date">(.*?)<span class="card-tag">(.*?)</span>'
            r'(?:(?!</li>).)*?<h2 class="card-title">(.*?)</h2>'
            r'(?:(?!</li>).)*?<p class="card-desc">(.*?)</p>', s, re.S):
        slug, date, tag, title, desc = m.groups()
        out.append((plain(date), plain(tag), plain(title), plain(desc), slug))
    return out


def live_slugs():
    out = set()
    for p in glob.glob(os.path.join(ROOT, "articles", "*.html")):
        if os.path.basename(p) == "index.html":
            continue
        if RETIRED in io.open(p, encoding="utf-8").read():
            continue
        out.add(os.path.basename(p)[:-5])
    return out


def main():
    rows = cards()
    if not rows:
        print("[中止] 記事一覧ページからカードを読めませんでした。")
        return 1
    live = live_slugs()
    got = {r[4] for r in rows}
    missing = sorted(live - got)
    if missing:
        print("[中止] カードが無い記事があります（先に記事一覧ページを直してください）:",
              ", ".join(missing))
        return 1
    extra = sorted(got - live)
    if extra:
        print("[中止] 取り下げ済みか存在しない記事のカードがあります:", ", ".join(extra))
        return 1

    # 日付の新しい順。同じ日付はカードの並びのまま（sorted は安定）
    rows = sorted(rows, key=lambda r: r[0], reverse=True)

    body = ""
    for date, tag, title, desc, slug in rows:
        body += ("\n  { date:'%s', tag:'%s',\n    title:'%s',\n    lead:'%s',\n"
                 "    url:'articles/%s.html' },"
                 % (date, tag.replace("'", "’"), title.replace("'", "’"),
                    short_lead(desc).replace("'", "’"), slug))
    body += "\n"

    p = os.path.join(ROOT, "index.html")
    s = io.open(p, encoding="utf-8").read()
    m = re.search(r"(const ARTICLES = \[)(.*?)(\];)", s, re.S)
    if not m:
        print("[中止] index.html に const ARTICLES が見つかりません。")
        return 1
    before = len(re.findall(r"url:'articles/", m.group(2)))
    new = s[:m.end(1)] + body + s[m.start(3):]
    if new != s:
        io.open(p, "w", encoding="utf-8").write(new)
    print("[トップの記事一覧] %d 本（直前は %d 本）" % (len(rows), before))
    return 0


if __name__ == "__main__":
    sys.exit(main())
