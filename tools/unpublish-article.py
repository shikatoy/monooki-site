#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公開済みの記事をサイトから取り下げる。publish-article.py の逆。

公開が6か所に散っているので、手で消すと必ずどこかが残る。
（記事HTML／index.html の ARTICLES／articles/index.html／sitemap.xml／
  sitemap.txt／llms.txt／OG画像／記事どうしのリンクの行き先）

    python3 tools/unpublish-article.py <slug>
    python3 tools/unpublish-article.py <slug> --check   # 消さずに確認だけ

消したファイルは削除せず ../_to_delete/ へ移す。
（この環境では rm が使えない。中身を確認してからボスが手で捨てる）
"""
import os, re, sys, glob, shutil, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TRASH = os.path.join(os.path.dirname(ROOT), "_to_delete")


def strip_articles_entry(s, slug):
    """ARTICLES 配列から該当スラッグの1件を落とす。

    2026-09-10：ここを正規表現で切っていたところ、1件消すつもりで
    手前の4件まで巻き込んで消してしまった。{ } の対応を数えて
    1件ずつに割る方式に変える（正規表現では入れ子を数えられない）。
    """
    i = s.find("const ARTICLES")
    if i < 0:
        return s, 0
    j = s.index("];", i)
    blk = s[i:j]

    ents, depth, start = [], 0, None
    for k, ch in enumerate(blk):
        if ch == "{":
            if depth == 0:
                start = k
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                ents.append(blk[start:k + 1])
                start = None

    keep = [e for e in ents if slug not in e]
    n = len(ents) - len(keep)
    if not n:
        return s, 0
    return s[:i] + "const ARTICLES = [\n  " + ",\n  ".join(keep) + "\n" + s[j:], n


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    check = "--check" in sys.argv
    if not args:
        print("使い方: python3 tools/unpublish-article.py <slug> [--check]")
        return 1
    slug = args[0]
    hits = []

    # 1. 記事HTML と OG画像 → 退避
    for rel in ["articles/%s.html" % slug, "images/og-%s.png" % slug]:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            hits.append(("移動", rel))
            if not check:
                os.makedirs(TRASH, exist_ok=True)
                stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                shutil.move(p, os.path.join(TRASH, "%s_%s" % (stamp, os.path.basename(p))))

    # 2. index.html の ARTICLES
    p = os.path.join(ROOT, "index.html")
    s = open(p, encoding="utf-8").read()
    s2, n = strip_articles_entry(s, slug)
    if n:
        hits.append(("ARTICLES から削除 %d件" % n, "index.html"))
        if not check:
            open(p, "w", encoding="utf-8").write(s2)

    # 3. 一覧・サイトマップ・llms.txt から、その記事を指す行を落とす
    for rel in ["articles/index.html", "sitemap.xml", "sitemap.txt", "llms.txt"]:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        if slug not in s:
            continue
        if rel == "sitemap.xml":
            out = re.sub(r"\s*<url>(?:(?!</url>).)*?" + re.escape(slug) + r"(?:(?!</url>).)*?</url>",
                         "", s, flags=re.S)
        elif rel == "articles/index.html":
            # カード1枚ぶん（<a ...>〜</a>）を落とす
            out = re.sub(r"\s*<a[^>]*" + re.escape(slug) + r"[^>]*>(?:(?!</a>).)*?</a>",
                         "", s, flags=re.S)
        else:
            out = "\n".join(l for l in s.split("\n") if slug not in l)
        hits.append(("行/ブロックを削除", rel))
        if not check:
            open(p, "w", encoding="utf-8").write(out)

    # 4. 記事どうしのリンクの行き先から外す（build-crosslinks.py の MAP）
    p = os.path.join(HERE, "build-crosslinks.py")
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        out = "\n".join(l for l in s.split("\n")
                        if not (l.strip().startswith("(") and '"%s"' % slug in l))
        if out != s:
            hits.append(("MAP から行き先を削除", "tools/build-crosslinks.py"))
            if not check:
                open(p, "w", encoding="utf-8").write(out)

    # 4b. OG画像の見出し表からも外す（build-og-images.py の TITLES）
    p = os.path.join(HERE, "build-og-images.py")
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        out = "\n".join(l for l in s.split("\n") if '"%s":' % slug not in l)
        if out != s:
            hits.append(("TITLES から見出しを削除", "tools/build-og-images.py"))
            if not check:
                open(p, "w", encoding="utf-8").write(out)

    # 5. 他の記事に残っている本文中リンクを、素のテキストに戻す
    for f in sorted(glob.glob(os.path.join(ROOT, "articles", "*.html"))):
        s = open(f, encoding="utf-8").read()
        out = re.sub(r'<a class="x-link" href="%s\.html">([^<]*)</a>' % re.escape(slug), r"\1", s)
        out = re.sub(r'<a href="(?:\.\./)?articles/%s\.html">([^<]*)</a>' % re.escape(slug), r"\1", out)
        if out != s:
            hits.append(("本文中のリンクを解除", os.path.relpath(f, ROOT)))
            if not check:
                open(f, "w", encoding="utf-8").write(out)

    for what, where in hits:
        print("  %-26s %s" % (what, where))
    print("[取り下げ] %s … %d か所%s" % (slug, len(hits), "（確認のみ）" if check else ""))
    if hits and not check:
        print("       退避先: %s" % TRASH)
        print("       このあと publish.sh を流して、残りの自動生成を作り直してください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
