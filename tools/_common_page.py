# -*- coding: utf-8 -*-
"""生成ページ共通の読み込み・雛形。build-*.py から使う。"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://monooki-erabi.com/"
NAME = "物置どれがいい？"
MAKER_JP = {"takubo": "タクボ", "inaba": "イナバ", "yodoko": "ヨドコウ"}
CAT_OK = {"小型物置", "中型物置", "中・大型物置", "大型物置"}
KUBUN = {"小型物置": "小型（収納庫）", "中型物置": "中型・大型",
         "中・大型物置": "中型・大型", "大型物置": "中型・大型",
         "バイク車庫": "バイク車庫", "ガレージ": "ガレージ", "断熱物置": "断熱物置"}


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


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
        door = re.search(r"door:'([^']*)'", seg)
        out.append(dict(
            id=pid, maker=mk, name=nm, cat=cat, page=pages.get(pid, ""),
            door=door.group(1) if door else "",
            sizes=[(c, int(w), int(d), int(h))
                   for c, w, d, h in re.findall(r"code:'([^']+)', w:(\d+), d:(\d+), h:(\d+)", seg)]))
    return out


def load_style():
    s = open(os.path.join(ROOT, "products", "index.html"), encoding="utf-8").read()
    i = s.find("<style"); j = s.find("</style>") + len("</style>")
    return s[i:j]


EXTRA_CSS = """
<style>
  .crumbs { margin:28px 0 0; font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:.18em; color:var(--mute); }
  .crumbs a { text-decoration:none; border-bottom:1px solid var(--linesoft); }
  .crumbs a:hover { color:var(--rust); border-bottom-color:currentColor; }
  .crumbs span { margin:0 8px; color:#b9b9b4; }
  .note { margin:22px 0 0; padding:18px 20px; border:1px solid var(--linesoft); background:#efe9dc; font-size:13px; line-height:2; }
  .tbl { width:100%; border-collapse:collapse; margin:18px 0 0; font-size:13px; }
  .tbl th, .tbl td { padding:10px 8px; border-bottom:1px solid var(--linesoft); text-align:right; font-variant-numeric:tabular-nums; }
  .tbl th { font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:.12em; text-transform:uppercase; color:var(--mute); font-weight:400; border-bottom:1px solid var(--line); white-space:nowrap; }
  .tbl td.l, .tbl th.l { text-align:left; }
  .tbl td.m { font-family:'IBM Plex Mono',monospace; letter-spacing:.02em; }
  .tbl tbody tr:hover { background:#efe9dc; }
  .tbl a { text-decoration:none; border-bottom:1px solid var(--linesoft); }
  .tbl a:hover { color:var(--rust); border-bottom-color:currentColor; }
  .grp { margin:44px 0 0; padding:14px 16px; border:1px solid var(--line); background:#efe9dc; }
  .grp h2 { margin:0; font-family:'Shippori Mincho B1',serif; font-weight:700; font-size:17px; line-height:1.6; }
  .grp p { margin:5px 0 0; font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:.14em; color:var(--mute); }
  .grp a { text-decoration:none; border-bottom:1px solid var(--linesoft); }
  .grp a:hover { color:var(--rust); }
  .jump { margin:26px 0 0; display:flex; flex-wrap:wrap; gap:8px; }
  .jump a { border:1px solid var(--line); padding:7px 12px; font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:.08em; text-decoration:none; }
  .jump a:hover { background:var(--ink); color:var(--paper); }
  .links { margin:40px 0 0; display:flex; flex-wrap:wrap; gap:10px; }
  .links a { border:1px solid var(--line); padding:9px 14px; font-size:12px; text-decoration:none; }
  .links a:hover { background:var(--ink); color:var(--paper); }
  .links a.is-here { background:var(--ink); color:var(--paper); pointer-events:none; }
  .cta { margin:40px 0 0; padding:34px 26px; border:1px solid var(--line); background:#efe9dc; }
  .cta-label { margin:0; font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:.28em; text-transform:uppercase; color:var(--rust); }
  .cta-title { margin:16px 0 0; font-family:'Shippori Mincho B1',serif; font-weight:800; font-size:clamp(1.25rem,4vw,1.6rem); line-height:1.7; }
  .cta-text { margin:16px 0 0; font-size:13px; line-height:2.1; color:var(--mute); }
  .cta-btn { display:inline-flex; align-items:center; gap:14px; margin:26px 0 0; font-family:'Shippori Mincho B1',serif; font-weight:700; font-size:18px; text-decoration:none; border-bottom:1px solid var(--ink); padding-bottom:4px; }
  .cta-btn .arrow { font-family:'IBM Plex Mono',monospace; transition:transform .3s cubic-bezier(.22,1,.36,1); }
  .cta-btn:hover { color:var(--rust); border-bottom-color:var(--rust); }
  .cta-btn:hover .arrow { transform:translateX(10px); }
  @media (min-width:768px){ .tbl th, .tbl td { font-size:14px; padding:12px 10px; } .grp h2 { font-size:19px; } }
</style>"""


def shell(title, desc, url, up, crumbs, body, style, jsonld):
    """up = 上位ディレクトリへの相対パス（'../'）"""
    ld = "\n".join('<script type="application/ld+json">\n%s\n</script>' % x for x in jsonld)
    return """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(title)s｜%(site)s</title>
<meta name="description" content="%(desc)s">
<meta name="theme-color" content="#101010">
<link rel="canonical" href="%(url)s">
<meta property="og:type" content="website">
<meta property="og:site_name" content="%(site)s">
<meta property="og:title" content="%(title)s">
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
%(ld)s
</head>
<body>

<header class="site-header">
  <div class="site-header-inner">
    <a href="%(up)s" class="brand"><span class="brand-mark"><svg viewBox="0 0 128 128" width="23" height="23" fill="currentColor" aria-hidden="true"><rect x="10" y="27" width="108" height="14" rx="1"/><rect x="22" y="47" width="38" height="54"/><rect x="68" y="47" width="38" height="54"/></svg></span><span class="brand-name">%(site)s</span></a>
    <a href="%(up)s" class="header-link">← トップへ戻る</a>
  </div>
</header>

<main>
  <div class="wrap">
    <nav class="crumbs" aria-label="パンくずリスト">%(crumbs)s</nav>
%(body)s
  </div>
</main>

<footer class="site-footer">
  <div class="site-footer-inner">
    <div class="footer-meta">
      <a href="%(up)s">← %(site)s トップへ</a>
      <a href="%(up)sabout.html">運営者情報</a>
      <a href="%(up)sprivacy.html">プライバシーポリシー</a>
      <span>© 2026 %(site)s — 非公式情報比較メディア</span>
    </div>
  </div>
</footer>

</body>
</html>
""" % dict(title=esc(title), desc=esc(desc), url=url, site=NAME, siteurl=SITE,
           style=style, extra=EXTRA_CSS, ld=ld, up=up, crumbs=crumbs, body=body)
