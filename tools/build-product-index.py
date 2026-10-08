#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
製品一覧ページ（products/index.html）のカードを、index.html の PRODUCTS から作り直す。

手で並べていたため、製品を足しても一覧に出てこなかった。
2026-10-06 時点で実際に落ちていたもの：
  ・エルモシャッター（10/05 に追加）が一覧に無い
  ・型番数が「エスモ 5型番」「Mr.ストックマン 7型番」など、古いまま
check-links.py はリンク切れを見るので、「載っていない」ことは止められない。

    python3 tools/build-product-index.py
"""
import importlib.util, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

PAGE = os.path.join(C.ROOT, "products", "index.html")
MK_ORDER = ["takubo", "inaba", "yodoko"]
# 区分の並び。ここに無い区分は末尾にまわし、注意を出す
ORDER = ["小型物置", "中型物置", "中・大型物置", "大型物置",
         "駐輪スペース付き物置", "断熱物置",
         "ドア型収納庫", "タイヤ収納庫", "宅配ボックス", "バイク車庫", "ガレージ"]

HEAD = ('      <li class="card" style="border:0;padding:0;margin-top:48px">'
        '<p class="card-date" style="font-size:11px">%s</p></li>')
CARD = """      <li class="card">
        <a class="card-inner" href="%(slug)s">
          <span class="card-date">%(maker)s<span class="card-tag">%(tag)s</span></span>
          <h2 class="card-title">%(name)s</h2>
          <p class="card-desc">%(desc)s</p>
          <span class="card-more">サイズと仕様を見る <span class="arrow">→</span></span>
        </a>
      </li>"""


def base_of(raw):
    m = re.search(r"base:'((?:[^'\\]|\\.)*)'", raw)
    return m.group(1).replace("\\'", "'") if m else ""


def raws():
    s = io.open(os.path.join(C.ROOT, "index.html"), encoding="utf-8").read()
    i = s.index("const PRODUCTS"); i = s.index("[", i)
    out, depth, st = {}, 0, None
    for k in range(i, len(s)):
        ch = s[k]
        if ch == "{":
            if depth == 0: st = k
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                e = s[st:k + 1]
                m = re.match(r"\{ id:'([^']+)'", e)
                if m: out[m.group(1)] = e
        elif ch == "]" and depth == 0:
            break
    return out


def main():
    src = raws()
    prods = [p for p in C.load_products() if p["page"]]
    cats = sorted({p["cat"] for p in prods},
                  key=lambda c: (ORDER.index(c) if c in ORDER else len(ORDER), c))
    for c in cats:
        if c not in ORDER:
            print("[注意] 並び順の決まっていない区分です: %s。"
                  "tools/build-product-index.py の ORDER に足してください。" % c)

    out = [""]
    for cat in cats:
        out.append(HEAD % C.esc(cat))
        group = [p for p in prods if p["cat"] == cat]
        group.sort(key=lambda p: (MK_ORDER.index(p["maker"]) if p["maker"] in MK_ORDER
                                  else len(MK_ORDER), p["name"]))
        for p in group:
            raw = src.get(p["id"], "")
            n = len(p["sizes"])
            tag = ("全%d型番" % n) if "sizesComplete:true" in raw else ("%d型番を掲載" % n)
            if not n:
                tag = "サイズ表は未公開"
            out.append(CARD % dict(
                slug=os.path.basename(p["page"]), maker=C.MAKER_JP[p["maker"]],
                tag=C.esc(tag), name=C.esc(p["name"]), desc=C.esc(base_of(raw))))
        out.append("")

    s = io.open(PAGE, encoding="utf-8").read()
    i = s.index('<ul class="card-list">') + len('<ul class="card-list">')
    j = s.rindex("</ul>")
    s2 = s[:i] + "\n".join(out) + "    " + s[j:]
    # リード文の製品数も合わせる
    s2, k = re.subn(r"全\d+製品です", "全%d製品です" % len(prods), s2, count=1)
    if k != 1:
        print("[注意] リード文の製品数を見つけられませんでした。products/index.html を確認してください。")
    if s2 != s:
        io.open(PAGE, "w", encoding="utf-8").write(s2)
    print("[製品一覧] %d 製品 / %d 区分 を書き出しました" % (len(prods), len(cats)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
