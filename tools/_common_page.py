# -*- coding: utf-8 -*-
"""生成ページ共通の読み込み・雛形。build-*.py から使う。"""
import json, os, re, urllib.parse

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


SID, PID = "3777863", "892682808"


def load_exshop():
    """index.html の EXSHOP を読む。{製品id: 販売店のシリーズ識別子}。
       'wh:' が頭に付いているものは倉庫・ガレージのカテゴリ。
       提携先リンクの出典はここ1か所だけ。表を2つ持つと必ず食い違う
       （2026-10-19 まで build-shop-links.py が別表を持っていて、9シリーズずれていた）"""
    s = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    i = s.find("const EXSHOP")
    if i < 0:
        return {}
    j = s.find("};", i)
    return dict(re.findall(r"'([a-z0-9\-]+)'\s*:\s*'([^']+)'", s[i:j]))


def exshop_url(code):
    """販売店（エクスショップ）の行き先。書き方は index.html の affUrl と同じ。
       （カテゴリ:）＋（種類:）＋値。カテゴリを省くと物置・収納（mo）。
         'inaba_s5'            物置・収納のシリーズ一覧
         'wh:inaba_s1'         倉庫・ガレージのシリーズ一覧
         'word:ペインタ'       商品名で絞った一覧（販売店側にシリーズの枠が無いとき）
         'xz:word:como lite'   お問い合わせ商品を商品名で絞った一覧
         'xz:item:8162'        お問い合わせ商品の見積もりページ（その商品1件しか無いとき）"""
    cat = "mo"
    s = code
    for c in ("mo:", "wh:", "xz:"):
        if s.startswith(c):
            cat, s = c[:-1], s[len(c):]
            break
    base = "https://www.ex-shop.net/index.php?action=public_item_%s_" % cat
    if s.startswith("item:"):
        return base + "estimate_input&item_id=" + urllib.parse.quote(s[5:], safe="")
    if s.startswith("word:"):
        q = "&search_word_like_ex=" + urllib.parse.quote(s[5:], safe="")
    else:
        q = "&se_series=" + urllib.parse.quote("series:" + s, safe="")
    return base + "search_execute" + q

def aff_url(code):
    """提携（バリューコマース）を通した行き先。生のURLは使わない"""
    return ("//ck.jp.ap.valuecommerce.com/servlet/referral?sid=%s&pid=%s&vc_url=%s"
            % (SID, PID, urllib.parse.quote(exshop_url(code), safe="")))


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
        note = re.search(r"codeNote:'([^']*)'", seg)
        # 桁揃えで空白が余分に入っている行がある（例 d:950,  h:2085）。
        # 空白を固定で書くと取りこぼす（2026-09-17 に型番索引が 343→337 と表示していた）。
        sizes = [(c, int(float(w)+0.5), int(float(d)+0.5), int(float(h)+0.5)) for c, w, d, h in re.findall(
            r"code:'([^']+)'\s*,\s*w:\s*([\d.]+)\s*,\s*d:\s*([\d.]+)\s*,\s*h:\s*([\d.]+)", seg)]
        loose = len(re.findall(r"code:'[^']+'", seg))
        if loose != len(sizes):
            raise SystemExit("[中止] %s の型番を取りこぼしました（%d 件中 %d 件）。書式を確認してください。"
                             % (pid, loose, len(sizes)))
        out.append(dict(
            id=pid, maker=mk, name=nm, cat=cat, page=pages.get(pid, ""),
            door=door.group(1) if door else "",
            codeNote=note.group(1) if note else "",
            sizes=sizes))
    return out


