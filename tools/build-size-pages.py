#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""寸法から絞り込む静的ページ（size/）を、index.html の PRODUCTS から生成する。

・製品名から探すのではなく「置ける寸法から探す」ための入口を作る
・データは index.html の PRODUCTS が唯一の出典。ここでは新しい数値を作らない
・車庫・ガレージ・バイク保管庫は物置の2区分に含めないため、対象から外す
・製品データが変わったら作り直せるよう、publish.sh から自動で呼ばれる
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://monooki-erabi.com/"
NAME = "物置どれがいい？"
OUT  = os.path.join(ROOT, "size")

MAKER_JP = {"takubo": "タクボ", "inaba": "イナバ", "yodoko": "ヨドコウ"}
# 物置の2区分のみを対象にする（車庫・ガレージ・バイク保管庫は別物）
CAT_OK = {"小型物置", "中型物置", "中・大型物置", "大型物置"}
KUBUN  = {"小型物置": "小型（収納庫）", "中型物置": "中型・大型",
          "中・大型物置": "中型・大型", "大型物置": "中型・大型"}

# ── 生成するページ。axis: w=間口 / d=奥行 / h=高さ ──
PAGES = [
    dict(slug="depth-600",  axis="d", limit=600,
         h1="奥行60cm以下で置ける物置",
         kicker="Depth — 奥行から探す",
         lead="隣家との隙間や、家の脇の通路など、奥行がとれない場所に置ける物置です。",
         why="奥行が足りないと、扉を開けたときに前へ出る分まで含めて収まらないことがあります。物を出し入れする側に、どれだけ余裕があるかもあわせてご確認ください。"),
    dict(slug="depth-900",  axis="d", limit=900,
         h1="奥行90cm以下で置ける物置",
         kicker="Depth — 奥行から探す",
         lead="奥行90cm以下に収まる物置です。小型（収納庫）の多くがこの範囲に入ります。",
         why="奥行が浅いほど、置ける場所は増えますが、中に人が入って作業することは難しくなります。何をどう出し入れするかで、必要な奥行は変わります。"),
    dict(slug="height-1400", axis="h", limit=1400,
         h1="高さ1.4m以下の物置（窓の下に収まる）",
         kicker="Height — 高さから探す",
         lead="窓の下や、低い塀の内側に収めたいときの物置です。",
         why="高さは、本体だけで判断できません。下に敷く基礎ブロックの分が加わります。"),
    dict(slug="height-1900", axis="h", limit=1900,
         h1="高さ1.9m以下の物置",
         kicker="Height — 高さから探す",
         lead="軒下や、目線の高さを超えたくない場所に置ける物置です。",
         why="高さは、本体だけで判断できません。下に敷く基礎ブロックの分が加わります。"),
    dict(slug="width-1200", axis="w", limit=1200,
         h1="間口1.2m以下の物置（幅がとれない場所へ）",
         kicker="Width — 間口から探す",
         lead="幅の狭いスペースに置ける物置です。",
         why="間口は、置けるかどうかだけでなく、何を入れられるかも左右します。タイヤや長い物を入れる予定があるなら、間口も見ておいてください。"),
    dict(slug="width-1500", axis="w", limit=1500,
         h1="間口1.5m以下の物置",
         kicker="Width — 間口から探す",
         lead="間口1.5m以下に収まる物置です。",
         why="間口は、置けるかどうかだけでなく、何を入れられるかも左右します。タイヤや長い物を入れる予定があるなら、間口も見ておいてください。"),
]
AXIS_JP = {"w": "間口", "d": "奥行", "h": "高さ"}


