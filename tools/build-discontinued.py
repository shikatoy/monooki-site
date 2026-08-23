#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""廃盤・生産終了になった物置と、その後継の索引ページを作る。

・掲載するのは、すでにサイト内（更新履歴）で公表済みの事実だけ。ここで新しい事実は作らない
・更新履歴に「廃盤」「入替」が増えたのに下の表に無い場合は、警告として名前を出す
  （自動で本文に入れない。出典と後継の確認は人がやる）
・publish.sh から自動で呼ばれる
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://monooki-erabi.com/"
NAME = "物置どれがいい？"
OUTP = os.path.join(ROOT, "products", "discontinued.html")

# ── 掲載する記録。すべて更新履歴に載っている内容と同じ ──
ITEMS = [
    dict(name="ナイソー 旧SMK型", maker="イナバ", kubun="断熱物置",
         state="2026年8月31日をもって生産終了",
         after="ナイソー SMX（2026年9月1日発売予定）", after_url="inaba-nyso-smx.html",
         src="イナバ（稲葉製作所）公式ニュースリリース（2026年7月6日付）", checked="2026-07-11"),
    dict(name="ヨド蔵MD／ヨド蔵SA（品番DZB）", maker="ヨドコウ", kubun="断熱物置",
         state="2024年3月末の受注をもって生産終了",
         after="未発表（現行ラインアップに後継の断熱物置の掲載なし）", after_url="",
         src="ヨドコウ公式の廃番案内（2024年1月付）", checked="2026-07-09"),
    dict(name="ネクスタ", maker="イナバ", kubun="中型・大型",
         state="フォルタへ全面切替済み",
         after="フォルタ", after_url="inaba-forta.html",
         src="イナバ（稲葉製作所）公式発表（2021年5月）", checked="2026-07-09"),
]


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def load_style():
    s = open(os.path.join(ROOT, "products", "index.html"), encoding="utf-8").read()
    i = s.find("<style"); j = s.find("</style>") + len("</style>")
    return s[i:j]


def check_log():
    """更新履歴に、この表に無い廃盤・入替が増えていないか見る"""
    s = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    i = s.find("const UPDATE_LOG")
    depth = 0; j = s.find("[", i)
    for k in range(j, len(s)):
        if s[k] == "[": depth += 1
        elif s[k] == "]":
            depth -= 1
            if depth == 0:
                end = k + 1; break
    blk = s[j:end]
    known = "".join(x["name"] for x in ITEMS)
    miss = []
    for d, t, title in re.findall(r"date:'([\d\-]+)', type:'(廃盤|入替)', title:'([^']+)'", blk):
        core = re.findall(r"『([^』]+)』", title)
        if core and not any(c in known for c in core):
            miss.append("%s [%s] %s" % (d, t, title))
    return miss


