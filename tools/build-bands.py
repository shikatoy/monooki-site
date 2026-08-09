#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同じサイズ帯で3メーカーを並べるページ（size/band-*.html）を作る。

各社の実寸は少しずつ違うため、そのままでは並べて比べられない。
間口・奥行を300mm刻みの帯にまとめて、同じ帯に入る型番を横並びにする。
2メーカー以上・5型番以上の帯だけをページにする。
"""
import importlib.util, json, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

OUTD = os.path.join(C.ROOT, "size")
STEP = 300
MIN_MAKERS = 2
MIN_CODES = 5


def m(v):
    return ("%.1f" % (v / 1000.0)).rstrip("0").rstrip(".")


def collect():
    rows = []
    for p in C.load_products():
        if p["cat"] not in C.CAT_OK:
            continue
        for c, w, d, h in p["sizes"]:
            rows.append(dict(maker=p["maker"], name=p["name"], page=p["page"], cat=p["cat"],
                             code=c, w=w, d=d, h=h))
    band = defaultdict(list)
    for r in rows:
        band[(r["w"] // STEP * STEP, r["d"] // STEP * STEP)].append(r)
    out = []
    for k, v in band.items():
        mk = {x["maker"] for x in v}
        if len(mk) >= MIN_MAKERS and len(v) >= MIN_CODES:
            out.append((k, v, mk))
    out.sort(key=lambda x: (-len(x[2]), -len(x[1])))
    return out


def build():
    bands = collect()
    style = C.load_style()
    cards = []
    for (bw, bd), rows, mks in bands:
        slug = "band-w%d-d%d" % (bw // 10, bd // 10)
        title = "間口%s〜%sm × 奥行%s〜%sm の物置" % (m(bw), m(bw + STEP), m(bd), m(bd + STEP))
        h1 = title + "を%dメーカーで比べる" % len(mks)
        url = C.SITE + "size/" + slug + ".html"
        ws = sorted({r["w"] for r in rows}); ds = sorted({r["d"] for r in rows})
        desc = ("間口%s〜%sm・奥行%s〜%smに収まる物置を、タクボ・イナバ・ヨドコウ%dメーカー%d型番で並べました。"
                "実寸は各社で違うため、間口・奥行・高さを横並びで比べられます。"
                % (m(bw), m(bw + STEP), m(bd), m(bd + STEP), len(mks), len(rows)))

        trs = "".join(
            '<tr><td class="l">%s</td><td class="l">%s</td><td class="l m">%s</td>'
            '<td>%s</td><td>%s</td><td>%s</td></tr>'
            % (C.MAKER_JP[r["maker"]],
               ('<a href="../%s">%s</a>' % (r["page"], C.esc(r["name"]))) if r["page"] else C.esc(r["name"]),
               C.esc(r["code"]), "{:,}".format(r["w"]), "{:,}".format(r["d"]), "{:,}".format(r["h"]))
            for r in sorted(rows, key=lambda r: (C.MAKER_JP[r["maker"]], r["w"], r["d"], r["h"])))

        per = defaultdict(list)
        for r in rows:
            per[(r["maker"], r["name"], r["page"])].append(r)
        sums = "".join(
            "<p><b>%s %s</b> — %d型番／間口 %s mm・奥行 %s mm</p>"
            % (C.MAKER_JP[k[0]], C.esc(k[1]), len(v),
               "・".join("{:,}".format(x) for x in sorted({r["w"] for r in v})),
               "・".join("{:,}".format(x) for x in sorted({r["d"] for r in v})))
            for k, v in sorted(per.items(), key=lambda x: -len(x[1])))

        nav = "".join(
            '<a href="band-w%d-d%d.html"%s>間口%s〜%sm × 奥行%s〜%sm</a>'
            % (k[0] // 10, k[1] // 10,
               ' class="is-here"' if (k[0], k[1]) == (bw, bd) else "",
               m(k[0]), m(k[0] + STEP), m(k[1]), m(k[1] + STEP))
            for k, _, _ in bands)

        body = """
    <div class="page-head">
      <p class="page-kicker">Size Class — サイズ帯で比べる</p>
      <h1 class="page-title">%(h1)s</h1>
      <p class="page-lead">この大きさで置きたい、と決まっている方へ。<b>%(nm)dメーカー%(nc)d型番</b>を横並びにしました。</p>
    </div>

    <div class="note">
      <p style="margin:0"><b>各社の実寸は同じではありません。</b>この帯に入る間口は %(ws)s mm、奥行は %(ds)s mm と幅があります。カタログの見出しが近くても、<b>数十mm単位で違います。</b>置き場所に余裕がないときは、この差が効いてきます。</p>
      <p style="margin:14px 0 0">※本体の下には基礎用コンクリートブロック（基本 高さ約10cm）を敷きます。<b>実際の高さは「本体高さ＋約10cm」</b>になります。</p>
      <p style="margin:14px 0 0">※この一覧は<b>物置のみ</b>です。車庫・ガレージ・バイク保管庫は含めていません。寸法は各メーカーの公表値をもとにしています。ご購入前に必ず公式サイト・最新カタログでご確認ください。</p>
    </div>

    <div class="grp" style="background:#fffdf9">%(sums)s</div>

    <table class="tbl">
      <thead><tr><th class="l">メーカー</th><th class="l">シリーズ</th><th class="l">型番</th><th>間口 mm</th><th>奥行 mm</th><th>高さ mm</th></tr></thead>
      <tbody>%(trs)s</tbody>
    </table>

    <div class="links">%(nav)s</div>

    <div class="cta">
      <p class="cta-label">Next — 次に</p>
      <p class="cta-title">大きさは同じでも、中身は違います。</p>
      <p class="cta-text">扉の開き方、鋼板、屋根の形はシリーズごとに違います。収納したい物や使い方から絞り込むこともできます。質問は3〜4問、1分ほどです。</p>
      <a class="cta-btn" href="../#shindan">診断をはじめる <span class="arrow">→</span></a>
    </div>

    <div class="links">
      <a href="./">寸法から探す</a>
      <a href="../products/">製品一覧</a>
      <a href="../products/codes.html">型番から探す</a>
      <a href="../products/discontinued.html">廃盤・生産終了</a>
    </div>