def load_products():
    s = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    i = s.find("const PRODUCTS = [")
    j = i + len("const PRODUCTS = ")
    depth = 0
    for k in range(j, len(s)):
        if s[k] == "[":
            depth += 1
        elif s[k] == "]":
            depth -= 1
            if depth == 0:
                end = k + 1
                break
    blk = s[j:end]
    pages = dict(re.findall(r"'([a-z0-9\-]+)':\s*'(products/[^']+)'", s))
    out = []
    for m in re.finditer(r"id:'([a-z0-9\-]+)', maker:'(\w+)', name:'([^']+)', cat:'([^']+)'", blk):
        pid, mk, nm, cat = m.groups()
        seg = blk[m.end(): m.end() + 12000]
        nx = seg.find("\n  { id:'")
        if nx > 0:
            seg = seg[:nx]
        sizes = [(c, int(w), int(d), int(h))
                 for c, w, d, h in re.findall(r"code:'([^']+)', w:(\d+), d:(\d+), h:(\d+)", seg)]
        out.append(dict(id=pid, maker=mk, name=nm, cat=cat, sizes=sizes, page=pages.get(pid, "")))
    return out


def load_style():
    s = open(os.path.join(ROOT, "products", "index.html"), encoding="utf-8").read()
    i = s.find("<style"); j = s.find("</style>") + len("</style>")
    return s[i:j]


