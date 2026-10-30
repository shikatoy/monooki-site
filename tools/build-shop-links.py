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

# エクスショップ側に、その機種を確認できなかったもの。
# 2026-10-19 まではカテゴリの一覧（物置だけで1,597件）へ逃がしていたが、
# 押した先で目当ての機種が出てこないので、リンクを置かないことにした。
#   ・宅配ボックス（TBJ） … 先方に見当たらない
#   ・エルモシャッター … 先方にあるのはブラックエルモシャッター40件だけで、黒以外は見当たらない
#   ・フォルタ大型（FB） … 先方のFORTA一覧にある幅3,580〜5,260mmの18件は、
#                          寸法を突き合わせると全てフォルタ（FS-3618H〜FS-5218H）
#   ・フォルタ縦長大型（FT） … 奥行3,580mm以上が先方に無い
# 見つかったら index.html の EXSHOP に足せばよい（ここに書く必要はない）。
NO_DEST = {
    "inaba-takuhai-box", "yodoko-elmo-shutter",
    "inaba-forta-large", "inaba-forta-tall",
}

NOTE = ('<p class="shop-none">提携先の販売店では、このシリーズの一覧を確認できていません。'
        'このページでは販売店への案内を出していません。メーカー公式の商品ページは上のリンクから開けます。</p>')

CAT_LABEL = {"mo": "物置・収納", "wh": "倉庫・ガレージ", "xz": "お問い合わせ商品"}


def _common():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import _common_page as C
    return C


def code_of(cat, filt):
    """DEST の書き方を、index.html の EXSHOP と同じ書き方に直す"""
    if filt is None:
        return None
    kind, val = filt
    pre = "" if cat == "mo" else cat + ":"
    return pre + ("word:" + val if kind == "word" else val)


def dest_url(cat, code):
    """行き先のURL。書き方の解釈は tools/_common_page.py の exshop_url だけが持つ。
       ここで組み立て直すと、書き方を増やしたときに必ず食い違う。
       2026-10-26 に実際そうなった。EXSHOP に 'xz:item:8161'（お問い合わせ商品の
       見積もりページ）を足したあと、このファイルだけが古い解釈のまま
       se_series=series:xz:item:8161 という行き先を書き出していた"""
    if code is None:
        return "https://www.ex-shop.net/index.php?action=public_item_%s_search_execute" % cat
    return _common().exshop_url(code)


def vc(url):
    return ("//ck.jp.ap.valuecommerce.com/servlet/referral?sid=%s&pid=%s&vc_url=%s"
            % (SID, PID, urllib.parse.quote(url, safe="")))


def lead_text(cat, code, name):
    """出口の文言。価格の出ない行き先（お問い合わせ商品）では「価格」を名乗らない。
       決まりは tools/_common_page.py の cta_text に置く（2026-10-30）"""
    return (_common().cta_text(name, code) if name
            else "エクスショップで%sを探す" % CAT_LABEL[cat])


def block(cat, code, name):
    lead = lead_text(cat, code, name)
    return (BEG + '<a class="shop" href="%s" rel="nofollow sponsored" target="_blank">'
            '<span class="shop-txt"><span class="shop-lead">%s</span>'
            '<span class="shop-sub"><b>広告</b> — エクスショップ（提携先）</span></span>'
            '<span class="shop-go" aria-hidden="true">→</span>'
            '<img src="//ad.jp.ap.valuecommerce.com/servlet/gifbanner?sid=%s&pid=%s" '
            'height="1" width="0" border="0" alt=""></a>' + END
            ) % (vc(dest_url(cat, code)), lead, SID, PID)


def resolve():
    """slug → (カテゴリ, EXSHOPの書き方, 文言)。
       index.html の EXSHOP を先に見て、無いものだけ DEST で補う。
       2026-10-19 まで DEST だけを見ていたため、EXSHOP にある9シリーズ
       （ナイソーシスター・アイビーストッカーなど）の製品ページだけ出口が無かった"""
    C = _common()
    out = {}
    for k, v in DEST.items():
        if k in NO_DEST:
            continue
        cat, filt, name = v
        out[k] = (cat, code_of(cat, filt), name)
    ex = C.load_exshop()
    for p in C.load_products():
        code = ex.get(p["id"])
        if not code or not p.get("page"):
            continue
        slug = os.path.basename(p["page"])[:-5]
        head = code.split(":")[0]
        cat = head if head in CAT_LABEL else "mo"
        out[slug] = (cat, code, p["name"])
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
        cat, code, name = table[slug]
        s = orig = open(f, encoding="utf-8").read()
        href = vc(dest_url(cat, code))

        # 既にあるリンクは href を差し替える（写真はそのまま）
        n = len(re.findall(r'href="//ck\.jp\.ap\.valuecommerce\.com[^"]*"', s))
        if n:
            s = re.sub(r'href="//ck\.jp\.ap\.valuecommerce\.com[^"]*"',
                       'href="%s"' % href.replace("\\", "\\\\"), s)
            note = "href を %d 本そろえた" % n
            # 文言もそろえる（2026-10-30）。
            # それまで href だけ差し替えていたため、文言の決まりを直しても
            # 一度入れた出口は古い言い方のまま残っていた。実際、価格の出ない
            # 行き先の5シリーズが「価格・無料見積もりを見る」のままだった。
            # 置き換えるのは出口（a.shop）の中の shop-lead だけ。
            lead = lead_text(cat, code, name)
            s, k = re.subn(r'(<span class="shop-lead">)[^<]*(</span>)',
                           lambda m: m.group(1) + lead + m.group(2), s)
            if k:
                note += "／文言を %d か所そろえた" % k
        else:
            # 出口が無いページ → まとめ（aside.cta）の直前に1本入れる
            s = re.sub(re.escape(BEG) + r".*?" + re.escape(END) + r"\s*", "", s, flags=re.S)
            anchor = '<aside class="cta">'
            if anchor not in s:
                print("  飛ばす（差し込み位置が無い）:", slug); continue
            s = s.replace(anchor, block(cat, code, name) + "\n\n        " + anchor, 1)
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