def load_inner():
    """index.html の INNER を読む。型番 → (内寸W, 内寸D, 内寸H, 開口W, 開口H)。
    外形寸法は PRODUCTS 側。ここに無い型番は、公式に内寸が見当たらないもの。"""
    s = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    i = s.find("INNER_START")
    if i < 0:
        return {}
    j = s.index("const INNER", i)
    k = s.index("};", j)
    out = {}
    for m in re.finditer(r"'([^']+)':\s*\[([^\]]+)\]", s[j:k]):
        v = [None if x.strip() == "null" else float(x) for x in m.group(2).split(",")]
        if len(v) != 5:
            raise SystemExit("[中止] INNER の %s が5つの値になっていません" % m.group(1))
        out[m.group(1)] = tuple(v)
    return out


def load_load():
    """tools/_load.json を読む。耐荷重まわりの公式値はここが唯一の出典。

    3社で測っているものも単位も違う。横に並べて数値を比べる使い方はしない。
      タクボ   … 床耐荷重。1棟あたりの合計（kg）。型番ごとに値がある
      ヨドコウ … 屋根・棚・床の耐荷重。面積あたり（N/m2）。シリーズと型区分ごと
      イナバ   … 積雪強度。屋根にかかる雪（N/m2）。シリーズと型区分ごと
    """
    p = os.path.join(ROOT, "tools", "_load.json")
    if not os.path.exists(p):
        raise SystemExit("[中止] tools/_load.json がありません。"
                         "耐荷重の値はこのファイルが唯一の出典です。")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def floor_load():
    """タクボの型番 → 床耐荷重（kg）。公式に記載のない型番は入っていない。"""
    return {c: v["kg"] for c, v in load_load()["takubo"]["型番"].items()}


def _nm(v):
    return "{:,}N/m²".format(v)


def load_spec_row(pid):
    """製品ページの仕様表に足す1行。(項目名, 値) か None を返す。

    タクボはここでは返さない。型番ごとに値が違うので、サイズ表に列で出す。
    """
    d = load_load()

    y = d["yodoko"]["シリーズ"].get(pid)
    if y:
        if "型区分なし" in y:
            v = y["型区分なし"]
            return ("耐荷重", "屋根 %s（積雪約%dcm）／棚 %s／床 %s"
                    % (_nm(v["屋根"]), v["積雪cm"], _nm(v["棚"]), _nm(v["床"])))
        order = [k for k in ("一般型", "積雪型", "豪雪型") if k in y]
        # 型区分どうしは「・」、屋根／棚／床のあいだは「／」。
        # 両方を「／」でつなぐと、どこまでが屋根の値か読めなくなる。
        roof = "・".join("%s %s（積雪約%dcm）" % (k, _nm(y[k]["屋根"]), y[k]["積雪cm"])
                         for k in order)
        base = y[order[0]]
        if "棚" not in base:
            return ("屋根の耐荷重", roof)
        return ("耐荷重", "屋根 %s／棚 %s／床 %s"
                % (roof, _nm(base["棚"]), _nm(base["床"])))

    i = d["inaba"]["シリーズ"].get(pid)
    if i:
        order = [k for k in ("一般型", "多雪型", "豪雪型") if k in i]
        if order:
            return ("積雪強度", "／".join("%s %s" % (k, _nm(i[k])) for k in order))
        if "値" in i:
            return ("積雪強度",
                    "・".join(_nm(v) for v in i["値"])
                    + "（どの型番がどれに当たるかは公式に記載がありません）")
    return None


def load_style():
    s = open(os.path.join(ROOT, "products", "index.html"), encoding="utf-8").read()
    i = s.find("<style"); j = s.find("</style>") + len("</style>")
    return s[i:j]


