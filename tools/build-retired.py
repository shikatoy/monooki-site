#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取り下げた記事のURLに、取り下げた旨のページを置く。

記事を取り下げたあと、そのURLは404のまま残っていた。
Search Console で見ると、2026年8月〜10月の3か月で
水平出しの記事に44回、組みやすさの記事に41回（うち2クリック）の表示が立っていた。
来た人が行き止まりに当たる状態だったので、理由と行き先を書いたページを置く。

・URLは取り下げる前と同じ。中身を元に戻すわけではない
・なぜ扱わないのかを書く。サイトの方針そのものなので、読者にとっても判断材料になる
・寸法に関わる部分だけは、どこに書いてあるかを示す
・記事一覧のカードは作らない（取り下げた記事なので）
"""
import importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

MARK = "<!-- RETIRED_PAGE -->"

# slug: (見出し, 取り下げた理由の段落, 行き先 [(ラベル, URL)])
PAGES = {
 "monooki-level-blocks": (
   "水平出しの記事は取り下げました",
   ["この記事では、物置の水平出しを主題にしていました。当サイトは、組み立ても設置も業者に任せる方に向けて作っています。"
    "作業そのものの手順は、読む方がご自分でやる場面を前提にした内容になるため、主題から外しました。",
    "ただし、<b>寸法に関わる部分は残しています。</b>本体の下には基礎用コンクリートブロック（基本 高さ約10cm）を敷くため、"
    "実際の高さは「本体高さ＋約10cm」になります。窓下や軒下など高さに制限のある場所では、ここが効いてきます。"
    "各サイズ帯のページに同じ注記を入れています。"],
   [("寸法から探す", "../size/"), ("物置が置けない場所と置きにくい場所", "monooki-okenai-basho.html"),
    ("記事一覧", "./")]),
 "monooki-maker-assembly": (
   "組みやすさの記事は取り下げました",
   ["この記事では、メーカーごとの組みやすさを、小型と中型・大型に分けて比べていました。"
    "当サイトの方針に二つの点で合わなくなったため、取り下げました。",
    "ひとつは、組み立てを記事の主題にしないこと。もうひとつは、「小型」と「中型・大型」の区分を記事の軸にしないことです。"
    "区分はメーカーごとに切り方が違い、同じ言葉が同じ大きさを指しません。いまは寸法そのもので比べる形にしています。"],
   [("物置の小型と中型・大型は何が違う？", "kogata-chugata-ogata-chigai.html"),
    ("寸法から探す", "../size/"), ("記事一覧", "./")]),
 "monooki-diy-assembly": (
   "自分で組み立てる話は扱っていません",
   ["この記事では、物置をご自分で組み立てられるかを扱っていました。"
    "当サイトは、組み立ても設置も業者に任せる方に向けて作っているため、主題から外しました。",
    "いま出しているのは、寸法・扉の形・鋼板・屋根の形といった、頼む前に決める部分の判断材料です。"],
   [("記事一覧", "./"), ("寸法から探す", "../size/"), ("製品一覧", "../products/")]),
 "monooki-diy-tools": (
   "組み立てに使う道具の話は扱っていません",
   ["この記事では、物置をご自分で組むときに必要な道具を扱っていました。"
    "当サイトは、組み立ても設置も業者に任せる方に向けて作っているため、主題から外しました。"],
   [("記事一覧", "./"), ("寸法から探す", "../size/"), ("製品一覧", "../products/")]),
 "inaba-yodo-takubo-monooki-compare": (
   "3社の比較は、記事ではなく索引と診断にまとめました",
   ["この記事では、イナバ・ヨドコウ・タクボの3社を文章で比べていました。"
    "どのメーカーが良いという書き方になりやすく、<b>価値判断ではなく判断材料を出す</b>というサイトの方針から外れるため、取り下げました。",
    "いまは、3社の全1,117型番を寸法で横断して絞り込める形にしています。"
    "メーカーで絞ることも、置ける寸法から絞ることもできます。"],
   [("トップ（3社から絞り込む）", "../"), ("寸法から探す", "../size/"),
    ("型番から探す", "../products/codes.html"), ("製品一覧", "../products/")]),
}


def build():
    style = C.load_style()
    n = 0
    for slug, (h1, paras, links) in sorted(PAGES.items()):
        url = C.SITE + "articles/" + slug + ".html"
        desc = paras[0].replace("<b>", "").replace("</b>", "")[:110]
        body = """
    <div class="page-head">
      <p class="page-kicker">Retired — 取り下げた記事</p>
      <h1 class="page-title">%(h1)s</h1>
    </div>

    <div class="note">
      %(paras)s
    </div>

    <h2 class="sec-h">こちらをご覧ください</h2>
    <div class="links">%(links)s</div>
""" % dict(h1=C.esc(h1),
           paras="\n      ".join('<p style="margin:%s">%s</p>' % ("0" if i == 0 else "14px 0 0", p)
                                 for i, p in enumerate(paras)),
           links="".join('<a href="%s">%s</a>' % (u, C.esc(l)) for l, u in links))

        crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "トップ", "item": C.SITE},
            {"@type": "ListItem", "position": 2, "name": "記事", "item": C.SITE + "articles/"},
            {"@type": "ListItem", "position": 3, "name": h1}]}
        html = C.shell(h1, desc, url, "../",
                       '<a href="../">トップ</a><span>/</span><a href="./">記事</a><span>/</span>' + C.esc(h1),  # 画面のパンくずと構造化データを揃える（2026-10-20）
                       body, style, [json.dumps(crumb, ensure_ascii=False, indent=2)])
        html = html.replace("<body>", "<body>\n" + MARK, 1)

        p = os.path.join(C.ROOT, "articles", slug + ".html")
        old = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        if old is not None and MARK not in old:
            print("  飛ばす（取り下げページではない実体があります）:", slug); continue
        if old != html:
            open(p, "w", encoding="utf-8").write(html)
            n += 1
    print("[取り下げページ] %d / %d ページを書きました" % (n, len(PAGES)))
    return 0


if __name__ == "__main__":
    sys.exit(build())