EXTRA_CSS = """
<style>
  /* 製品ページから流用（products/index.html の CSS に無いもの） */
  .crumbs { margin:28px 0 0; font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:.18em; color:var(--mute); }
  .crumbs a { text-decoration:none; border-bottom:1px solid var(--linesoft); }
  .crumbs a:hover { color:var(--rust); border-bottom-color:currentColor; }
  .crumbs span { margin:0 8px; color:#b9b9b4; }
  .note { margin:22px 0 0; padding:18px 20px; border:1px solid var(--linesoft); background:#efe9dc; font-size:13px; line-height:2; }
  .cta { margin:40px 0 0; padding:34px 26px; border:1px solid var(--line); background:#efe9dc; }
  .cta-label { margin:0; font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:.28em; text-transform:uppercase; color:var(--rust); }
  .cta-title { margin:16px 0 0; font-family:'Shippori Mincho B1',serif; font-weight:800; font-size:clamp(1.25rem,4vw,1.6rem); line-height:1.7; }
  .cta-text { margin:16px 0 0; font-size:13px; line-height:2.1; color:var(--mute); }
  .cta-btn { display:inline-flex; align-items:center; gap:14px; margin:26px 0 0;
    font-family:'Shippori Mincho B1',serif; font-weight:700; font-size:18px;
    text-decoration:none; border-bottom:1px solid var(--ink); padding-bottom:4px; }
  .cta-btn .arrow { font-family:'IBM Plex Mono',monospace; transition:transform .3s cubic-bezier(.22,1,.36,1); }
  .cta-btn:hover { color:var(--rust); border-bottom-color:var(--rust); }
  .cta-btn:hover .arrow { transform:translateX(10px); }
  .sz-table { width:100%; border-collapse:collapse; margin:26px 0 0; font-size:13px; }
  .sz-table th, .sz-table td { padding:10px 8px; border-bottom:1px solid var(--linesoft); text-align:right; font-variant-numeric:tabular-nums; }
  .sz-table th { font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:.12em; text-transform:uppercase; color:var(--mute); font-weight:400; border-bottom:1px solid var(--line); white-space:nowrap; }
  .sz-table td:nth-child(1), .sz-table th:nth-child(1),
  .sz-table td:nth-child(2), .sz-table th:nth-child(2),
  .sz-table td:nth-child(3), .sz-table th:nth-child(3) { text-align:left; }
  .sz-table td:nth-child(3) { font-family:'IBM Plex Mono',monospace; letter-spacing:.02em; }
  .sz-table tbody tr:hover { background:#efe9dc; }
  .sz-table a { text-decoration:none; border-bottom:1px solid var(--linesoft); }
  .sz-table a:hover { color:var(--rust); border-bottom-color:currentColor; }
  .sz-sum { margin:26px 0 0; border:1px solid var(--line); }
  .sz-sum p { margin:0; padding:12px 16px; font-size:13px; line-height:1.9; border-bottom:1px solid var(--linesoft); }
  .sz-sum p:last-child { border-bottom:0; }
  .sz-sum b { font-weight:700; }
  .sz-links { margin:40px 0 0; display:flex; flex-wrap:wrap; gap:10px; }
  .sz-links a { border:1px solid var(--line); padding:9px 14px; font-size:12px; text-decoration:none; }
  .sz-links a:hover { background:var(--ink); color:var(--paper); }
  .sz-links a.is-here { background:var(--ink); color:var(--paper); pointer-events:none; }
  @media (min-width:768px){ .sz-table th, .sz-table td { font-size:14px; padding:12px 10px; } }
</style>"""


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def page_html(cfg, rows, series, style, nav_links, desc):
    axis = cfg["axis"]
    unit = AXIS_JP[axis]
    url = SITE + "size/" + cfg["slug"] + ".html"
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "トップ", "item": SITE},
        {"@type": "ListItem", "position": 2, "name": "寸法から探す", "item": SITE + "size/"},
        {"@type": "ListItem", "position": 3, "name": cfg["h1"]}]}
    coll = {"@context": "https://schema.org", "@type": "CollectionPage",
            "name": cfg["h1"], "description": desc, "url": url, "inLanguage": "ja",
            "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE},
            "publisher": {"@type": "Organization", "name": NAME}}

    trs = []
    for p, (code, w, d, h) in rows:
        link = ('<a href="../%s">%s</a>' % (esc(p["page"]), esc(p["name"]))) if p["page"] else esc(p["name"])
        trs.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (MAKER_JP[p["maker"]], link, esc(code), KUBUN.get(p["cat"], p["cat"]),
               "{:,}".format(w), "{:,}".format(d), "{:,}".format(h)))

    sums = "".join(
        "<p><b>%s %s</b> — %d型番（%s）</p>" % (MAKER_JP[p["maker"]], esc(p["name"]), n, KUBUN.get(p["cat"], p["cat"]))
        for p, n in series)

    return """<!DOCTYPE html>
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
<link rel="icon" href="/favicon.ico" sizes="48x48">
  <link rel="icon" type="image/png" sizes="96x96" href="/images/favicon-96.png">
  <link rel="icon" type="image/png" sizes="192x192" href="/images/favicon-192.png">
  <link rel="apple-touch-icon" href="/images/apple-touch-icon.png">
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
      <a href="../">トップ</a><span>/</span><a href="./">寸法から探す</a><span>/</span>%(h1)s
    </nav>

    <div class="page-head">
      <p class="page-kicker">%(kicker)s</p>
      <h1 class="page-title">%(h1)s</h1>
      <p class="page-lead">%(lead)s タクボ・イナバ・ヨドコウの3メーカーから、<b>%(unit)s%(limit)smm以下の型番を%(ncode)d件</b>集めました（%(nseries)dシリーズ）。</p>
    </div>

    <div class="note">
      <p style="margin:0">%(why)s</p>
      <p style="margin:14px 0 0">※本体の下には基礎用コンクリートブロック（基本 高さ約10cm）を敷きます。<b>実際の高さは「本体高さ＋約10cm」</b>になるため、高さに制限のある場所では、ブロック分を含めてご確認ください。</p>
      <p style="margin:14px 0 0">※この一覧は<b>物置のみ</b>です。車庫・ガレージ・バイク保管庫は含めていません。寸法は各メーカーの公表値をもとにしています。ご購入前に必ず公式サイト・最新カタログでご確認ください。</p>
    </div>

    <div class="sz-sum">%(sums)s</div>

    <table class="sz-table">
      <thead><tr><th>メーカー</th><th>シリーズ</th><th>型番</th><th>区分</th><th>間口 mm</th><th>奥行 mm</th><th>高さ mm</th></tr></thead>
      <tbody>%(trs)s</tbody>
    </table>

    <div class="sz-links">%(nav)s</div>

    <div class="cta">
      <p class="cta-label">Next — 次に</p>
      <p class="cta-title">置ける寸法は分かったけれど、どれを選ぶか迷う。</p>
      <p class="cta-text">収納したい物や使い方から絞り込むこともできます。質問は3〜4問、1分ほどで終わります。</p>
      <a class="cta-btn" href="../#shindan">診断をはじめる <span class="arrow">→</span></a>
    </div>

    <div class="nav-links">
      <a href="../products/">製品一覧へ</a>
      <a href="./">寸法から探す（一覧）</a>
      <a href="../#articles">記事を読む</a>
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
""" % dict(h1=esc(cfg["h1"]), site=NAME, desc=esc(desc), url=url, siteurl=SITE,
           style=style, extra=EXTRA_CSS,
           coll=json.dumps(coll, ensure_ascii=False, indent=2),
           crumb=json.dumps(crumb, ensure_ascii=False, indent=2),
           kicker=esc(cfg["kicker"]), lead=esc(cfg["lead"]), why=esc(cfg["why"]),
           unit=unit, limit="{:,}".format(cfg["limit"]),
           ncode=len(rows), nseries=len(series),
           sums=sums, trs="".join(trs), nav=nav_links)


