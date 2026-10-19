#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
製品ページの「買える場所への出口」（エクスショップへの提携リンク）を一元管理する。

これまで各ページに手で書いていたため、次の2つが起きていた。
  ・ペインタのリンクがグランプレステージ ジャンプの一覧を指していた（複製時の直し忘れ）
  ・6ページに出口が1つも無かった（写真が無い機種は後回しにしたまま）

このスクリプトは下の DEST 表だけを正とする。
  ・既にリンクがあるページ → href だけ書き換える（見た目・文言は触らない）
  ・リンクが無いページ    → まとめの直前に1本だけ差し込む

    python3 tools/build-shop-links.py            # 差分を出して書き換え
    python3 tools/build-shop-links.py --check    # 書き換えずに確認だけ
"""
import os, re, sys, glob, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD = os.path.join(ROOT, "products")
SID, PID = "3777863", "892682808"
BEG, END = "<!-- AUTO_SHOP_START -->", "<!-- AUTO_SHOP_END -->"
CSSBEG, CSSEND = "/* AUTO_SHOP_CSS_START */", "/* AUTO_SHOP_CSS_END */"

# 出口が無かったページには見た目の指定も無い。既存ページと同じものを入れる
CSS = CSSBEG + """
  .shop { position:relative; display:flex; align-items:stretch; margin:32px 0 0; border:1px solid var(--line);
    background:#fff; text-decoration:none; overflow:hidden;
    transition:border-color .2s ease, box-shadow .2s ease, transform .2s ease; }
  .shop:hover { border-color:var(--rust); box-shadow:4px 4px 0 var(--rust); transform:translate(-1px,-1px); }
  .shop-txt { flex:1; min-width:0; padding:10px 14px; display:flex; flex-direction:column; justify-content:center; gap:4px; }
  .shop-lead { font-family:'Shippori Mincho B1',serif; font-weight:700; font-size:14px; line-height:1.5; }
  .shop-sub { font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:.12em; color:var(--mute); }
  .shop-sub b { color:var(--rust); }
  .shop-go { flex:0 0 46px; display:flex; align-items:center; justify-content:center;
    background:var(--rust); color:#fff; font-size:17px; transition:background .2s ease; }
  .shop:hover .shop-go { background:var(--ink); }
  .shop img[height='1'] { position:absolute; left:0; top:0; width:1px !important; height:1px !important; opacity:0; }
  .shop-none { margin:32px 0 0; padding:14px 16px; border:1px dashed var(--linesoft);
    background:#f4f4f4; font-size:13px; line-height:2; color:var(--mute); }
""" + CSSEND + "\n"

# slug → (カテゴリ, 絞り込み, 出口の文言)
#   カテゴリ  'mo'=物置・収納  'wh'=倉庫・ガレージ
#   絞り込み  ('series', コード) … シリーズ一覧
#             ('word',   語)     … 商品名で絞った一覧（シリーズが無い機種）
#             None               … カテゴリの一覧（行き先が特定できていない機種）
DEST = {
    "takubo-grand-prestage-jump": ("mo", ("series", "takubo_s13"), "グランプレステージ ジャンプ"),
    "takubo-mr-stockman-dandy":   ("mo", ("series", "takubo_s2"),  "Mr.ストックマンダンディ"),
    "takubo-mr-tallman-dandy":    ("mo", ("series", "takubo_s6"),  "Mr.トールマンダンディ"),
    "takubo-belos":               ("mo", ("series", "takubo_s28"), "BELOS"),
    "takubo-leisure":             ("mo", ("series", "takubo_s29"), "リジュー"),
    "takubo-peinte":              ("mo", ("word",   "ペインタ"),    "ペインタ"),
    "inaba-simply":               ("mo", ("series", "inaba_s2"),   "シンプリー"),
    "inaba-forta":                ("mo", ("series", "inaba_s12"),  "FORTA"),
    "inaba-nyso-smx":             ("mo", ("word",   "ナイソーSMX"), "ナイソー SMX"),
    "inaba-garudia":              ("wh", ("series", "inaba_s3"),   "ガレーディア"),
    "inaba-bike-hokanko":         ("wh", ("series", "inaba_s9"),   "バイク保管庫"),
    "yodoko-esmo":                ("mo", ("series", "yodoko_s1"),  "エスモ"),
    "yodoko-elmo":                ("mo", ("series", "yodoko_s3"),  "エルモ"),
}

# エクスショップ側に、そのシリーズの一覧を確認できなかったもの。
# 2026-10-19 まではカテゴリの一覧（物置だけで1,597件）へ逃がしていたが、
# 押した先で目当ての機種が出てこないので、リンクを置かないことにした。
#   ・アルシアフィット … 「アルシア 一般型／豪雪地型」はあるが、アルシアフィットは見当たらない
#   ・como lite／宅配ボックス … イナバの物置シリーズ一覧（10件）に無い
#   ・バイクシャッターマン／エルモシャッター … シリーズ一覧に見当たらない
# 見つかったら DEST に ('series', '…') か ('word', '…') で足せばよい。
NO_DEST = {
    "inaba-arcia-fit", "inaba-como-lite", "inaba-takuhai-box",
    "takubo-bike-shutterman", "yodoko-elmo-shutter",
    # 下の3つは、手で書いた「カテゴリ一覧へ」のリンクだけが残っていた
    "inaba-forta-large", "inaba-forta-tall", "takubo-mr-shutterman",
}

NOTE = ('<p class="shop-none">提携先の販売店では、このシリーズの一覧を確認できていません。'
        'このページでは販売店への案内を出していません。メーカー公式の商品ページは上のリンクから開けます。</p>')

CAT_LABEL = {"mo": "物置・収納", "wh": "倉庫・ガレージ"}


def dest_url(cat, filt):
    act = "public_item_%s_search_execute" % cat
    q = "action=" + act
    if filt and filt[0] == "series":
        q += "&se_series=" + urllib.parse.quote("series:" + filt[1], safe="")
    elif filt and filt[0] == "word":
        q += "&search_word_like_ex=" + urllib.parse.quote(filt[1], safe="")
    return "https://www.ex-shop.net/index.php?" + q


def vc(url):
    return ("//ck.jp.ap.valuecommerce.com/servlet/referral?sid=%s&pid=%s&vc_url=%s"
            % (SID, PID, urllib.parse.quote(url, safe="")))


def block(cat, filt, name):
    lead = ("%sの価格・無料見積もりを見る" % name if name
            else "エクスショップで%sを探す" % CAT_LABEL[cat])
    return (BEG + '<a class="shop" href="%s" rel="nofollow sponsored" target="_blank">'
            '<span class="shop-txt"><span class="shop-lead">%s</span>'
            '<span class="shop-sub"><b>広告</b> — エクスショップ（提携先）</span></span>'
            '<span class="shop-go" aria-hidden="true">→</span>'
            '<img src="//ad.jp.ap.valuecommerce.com/servlet/gifbanner?sid=%s&pid=%s" '
            'height="1" width="0" border="0" alt=""></a>' + END
            ) % (vc(dest_url(cat, filt)), lead, SID, PID)


def resolve():
    """slug → (カテゴリ, 絞り込み, 文言)。
       index.html の EXSHOP を先に見て、無いものだけ DEST で補う。
       2026-10-19 まで DEST だけを見ていたため、EXSHOP にある9シリーズ
       （ナイソーシスター・アイビーストッカーなど）の製品ページだけ出口が無かった"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import _common_page as C
    out = {k: v for k, v in DEST.items() if k not in NO_DEST}
    ex = C.load_exshop()
    for p in C.load_products():
        code = ex.get(p["id"])
        if not code or not p.get("page"):
            continue
        slug = os.path.basename(p["page"])[:-5]
        cat = "wh" if code.startswith("wh:") else "mo"
        out[slug] = (cat, ("series", code[3:] if code.startswith("wh:") else code), p["name"])
    return out


def main():
    check = "--check" in sys.argv
    changed = 0
    table = resolve()
    for f in sorted(glob.glob(os.path.join(PROD, "*.html"))):
        slug = os.path.basename(f)[:-5]
        if slug in NO_DEST and slug not in table:
            s = orig = open(f, encoding="utf-8").read()
            s = re.sub(re.escape(BEG) + r".*?" + re.escape(END) + r"\s*", "", s, flags=re.S)
            # 自動生成ではない、手で書かれた提携リンクも外す。
            # 行き先がカテゴリ全体の一覧になっていて、目当ての機種に着かないため。
            # エルモシャッターのページは、ここでエルモの写真（YDMO320071）も一緒に外れる。
            # 扉の形が違う機種の写真が「エルモシャッター」として出ていた（2026-10-19）
            s = re.sub(r'<a[^>]*ck\.jp\.ap\.valuecommerce[^>]*>.*?</a>\s*', "", s, flags=re.S)
            if 'class="shop-none"' not in s and '<aside class="cta">' in s:
                s = s.replace('<aside class="cta">', BEG + NOTE + END + "\n\n        " +
                              '<aside class="cta">', 1)
            # 但し書きの見た目が無いページには入れる
            if 'class="shop-none"' in s and ".shop-none {" not in s and "</style>" in s:
                s = re.sub(re.escape(CSSBEG) + r".*?" + re.escape(CSSEND) + r"\n?", "", s, flags=re.S)
                s = s.replace("</style>", CSS + "</style>", 1)
            if s != orig:
                changed += 1
                if not check:
                    open(f, "w", encoding="utf-8").write(s)
                print("  %-32s 行き先を確認できないので案内を外した" % slug[:30])
            continue
        if slug not in table:
            continue
        cat, filt, name = table[slug]
        s = orig = open(f, encoding="utf-8").read()
        href = vc(dest_url(cat, filt))

        # 既にあるリンクは href だけ差し替える（文言・写真はそのまま）
        n = len(re.findall(r'href="//ck\.jp\.ap\.valuecommerce\.com[^"]*"', s))
        if n:
            s = re.sub(r'href="//ck\.jp\.ap\.valuecommerce\.com[^"]*"',
                       'href="%s"' % href.replace("\\", "\\\\"), s)
            note = "href を %d 本そろえた" % n
        else:
            # 出口が無いページ → まとめ（aside.cta）の直前に1本入れる
            s = re.sub(re.escape(BEG) + r".*?" + re.escape(END) + r"\s*", "", s, flags=re.S)
            anchor = '<aside class="cta">'
            if anchor not in s:
                print("  飛ばす（差し込み位置が無い）:", slug); continue
            s = s.replace(anchor, block(cat, filt, name) + "\n\n        " + anchor, 1)
            note = "出口を新しく入れた" + ("" if name else "（カテゴリ一覧へ）")

        # 見た目の指定が無いページには入れる（出口だけあって崩れるのを防ぐ）
        if 'class="shop"' in s and ".shop {" not in s and "</style>" in s:
            s = s.replace("</style>", CSS + "</style>", 1)
            note += "／見た目の指定も入れた"

        if s != orig:
            changed += 1
            if not check:
                open(f, "w", encoding="utf-8").write(s)
            print("  %-32s %s" % (slug[:30], note))
    print("[製品ページの出口] %d ページ%s" % (changed, "（確認のみ）" if check else "を更新"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