EXTRA = """
<style>
  .crumbs { margin:28px 0 0; font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:.18em; color:var(--mute); }
  .crumbs a { text-decoration:none; border-bottom:1px solid var(--linesoft); }
  .crumbs a:hover { color:var(--rust); border-bottom-color:currentColor; }
  .crumbs span { margin:0 8px; color:#b9b9b4; }
  .note { margin:22px 0 0; padding:18px 20px; border:1px solid var(--linesoft); background:#efe9dc; font-size:13px; line-height:2; }
  .dc { margin:34px 0 0; border:1px solid var(--line); }
  .dc-head { padding:16px 18px; border-bottom:1px solid var(--line); background:#efe9dc; }
  .dc-name { margin:0; font-family:'Shippori Mincho B1',serif; font-weight:700; font-size:18px; line-height:1.6; }
  .dc-meta { margin:6px 0 0; font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:.14em; color:var(--mute); }
  .dc-rows { }
  .dc-row { display:grid; grid-template-columns:6.5em 1fr; gap:10px; padding:13px 18px; border-bottom:1px solid var(--linesoft); font-size:13px; line-height:1.95; }
  .dc-row:last-child { border-bottom:0; }
  .dc-row dt { font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:.12em; color:var(--mute); margin:0; }
  .dc-row dd { margin:0; }
  .dc-row a { border-bottom:1px solid var(--linesoft); text-decoration:none; }
  .dc-row a:hover { color:var(--rust); border-bottom-color:currentColor; }
  .cta { margin:40px 0 0; padding:34px 26px; border:1px solid var(--line); background:#efe9dc; }
  .cta-label { margin:0; font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:.28em; text-transform:uppercase; color:var(--rust); }
  .cta-title { margin:16px 0 0; font-family:'Shippori Mincho B1',serif; font-weight:800; font-size:clamp(1.25rem,4vw,1.6rem); line-height:1.7; }
  .cta-text { margin:16px 0 0; font-size:13px; line-height:2.1; color:var(--mute); }
  .cta-btn { display:inline-flex; align-items:center; gap:14px; margin:26px 0 0; font-family:'Shippori Mincho B1',serif; font-weight:700; font-size:18px; text-decoration:none; border-bottom:1px solid var(--ink); padding-bottom:4px; }
  .cta-btn .arrow { font-family:'IBM Plex Mono',monospace; transition:transform .3s cubic-bezier(.22,1,.36,1); }
  .cta-btn:hover { color:var(--rust); border-bottom-color:var(--rust); }
  .cta-btn:hover .arrow { transform:translateX(10px); }
  @media (min-width:768px){ .dc-row { font-size:14px; padding:15px 20px; } .dc-name { font-size:20px; } }
</style>"""


def build():
    style = load_style()
    url = SITE + "products/discontinued.html"
    h1 = "廃盤・生産終了になった物置と、その後継"
    desc = ("タクボ・イナバ・ヨドコウで廃盤・生産終了になった物置と、その後継の記録です。"
            "各メーカーの公式発表をもとに、確認できた日付とあわせて残しています。")

    coll = {"@context": "https://schema.org", "@type": "CollectionPage", "name": h1,
            "description": desc, "url": url, "inLanguage": "ja",
            "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE},
            "publisher": {"@type": "Organization", "name": NAME}}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "トップ", "item": SITE},
        {"@type": "ListItem", "position": 2, "name": "製品", "item": SITE + "products/"},
        {"@type": "ListItem", "position": 3, "name": "廃盤・生産終了"}]}

    blocks = ""
    for it in ITEMS:
        after = (('<a href="%s">%s</a>' % (esc(it["after_url"]), esc(it["after"])))
                 if it["after_url"] else esc(it["after"]))
        blocks += ('<div class="dc">'
                   '<div class="dc-head"><p class="dc-name">%s</p>'
                   '<p class="dc-meta">%s — %s</p></div>'
                   '<dl class="dc-rows">'
                   '<div class="dc-row"><dt>状況</dt><dd>%s</dd></div>'
                   '<div class="dc-row"><dt>後継</dt><dd>%s</dd></div>'
                   '<div class="dc-row"><dt>出典</dt><dd>%s</dd></div>'
                   '<div class="dc-row"><dt>確認日</dt><dd>%s</dd></div>'
                   '</dl></div>'
                   % (esc(it["name"]), esc(it["maker"]), esc(it["kubun"]),
                      esc(it["state"]), after, esc(it["src"]), esc(it["checked"])))

    html = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(h1)s｜%(site)s</title>
<meta name="description" content="%(desc)s">
<meta name="theme-color" content="#101010">
<link rel="canonical" href="%(url)s">
<meta property="og:type" content="website">
<meta property="og:site_name" content="%(site)s">
<meta property="og:title" content="%(h1)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(url)s">
<meta property="og:image" content="%(siteurl)simages/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%%3E%%3Crect width='64' height='64' fill='%%23101010'/%%3E%%3Ctext x='32' y='45' font-family='serif' font-size='34' font-weight='bold' fill='%%23ffffff' text-anchor='middle'%%3E倉%%3C/text%%3E%%3C/svg%%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@600;700;800&family=Noto+Sans+JP:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
%(style)s
%(extra)s
<script type="application/ld+json">
%(coll)s
</script>
<script type="application/ld+json">
%(crumb)s
</script>
</head>
<body>