def hub_html(style, cards):
    url = SITE + "size/"
    desc = "置ける場所の寸法から物置をさがせます。奥行・高さ・間口ごとに、タクボ・イナバ・ヨドコウの型番を横断して並べています。"
    coll = {"@context": "https://schema.org", "@type": "CollectionPage",
            "name": "寸法から探す", "description": desc, "url": url, "inLanguage": "ja",
            "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE},
            "publisher": {"@type": "Organization", "name": NAME}}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "トップ", "item": SITE},
        {"@type": "ListItem", "position": 2, "name": "寸法から探す"}]}
    return """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>寸法から物置をさがす｜奥行・高さ・間口で絞り込む｜%(site)s</title>
<meta name="description" content="%(desc)s">
<meta name="theme-color" content="#101010">
<link rel="canonical" href="%(url)s">
<meta property="og:type" content="website">
<meta property="og:site_name" content="%(site)s">
<meta property="og:title" content="寸法から物置をさがす｜奥行・高さ・間口で絞り込む">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(url)s">
<meta property="og:image" content="%(siteurl)simages/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="48x48">
  <link rel="icon" type="image/png" sizes="96x96" href="/images/favicon-96.png">
  <link rel="icon" type="image/png" sizes="192x192" href="/images/favicon-192.png">
  <link rel="apple-touch-icon" href="/images/apple-touch-icon.png">
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
      <a href="../">トップ</a><span>/</span>寸法から探す
    </nav>

    <div class="page-head">
      <p class="page-kicker">Size — 寸法から探す</p>
      <h1 class="page-title">寸法から探す。</h1>
      <p class="page-lead">「ここに置きたい」が先に決まっている方へ。タクボ・イナバ・ヨドコウの3メーカーを横断して、<b>置ける寸法から物置を絞り込めます</b>。掲載は物置のみで、車庫・ガレージ・バイク保管庫は含めていません。</p>
    </div>

    <ul class="card-list">%(cards)s</ul>

    <div class="cta">
      <p class="cta-label">Next — 次に</p>
      <p class="cta-title">寸法がまだ決まっていない方へ。</p>
      <p class="cta-text">収納したい物や使い方から絞り込むこともできます。質問は3〜4問、1分ほどで終わります。</p>
      <a class="cta-btn" href="../#shindan">診断をはじめる <span class="arrow">→</span></a>
    </div>

    <div class="nav-links">
      <a href="../products/">製品一覧へ</a>
      <a href="../#articles">記事を読む</a>
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
""" % dict(site=NAME, desc=esc(desc), url=url, siteurl=SITE, style=style, extra=EXTRA_CSS,
           coll=json.dumps(coll, ensure_ascii=False, indent=2),
           crumb=json.dumps(crumb, ensure_ascii=False, indent=2), cards=cards)


