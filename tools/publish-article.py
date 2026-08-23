#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
制作ラインが出した記事（_output の .md）を、サイトの記事ページとして公開する。

  python3 tools/publish-article.py <path-to.md> [--tag 機種の見方]

触る場所が6つあり、手でやると必ずどれかが漏れる：
  1. articles/<slug>.html          （記事ページ本体）
  2. index.html の ARTICLES        （トップの記事一覧）
  3. articles/index.html           （記事一覧ページのカード）
  4. sitemap.xml                   （URL追加）
  5. llms.txt                      （AI検索向けの要約行）
  6. build-article-links.py        （末尾の製品導線。publish.sh が走らせる）

同じ slug で2回流しても重複しない（前の分を消してから入れ直す）。
"""
import os, re, sys, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://monooki-erabi.com/"
NAME = "物置どれがいい？"
TEMPLATE = os.path.join(ROOT, "articles", "monooki-level-blocks.html")
TAGS = ["設置の実務", "選び方", "機種の見方"]


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def esc_attr(t):
    return esc(t).replace('"', "&quot;")


def parse_front(md):
    if not md.startswith("---"):
        raise SystemExit("[中止] front matter がありません")
    end = md.index("\n---", 3)
    head, body = md[3:end], md[end + 4:]
    fm = {}
    for line in head.splitlines():
        m = re.match(r'^(\w+):\s*(.*)$', line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if v.startswith("[") and v.endswith("]"):
            fm[k] = [x.strip().strip('"') for x in v[1:-1].split(",") if x.strip()]
        else:
            fm[k] = v.strip('"')
    return fm, body.strip()


def inline(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return t


def md_to_html(body):
    """記事本文のマークダウンを、このサイトの article-body の書式に変換する"""
    lines = body.split("\n")
    out, buf, lis, h1 = [], [], [], None

    def flush_p():
        if buf:
            out.append("        <p>" + inline(" ".join(buf)).replace("  ", " ") + "</p>")
            buf.clear()

    def flush_li():
        if lis:
            out.append("        <ul>")
            out.extend("        <li>" + inline(x) + "</li>" for x in lis)
            out.append("        </ul>")
            lis.clear()

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("# "):
            flush_p(); flush_li(); h1 = line[2:].strip(); continue
        if line.startswith("## "):
            flush_p(); flush_li()
            out.append(""); out.append("        <h2>" + inline(line[3:].strip()) + "</h2>"); continue
        if line.startswith("### "):
            flush_p(); flush_li()
            out.append(""); out.append("        <h3>" + inline(line[4:].strip()) + "</h3>"); continue
        if line.startswith("> "):
            flush_p(); flush_li()
            out.append('        <p class="note">' + inline(line[2:].strip()) + "</p>"); continue
        if line.startswith("- "):
            flush_p(); lis.append(line[2:].strip()); continue
        if not line.strip():
            flush_p(); flush_li(); continue
        buf.append(line.strip())
    flush_p(); flush_li()
    return h1, "\n".join(out).strip("\n")


def short_lead(desc, limit=120):
    """トップの一覧用に、説明文を最大2文・limit字までに詰める"""
    parts = [x for x in re.split(r"(?<=。)", desc) if x.strip()]
    s = ""
    for p in parts[:2]:
        if len(s) + len(p) > limit and s:
            break
        s += p
    return s or desc[:limit]


def build_page(fm, h1, body_html, tag):
    shell = open(TEMPLATE, encoding="utf-8").read()
    # 前回の生成物（記事末尾の導線）はテンプレ側から取り除く
    shell = re.sub(r"<!-- AUTO_RELATED_START -->.*?<!-- AUTO_RELATED_END -->\s*", "", shell, flags=re.S)
    shell = re.sub(r"/\* AUTO_RELATED_CSS_START \*/.*?/\* AUTO_RELATED_CSS_END \*/\n?", "", shell, flags=re.S)

    slug = fm["slug"]
    url = SITE + "articles/" + slug + ".html"
    title = fm["title"]
    desc = fm["description"]
    kw = ", ".join(fm.get("keywords", []))
    date = fm.get("date", "")
    ogimg = SITE + "images/og-image.png"          # 記事ごとのOG画像はまだ無い
    crumb = fm.get("crumb") or re.sub(r"^.*?[｜|]", "", title).strip() or title

    def one(pat, rep, label):
        nonlocal shell
        n = len(re.findall(pat, shell, flags=re.S))
        if n != 1:
            raise SystemExit("[中止] 差し替え箇所が %d 件: %s" % (n, label))
        shell = re.sub(pat, lambda _m: rep, shell, count=1, flags=re.S)

    one(r"<title>.*?</title>", "<title>%s｜%s</title>" % (esc(title), NAME), "title")
    one(r'<meta name="description" content=".*?">',
        '<meta name="description" content="%s">' % esc_attr(desc), "description")
    one(r'<meta name="keywords" content=".*?">',
        '<meta name="keywords" content="%s">' % esc_attr(kw), "keywords")
    one(r'<link rel="canonical" href=".*?">',
        '<link rel="canonical" href="%s">' % url, "canonical")
    one(r'<meta property="og:title" content=".*?">',
        '<meta property="og:title" content="%s">' % esc_attr(title), "og:title")
    one(r'<meta property="og:description" content=".*?">',
        '<meta property="og:description" content="%s">' % esc_attr(desc), "og:description")
    one(r'<meta property="og:url" content=".*?">',
        '<meta property="og:url" content="%s">' % url, "og:url")
    one(r'<meta property="og:image" content=".*?">',
        '<meta property="og:image" content="%s">' % ogimg, "og:image")

    ld = ('<script type="application/ld+json">\n{\n'
          '  "@context": "https://schema.org",\n  "@type": "Article",\n'
          '  "headline": "%s",\n  "description": "%s",\n'
          '  "datePublished": "%s",\n  "dateModified": "%s",\n'
          '  "author": { "@type": "Organization", "name": "%s" },\n'
          '  "publisher": { "@type": "Organization", "name": "%s" },\n'
          '  "mainEntityOfPage": "%s",\n  "image": "%s",\n'
          '  "inLanguage": "ja",\n  "keywords": "%s"\n}\n</script>'
          % (esc_attr(title), esc_attr(desc), date, date, NAME, NAME, url, ogimg, esc_attr(kw)))
    one(r'<script type="application/ld\+json">.*?</script>', ld, "JSON-LD")

    one(r'(<nav class="crumbs" aria-label="パンくずリスト">\s*<a href="\.\./">トップ</a><span>/</span><a href="\./">記事</a><span>/</span>).*?(\s*</nav>)',
        '<nav class="crumbs" aria-label="パンくずリスト">\n      <a href="../">トップ</a><span>/</span><a href="./">記事</a><span>/</span>%s\n    </nav>' % esc(crumb),
        "パンくず")

    one(r'<p class="article-kicker">.*?</p>',
        '<p class="article-kicker">Article — %s</p>' % esc(tag), "kicker")
    one(r'<h1 class="article-title">.*?</h1>',
        '<h1 class="article-title">%s</h1>' % inline(h1 or title), "h1")
    one(r'<p class="article-lead">.*?</p>',
        '<p class="article-lead">%s</p>' % esc(desc), "lead")
    one(r'<time datetime=".*?">.*?</time>',
        '<time datetime="%s">%s</time>' % (date, date), "date")
    one(r'<div class="tags">.*?</div>',
        '<div class="tags">\n          %s\n        </div>'
        % "\n          ".join('<span class="tag">%s</span>' % esc(k) for k in fm.get("keywords", [])),
        "tags")
    one(r'(<div class="article-body">)\s*.*?(\s*</div>\s*</article>)',
        '<div class="article-body">\n\n%s\n\n      </div>\n    </article>' % body_html,
        "本文")
    return shell


def upsert(path, block, slug, anchor_pat, label):
    """slug の既存分を消してから、anchor の直後に差し込む"""
    s = open(path, encoding="utf-8").read()
    before = s
    s = re.sub(r"\n?[ \t]*<li class=\"card\">\s*<a class=\"card-inner\" href=\"%s\.html\">.*?</li>\n?" % re.escape(slug),
               "\n", s, flags=re.S)
    s = re.sub(r"\n?  \{ date:'[^']*', tag:'[^']*',\n(?:[^\n]*\n)*?[^\n]*url:'articles/%s\.html' \},\n?" % re.escape(slug),
               "\n", s, flags=re.S)
    s = re.sub(r"\n?  <url>\s*<loc>[^<]*articles/%s\.html</loc>.*?</url>\n?" % re.escape(slug),
               "\n", s, flags=re.S)
    s = re.sub(r"\n?  - 「[^」]*」\(/articles/%s\.html[^\n]*\n" % re.escape(slug), "\n", s)
    m = re.search(anchor_pat, s, flags=re.S)
    if not m:
        raise SystemExit("[中止] 差し込み位置が見つかりません: " + label)
    s = s[:m.end()] + block + s[m.end():]
    open(path, "w", encoding="utf-8").write(s)
    print("  更新:", os.path.relpath(path, ROOT), "（%s）" % ("入れ替え" if before != s else "追加"))


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    src = sys.argv[1]
    tag = "選び方"
    if "--tag" in sys.argv:
        tag = sys.argv[sys.argv.index("--tag") + 1]
    crumb = sys.argv[sys.argv.index("--crumb") + 1] if "--crumb" in sys.argv else None
    if tag not in TAGS:
        print("[中止] tag は %s のいずれか" % " / ".join(TAGS)); return 1

    fm, body = parse_front(open(src, encoding="utf-8").read())
    for k in ("title", "description", "slug"):
        if not fm.get(k):
            print("[中止] front matter に %s がありません" % k); return 1
    slug, title, desc, date = fm["slug"], fm["title"], fm["description"], fm.get("date", "")
    if crumb: fm["crumb"] = crumb
    h1, body_html = md_to_html(body)

    # 1. 記事ページ
    out = os.path.join(ROOT, "articles", slug + ".html")
    open(out, "w", encoding="utf-8").write(build_page(fm, h1, body_html, tag))
    print("  作成:", os.path.relpath(out, ROOT))

    # 2. トップの ARTICLES（先頭に差し込む）
    upsert(os.path.join(ROOT, "index.html"),
           "\n  { date:'%s', tag:'%s',\n    title:'%s',\n    lead:'%s',\n    url:'articles/%s.html' },"
           % (date, tag, title.replace("'", "’"), short_lead(desc).replace("'", "’"), slug),
           slug, r"const ARTICLES = \[", "index.html の ARTICLES")

    # 3. 記事一覧ページのカード
    upsert(os.path.join(ROOT, "articles", "index.html"),
           '\n\n      <li class="card">\n        <a class="card-inner" href="%s.html">\n'
           '          <span class="card-date">%s<span class="card-tag">%s</span></span>\n'
           '          <h2 class="card-title">%s</h2>\n'
           '          <p class="card-desc">%s</p>\n'
           '          <span class="card-more">続きを読む <span class="arrow">→</span></span>\n'
           '        </a>\n      </li>' % (slug, date, esc(tag), esc(title), esc(desc)),
           slug, r'<ul class="card-list">', "articles/index.html")

    # 4. sitemap.xml
    upsert(os.path.join(ROOT, "sitemap.xml"),
           "\n  <url>\n    <loc>%sarticles/%s.html</loc>\n    <lastmod>%s</lastmod>\n"
           "    <changefreq>monthly</changefreq>\n    <priority>0.9</priority>\n  </url>"
           % (SITE, slug, date),
           slug, r"<urlset[^>]*>", "sitemap.xml")

    # 5. llms.txt
    upsert(os.path.join(ROOT, "llms.txt"),
           "\n  - 「%s」(/articles/%s.html, %s): %s" % (title, slug, date, desc),
           slug, r"\n(?=  - 「)", "llms.txt")

    print("\n[完了] %s を公開対象に入れました。" % slug)
    print("       このあと publish.sh を流すと、記事末尾の製品導線も自動で付きます。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