EXTRA_CSS = """
<style>
    @media (max-width: 520px) {
    .tbl { font-size: 13px; }
    .tbl td.na { color:var(--mute); font-size:12px; }
  .tbl th, .tbl td { padding: 10px 5px; }
  }
  /* 列の多い表が画面からはみ出し、ページごと横にずれるのを防ぐ。
     2026-10-19 に 400px から 860px へ広げた。サイズ帯の表に内寸と開口の2列を足したところ、
     414〜768px でページが横スクロールしていた。列の少ない表は、はみ出さないかぎり見た目は変わらない */
  @media (max-width: 860px) {
    .tbl { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }
    /* 横に流れる表では、文字を折り返さない。
       折り返すとシリーズ名が1文字ずつ縦に並んで、かえって読めなくなる */
    .tbl th, .tbl td { white-space: nowrap; }
  }
/* TAPTARGET */

  /* ───── タップの的を24px以上に（WCAG 2.2 / 2.5.8）───── */
  .crumbs a, .footer-meta a, .header-link,
  .tbl td.l a, .sizes td a, h2 > a, h3 > a,
  dd > a, .codes-list a { display: inline-flex; align-items: center; min-height: 24px; }
  .crumbs { line-height: 2; }
  .crumbs { margin:28px 0 0; font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:.18em; color:var(--mute); }
  .crumbs a { text-decoration:none; border-bottom:1px solid var(--linesoft); }
  .crumbs a:hover { color:var(--rust); border-bottom-color:currentColor; }
  .crumbs span { margin:0 8px; color:#bababa; }
  .note { margin:22px 0 0; padding:18px 20px; border:1px solid var(--linesoft); background:#f4f4f4; font-size:14px; line-height:2; }
  .note a { color:inherit; text-decoration:none; border-bottom:1px solid #bababa; }
  .note a:hover { color:var(--rust); border-bottom-color:currentColor; }
  .tbl { width:100%; border-collapse:collapse; margin:18px 0 0; font-size:14px; }
  .tbl th, .tbl td { padding:10px 8px; border-bottom:1px solid var(--linesoft); text-align:right; font-variant-numeric:tabular-nums; }
  .tbl th { font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:.12em; text-transform:uppercase; color:var(--mute); font-weight:400; border-bottom:1px solid var(--line); white-space:nowrap; }
  .tbl td.l, .tbl th.l { text-align:left; }
  .tbl td.m { font-family:'IBM Plex Mono',monospace; letter-spacing:.02em; }
  .tbl tbody tr:hover { background:#f4f4f4; }
  .tbl a { text-decoration:none; border-bottom:1px solid var(--linesoft); }
  .tbl a:hover { color:var(--rust); border-bottom-color:currentColor; }
  .grp { margin:44px 0 0; padding:14px 16px; border:1px solid var(--line); background:#f4f4f4; }
  .grp h2 { margin:0; font-family:'Shippori Mincho B1',serif; font-weight:700; font-size:17px; line-height:1.6; }
  .grp p { margin:5px 0 0; font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:.14em; color:var(--mute); }
  /* BANDAD */
  /* ───── サイズ帯のシリーズ行に置く、販売店への出口（広告） ───── */
  .band-row { display:flex; flex-wrap:wrap; align-items:baseline;
    justify-content:space-between; gap:6px 12px; }
  .band-txt { flex:1 1 auto; min-width:0; }
  .band-ad { margin-left:10px; display:inline-flex; align-items:center; gap:7px; min-height:24px;
    padding:2px 8px; border:1px solid var(--rust); color:var(--rust);
    font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:.08em;
    text-decoration:none; white-space:nowrap; }
  .band-ad b { font-weight:500; }
  .band-ad:hover { background:var(--rust); color:#fff; }
  .grp a { text-decoration:none; border-bottom:1px solid var(--linesoft); }
  .grp a:hover { color:var(--rust); }
  /* GRPD */
  /* ───── 型番索引：シリーズごとに畳む（tools/build-codes.py が生成） ───── */
  .grpd { margin:0; }
  .grpd > summary { display:block; cursor:pointer; position:relative; list-style:none; }
  .grpd > summary::-webkit-details-marker { display:none; }
  .grpd > summary:hover { background:#ececec; }
  .grpd > summary:focus-visible { outline:2px solid var(--ink); outline-offset:2px; }
  .grpd .grpd-mk { display:block; margin:8px 0 0; font-family:'IBM Plex Mono',monospace;
    font-size:11px; letter-spacing:.14em; text-transform:uppercase; }
  .grpd > summary .grpd-mk::after { content:'＋ ひらく'; }
  .grpd[open] > summary .grpd-mk::after { content:'− たたむ'; }
  .grpd-in { padding:0 0 4px; }
  .grpd-to { margin:18px 0 0; font-size:14px; }
  .grpd-to a { text-decoration:none; border-bottom:1px solid var(--linesoft); }
  .grpd-to a:hover { color:var(--rust); }
  .grpd-bar { margin:26px 0 0; padding:14px 16px; border:1px solid var(--line);
    display:flex; flex-wrap:wrap; gap:12px 20px; align-items:center; justify-content:space-between; }
  .grpd-note { margin:0; font-size:13px; line-height:1.9; color:var(--mute); }
  .grpd-all { flex:none; border:1px solid var(--ink); background:var(--ink); color:var(--paper);
    padding:9px 16px; min-height:24px; cursor:pointer; border-radius:0;
    font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:.14em; text-transform:uppercase; }
  .grpd-all:hover { background:var(--paper); color:var(--ink); }
  .jump a { position:relative; }
  .jump-n { display:block; margin-top:3px; font-family:'Shippori Mincho B1',serif;
    font-size:11px; letter-spacing:0; color:var(--mute); }
  .jump a:hover .jump-n { color:inherit; }
  @media (min-width:768px){
    .grpd > summary { padding-right:104px; }
    .grpd .grpd-mk { position:absolute; right:16px; top:14px; margin:0; }
  }
  .jump { margin:26px 0 0; display:flex; flex-wrap:wrap; gap:8px; }
  .jump a { border:1px solid var(--line); padding:7px 12px; font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:.08em; text-decoration:none; }
  .jump a:hover { background:var(--ink); color:var(--paper); }
  .links { margin:40px 0 0; display:flex; flex-wrap:wrap; gap:10px; }
  .links a { border:1px solid var(--line); padding:9px 14px; font-size:13px; text-decoration:none; }
  .links a:hover { background:var(--ink); color:var(--paper); }
  .links a.is-here { background:var(--ink); color:var(--paper); pointer-events:none; }
  .cta { margin:40px 0 0; padding:34px 26px; border:1px solid var(--line); background:#f4f4f4; }
  .cta-label { margin:0; font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:.2em; text-transform:uppercase; color:var(--rust); }
  .cta-title { margin:16px 0 0; font-family:'Shippori Mincho B1',serif; font-weight:800; font-size:clamp(1.25rem,4vw,1.6rem); line-height:1.7; }
  .cta-text { margin:16px 0 0; font-size:14px; line-height:2.1; color:var(--mute); }
  .cta-btn { display:inline-flex; align-items:center; gap:14px; margin:26px 0 0; font-family:'Shippori Mincho B1',serif; font-weight:700; font-size:18px; text-decoration:none; border-bottom:1px solid var(--ink); padding-bottom:4px; }
  .cta-btn .arrow { font-family:'IBM Plex Mono',monospace; transition:transform .3s cubic-bezier(.22,1,.36,1); }
  .cta-btn:hover { color:var(--rust); border-bottom-color:var(--rust); }
  .cta-btn:hover .arrow { transform:translateX(10px); }
  .sec-h { margin:48px 0 0; font-family:'Shippori Mincho B1',serif; font-weight:700; font-size:clamp(1.05rem,3.2vw,1.3rem); line-height:1.7; padding-bottom:12px; border-bottom:1px solid var(--line); }
  .sec-p { margin:16px 0 0; font-size:14px; line-height:2.1; color:var(--mute); }
  .sec-p a { color:inherit; text-decoration:none; border-bottom:1px solid var(--linesoft); }
  .sec-p a:hover { color:var(--rust); border-bottom-color:currentColor; }
  .sec-p + .links { margin-top:20px; }
  .fine { margin:44px 0 0; padding-top:18px; border-top:1px solid var(--linesoft); font-size:11px; line-height:1.9; color:var(--mute); }
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
<meta name="theme-color" content="#161616">
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