<header class="site-header">
  <div class="site-header-inner">
    <a href="../" class="brand"><span class="brand-mark">倉</span><span class="brand-name">%(site)s</span></a>
    <a href="../" class="header-link">← トップへ戻る</a>
  </div>
</header>

<main>
  <div class="wrap">
    <nav class="crumbs" aria-label="パンくずリスト">
      <a href="../">トップ</a><span>/</span><a href="./">製品</a><span>/</span>廃盤・生産終了
    </nav>

    <div class="page-head">
      <p class="page-kicker">Discontinued — 廃盤・生産終了</p>
      <h1 class="page-title">廃盤・生産終了になった物置と、その後継。</h1>
      <p class="page-lead">販売しているサイトは、終わった商品のページを消していきます。ここは<b>消さずに残します</b>。いま使っている物置の型番を調べたい方、同じシリーズの後継を探している方へ。各メーカーの公式発表をもとに、<b>確認できた日付とあわせて</b>記録しています。</p>
    </div>

    <div class="note">
      <p style="margin:0">※後継が発表されていないものもあります。</p>
      <p style="margin:14px 0 0">※部品の供給や修理の可否は、製品と時期によって変わります。<b>各メーカーへ直接お問い合わせください。</b>当サイトでは分かりかねます。</p>
      <p style="margin:14px 0 0">※記載は上記「確認日」時点のものです。ご購入・お手続きの前に、必ず各メーカーの公式サイトでご確認ください。</p>
    </div>

%(blocks)s

    <div class="cta">
      <p class="cta-label">Next — 次に</p>
      <p class="cta-title">後継や、いま買える物置をさがす。</p>
      <p class="cta-text">現行の18製品は製品一覧に、置ける寸法から絞り込む一覧は「寸法から探す」にまとめています。</p>
      <a class="cta-btn" href="./">製品一覧を見る <span class="arrow">→</span></a>
    </div>

    <div class="nav-links">
      <a href="./">製品一覧へ</a>
      <a href="../size/">寸法から探す</a>
      <a href="../#journal">更新履歴</a>
      <a href="../contact.html">お問い合わせ</a>
    </div>
  </div>
</main>

<footer class="site-footer">
  <div class="site-footer-inner">
    <div class="footer-meta">
      <a href="../">← %(site)s トップへ</a>
      <a href="../about.html">運営者情報</a>
      <a href="../privacy.html">プライバシーポリシー</a>
      <span>© 2026 %(site)s — 非公式情報比較メディア</span>
    </div>
  </div>
</footer>

</body>
</html>
""" % dict(h1=esc(h1), site=NAME, desc=esc(desc), url=url, siteurl=SITE,
           style=style, extra=EXTRA,
           coll=json.dumps(coll, ensure_ascii=False, indent=2),
           crumb=json.dumps(crumb, ensure_ascii=False, indent=2),
           blocks=blocks)

    old = open(OUTP, encoding="utf-8").read() if os.path.exists(OUTP) else None
    if old != html:
        open(OUTP, "w", encoding="utf-8").write(html)
        print("[廃盤] products/discontinued.html を更新しました（%d件）" % len(ITEMS))
    else:
        print("[廃盤] 変更はありません（%d件）" % len(ITEMS))

    miss = check_log()
    if miss:
        print("[廃盤][注意] 更新履歴にあるのに、このページに載っていない記録があります。")
        print("            出典と後継を確認して tools/build-discontinued.py の ITEMS に足してください。")
        for m in miss:
            print("            " + m)


if __name__ == "__main__":
    build()