def main():
    prods = [p for p in load_products() if p["cat"] in CAT_OK and p["sizes"]]
    style = load_style()
    os.makedirs(OUT, exist_ok=True)
    idx = {"w": 1, "d": 2, "h": 3}
    written = []
    cards = []

    navs = {c["slug"]: c for c in PAGES}
    for cfg in PAGES:
        ax = cfg["axis"]; lim = cfg["limit"]
        rows, series = [], []
        for p in prods:
            hit = [s for s in p["sizes"] if s[idx[ax]] <= lim]
            if not hit:
                continue
            series.append((p, len(hit)))
            rows += [(p, s) for s in hit]
        rows.sort(key=lambda r: (r[1][idx[ax]], r[1][1], r[1][2]))
        series.sort(key=lambda x: -x[1])

        desc = ("%s%smm以下に収まる物置の型番一覧です。タクボ・イナバ・ヨドコウの3メーカーから%d型番（%dシリーズ）。"
                "間口・奥行・高さを一覧で比べられます。"
                % (AXIS_JP[ax], "{:,}".format(lim), len(rows), len(series)))

        nav = "".join(
            '<a href="%s.html"%s>%s</a>' % (c["slug"], ' class="is-here"' if c["slug"] == cfg["slug"] else "",
                                            esc(c["h1"]))
            for c in PAGES)

        html = page_html(cfg, rows, series, style, nav, desc)
        path = os.path.join(OUT, cfg["slug"] + ".html")
        old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if old != html:
            open(path, "w", encoding="utf-8").write(html)
            written.append(cfg["slug"] + ".html")
        print("  %-14s %3d型番 / %dシリーズ  %s" % (cfg["slug"], len(rows), len(series), cfg["h1"]))

        cards.append(
            '<li class="card"><a class="card-inner" href="%s.html">'
            '<span class="card-date">%s<span class="card-tag">%d型番を掲載</span></span>'
            '<h2 class="card-title">%s</h2><p class="card-desc">%s</p>'
            '<span class="card-more">一覧を見る <span class="arrow">→</span></span></a></li>'
            % (cfg["slug"], AXIS_JP[ax] + "で絞る", len(rows), esc(cfg["h1"]), esc(cfg["lead"])))

    # サイズ帯ページ（build-bands.py が先に書き出す）をハブに載せる
    bpath = os.path.join(ROOT, "tools", "_bands.json")
    if os.path.exists(bpath):
        bands = json.load(open(bpath, encoding="utf-8"))
        if bands:
            cards.append('<li class="card" style="border:0;padding:0;margin-top:48px">'
                         '<p class="card-date" style="font-size:11px">サイズ帯で3メーカーを比べる</p></li>')
            for b in bands:
                cards.append(
                    '<li class="card"><a class="card-inner" href="%s.html">'
                    '<span class="card-date">%d社で比較<span class="card-tag">%d型番</span></span>'
                    '<h2 class="card-title">%s</h2><p class="card-desc">%s</p>'
                    '<span class="card-more">並べて見る <span class="arrow">→</span></span></a></li>'
                    % (b["slug"], b["nm"], b["n"], esc(b["title"]), esc(b["lead"])))

    hub = hub_html(style, "".join(cards))
    hp = os.path.join(OUT, "index.html")
    old = open(hp, encoding="utf-8").read() if os.path.exists(hp) else None
    if old != hub:
        open(hp, "w", encoding="utf-8").write(hub)
        written.append("index.html")

    print("[size] 更新: %s" % (", ".join(written) if written else "変更なし"))


if __name__ == "__main__":
    main()
