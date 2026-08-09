#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""型番から引ける索引（products/codes.html）を作る。

見積書や既存の物置に書かれた型番から、寸法とシリーズに辿り着けるようにする。
型番はカタログにしか載っていないことが多く、Web上で引ける場所が少ない。
データは index.html の PRODUCTS が唯一の出典。
"""
import importlib.util, json, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

OUT = os.path.join(C.ROOT, "products", "codes.html")


def build():
    prods = C.load_products()
    groups = []
    total = 0
    for p in sorted(prods, key=lambda x: (x["maker"], x["name"])):
        if not p["sizes"]:
            continue
        pre = sorted({re.match(r"^[A-Za-z]+", c).group(0) for c, *_ in p["sizes"]
                      if re.match(r"^[A-Za-z]+", c)})
        groups.append((p, pre))
        total += len(p["sizes"])
    groups.sort(key=lambda g: g[1][0] if g[1] else "zz")

    jump = "".join('<a href="#%s">%s</a>' % (g[0]["id"], C.esc("／".join(g[1]) or g[0]["name"]))
                   for g in groups)

    body_parts = []
    for p, pre in groups:
        head = ('<div class="grp" id="%s"><h2>%s</h2><p>%s — %s — %d型番%s</p></div>'
                % (p["id"],
                   ('<a href="%s">%s</a>' % (os.path.basename(p["page"]), C.esc(p["name"])))
                   if p["page"] else C.esc(p["name"]),
                   C.MAKER_JP[p["maker"]], C.esc(C.KUBUN.get(p["cat"], p["cat"])), len(p["sizes"]),
                   "（型番の頭：" + "／".join(pre) + "）" if pre else ""))
        rows = "".join(
            '<tr><td class="l m">%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
            % (C.esc(c), "{:,}".format(w), "{:,}".format(d), "{:,}".format(h))
            for c, w, d, h in sorted(p["sizes"], key=lambda s: s[0]))
        body_parts.append(head +
                          '<table class="tbl"><thead><tr><th class="l">型番</th>'
                          '<th>間口 mm</th><th>奥行 mm</th><th>高さ mm</th></tr></thead>'
                          '<tbody>%s</tbody></table>' % rows)

    h1 = "型番から探す（全%d型番）" % total
    desc = ("タクボ・イナバ・ヨドコウの物置 全%d型番の索引です。見積書やカタログに書かれた型番から、"
            "間口・奥行・高さとシリーズを引けます。" % total)
    url = C.SITE + "products/codes.html"

    body = """
    <div class="page-head">
      <p class="page-kicker">Model Codes — 型番から探す</p>
      <h1 class="page-title">型番から探す。</h1>
      <p class="page-lead">見積書に書かれている記号、いま使っている物置に貼ってある型番。<b>それが何のシリーズで、どんな寸法なのか</b>を引くための索引です。タクボ・イナバ・ヨドコウの<b>全%(total)d型番</b>を、シリーズごとにまとめています。</p>
    </div>

    <div class="note">
      <p style="margin:0">※型番の頭の英字でシリーズが分かります。たとえば <b>GP</b> はタクボのグランプレステージ ジャンプ、<b>FS</b> はイナバのフォルタ、<b>LMD</b> はヨドコウのエルモです。下のボタンから飛べます。</p>
      <p style="margin:14px 0 0">※<b>各社で数字の付け方が似ていても、実際の寸法は同じではありません。</b>たとえば型番に「2215」を含むものは3社にありますが、間口は2,200／2,210／2,220mm、奥行は1,530〜1,590mmと差があります。<b>買い替えのときは、型番の数字ではなく実寸で確認してください。</b></p>
      <p style="margin:14px 0 0">※寸法は各メーカーの公表値をもとにしています。ご購入前に必ず公式サイト・最新カタログでご確認ください。</p>
    </div>

    <div class="jump">%(jump)s</div>

%(groups)s

    <div class="cta">
      <p class="cta-label">Next — 次に</p>
      <p class="cta-title">型番が分かったら。</p>
      <p class="cta-text">シリーズごとの仕様は製品ページに、置ける寸法から絞り込む一覧は「寸法から探す」にまとめています。廃盤になった物置は別ページに記録しています。</p>
      <a class="cta-btn" href="./">製品一覧を見る <span class="arrow">→</span></a>
    </div>

    <div class="links">
      <a href="./">製品一覧</a>
      <a href="../size/">寸法から探す</a>
      <a href="discontinued.html">廃盤・生産終了</a>
      <a href="../#shindan">物置マッチング診断</a>
    </div>
""" % dict(total=total, jump=jump, groups="\n".join(body_parts))

    coll = {"@context": "https://schema.org", "@type": "CollectionPage", "name": h1,
            "description": desc, "url": url, "inLanguage": "ja",
            "isPartOf": {"@type": "WebSite", "name": C.NAME, "url": C.SITE},
            "publisher": {"@type": "Organization", "name": C.NAME}}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "トップ", "item": C.SITE},
        {"@type": "ListItem", "position": 2, "name": "製品", "item": C.SITE + "products/"},
        {"@type": "ListItem", "position": 3, "name": "型番から探す"}]}

    html = C.shell(h1, desc, url, "../",
                   '<a href="../">トップ</a><span>/</span><a href="./">製品</a><span>/</span>型番から探す',
                   body, C.load_style(),
                   [json.dumps(coll, ensure_ascii=False, indent=2),
                    json.dumps(crumb, ensure_ascii=False, indent=2)])

    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
    if old != html:
        open(OUT, "w", encoding="utf-8").write(html)
        print("[型番] products/codes.html を更新しました（%d型番 / %dシリーズ）" % (total, len(groups)))
    else:
        print("[型番] 変更はありません（%d型番）" % total)


if __name__ == "__main__":
    build()