""" % dict(h1=C.esc(h1), nm=len(mks), nc=len(rows), sums=sums, trs=trs, nav=nav,
           ws="・".join("{:,}".format(x) for x in ws),
           ds="・".join("{:,}".format(x) for x in ds))

        coll = {"@context": "https://schema.org", "@type": "CollectionPage", "name": h1,
                "description": desc, "url": url, "inLanguage": "ja",
                "isPartOf": {"@type": "WebSite", "name": C.NAME, "url": C.SITE},
                "publisher": {"@type": "Organization", "name": C.NAME}}
        crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "トップ", "item": C.SITE},
            {"@type": "ListItem", "position": 2, "name": "寸法から探す", "item": C.SITE + "size/"},
            {"@type": "ListItem", "position": 3, "name": title}]}

        html = C.shell(h1, desc, url, "../",
                       '<a href="../">トップ</a><span>/</span><a href="./">寸法から探す</a><span>/</span>'
                       + C.esc(title),
                       body, style,
                       [json.dumps(coll, ensure_ascii=False, indent=2),
                        json.dumps(crumb, ensure_ascii=False, indent=2)])
        path = os.path.join(OUTD, slug + ".html")
        old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if old != html:
            open(path, "w", encoding="utf-8").write(html)
        print("  %-18s %d社 / %3d型番  %s" % (slug, len(mks), len(rows), title))
        cards.append(dict(slug=slug, title=title, n=len(rows), nm=len(mks),
                          lead="タクボ・イナバ・ヨドコウ%dメーカー%d型番。実寸の違いを横並びで比べられます。"
                               % (len(mks), len(rows))))
    json.dump(cards, open(os.path.join(HERE, "_bands.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("[サイズ帯] %d ページ" % len(bands))
    return cards


if __name__ == "__main__":
    build()
