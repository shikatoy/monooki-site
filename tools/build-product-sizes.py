#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
製品ページ（products/*.html）の「サイズ一覧」表を、index.html の PRODUCTS から作り直す。

これまで手で同期していたため、PRODUCTS を直しても製品ページが古いまま残った。
（2026-09-17：エスモを 5→90 型番に直したのに、製品ページは 5 行のままだった）

    python3 tools/build-product-sizes.py
"""
import importlib.util, os, re, io, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_s = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)

# PRODUCTS の id → products/ のファイル名。
# 2026-10-27 まで、ここに同じ表を手で持っていた。index.html の PRODUCT_PAGES と
# 二重管理になっていて、製品を足すたびに片方だけ直して止まっていた。
# （同じ型の食い違いを build-shop-links.py でも起こしている。表は1か所に持つ）
def _pages():
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    i = s.find("const PRODUCT_PAGES")
    if i < 0:
        raise SystemExit("[中止] index.html の PRODUCT_PAGES を読めませんでした")
    j = s.find("};", i)
    return {pid: os.path.basename(path)[:-5]
            for pid, path in re.findall(r"'([a-z0-9-]+)':\s*'(products/[^']+)'", s[i:j])}


PAGES = _pages()

# 表がまだ無いページに差し込むときの目印。型番0件で作ったページは
# 「サイズ一覧」の下がこの注記1行だけになっている。
PLACEHOLDER = re.compile(
    r'<p class="note">現時点でサイズ表は公開されていません。[^<]*</p>')

# サイズ表のすぐ下の注記。段落ごと作り直す（床耐荷重の列を足すと文面も変わるため）
NOTE_RE = re.compile(
    r'<p class="note">(?:(?!</p>).)*?寸法は本体の外寸（mm）です。(?:(?!</p>).)*</p>', re.S)

BASE_NOTE = ("寸法は本体の外寸（mm）です。実際の設置高さは、"
             "基礎ブロック分（基本 高さ約10cm）を足した値になります。")
KG_NOTE = ("床耐荷重はタクボ公式の型番ページに載っている値です。"
           "物置1棟あたりの合計で、面積あたりの値ではありません。")


def _table(sizes, kg):
    """サイズ表のHTML。kg が渡ったときだけ床耐荷重の列を足す。"""
    cols = '<th>型番</th><th>間口 W</th><th>奥行 D</th><th>高さ H</th>'
    if kg:
        cols += '<th>床耐荷重</th>'
    rows = []
    for c, w, d, h in sorted(sizes, key=lambda x: (x[1], x[2], x[3])):
        tds = ("<td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
               % (c, format(w, ","), format(d, ","), format(h, ",")))
        if kg:
            tds += "<td>%skg</td>" % format(kg[c], ",")
        rows.append("          <tr>%s</tr>" % tds)
    return ('<table class="sizes">\n        <thead>\n          <tr>%s</tr>\n'
            '        </thead>\n        <tbody>\n%s\n        </tbody>\n      </table>'
            % (cols, "\n".join(rows)))


def _mm(v):
    """寸法は整数mmに揃える。ヨドは図面値を .5 で出すことがあるので四捨五入する。"""
    return int(float(v) + 0.5)


def products():
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    i = s.index("const PRODUCTS"); j = s.index("];", i)
    blk = s[i:j]
    ents, depth, st = [], 0, None
    for k, ch in enumerate(blk):
        if ch == "{":
            if depth == 0: st = k
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                ents.append(blk[st:k + 1]); st = None
    out = {}
    for e in ents:
        m = re.match(r"\{ id:'([^']+)'", e)
        if not m: continue
        # 桁揃えのため空白が余分に入っている行がある（例 d:950,  h:2085）。
        # 空白を固定で書くと取りこぼす（2026-09-17 にフォルタの6型番を落とした）。
        sizes = [(c, _mm(w), _mm(d), _mm(h)) for c, w, d, h
                 in re.findall(r"\{\s*code:'([^']+)'\s*,\s*w:\s*([\d.]+)\s*,\s*d:\s*([\d.]+)\s*,\s*h:\s*([\d.]+)\s*\}", e)]
        # 取りこぼしが無いか、単純な型番の数と突き合わせる
        loose = len(re.findall(r"code:'[^']+'", e))
        if loose != len(sizes):
            raise SystemExit("[中止] %s の型番を取りこぼしました（%d 件中 %d 件しか読めていません）。"
                             "書式を確認してください。" % (m.group(1), loose, len(sizes)))
        out[m.group(1)] = (sizes, "sizesComplete:true" in e)
    return out


def main():
    data = products()
    LOAD = C.floor_load()
    missing = [pid for pid, (sizes, _) in data.items()
               if sizes and pid not in PAGES]
    if missing:
        raise SystemExit("[中止] 製品ページの割り当てが無い機種に型番が入っています: %s。"
                         "index.html の PRODUCT_PAGES に製品ページのファイル名を"
                         "足してください。" % "／".join(missing))
    n = 0
    for pid, slug in PAGES.items():
        if pid not in data: continue
        sizes, complete = data[pid]
        if not sizes: continue
        p = os.path.join(ROOT, "products", slug + ".html")
        if not os.path.exists(p): continue
        s = io.open(p, encoding="utf-8").read()

        # 床耐荷重は、その製品の型番が全部そろっているときだけ列にする。
        # 一部だけ公式に記載がある状態で列を作ると、空欄が0kgに見える。
        kg = ({c: LOAD[c] for c, *_ in sizes}
              if all(c in LOAD for c, *_ in sizes) else None)

        note = ("全 %d 型番を掲載しています。" % len(sizes) if complete
                else "公式で確認できた %d 型番を掲載しています。"
                     "<strong>これ以外の型番もあります。</strong>" % len(sizes))
        note += BASE_NOTE
        if kg:
            note += KG_NOTE

        body = re.search(r"(<table class=\"sizes\">.*?</table>)", s, re.S)
        if not body:
            # 型番0件のまま作ったページ。注記の位置に表と注記を新しく置く。
            body = PLACEHOLDER.search(s)
            if not body:
                print("  [飛ばす] 表も差し込み位置も見つかりません:", slug); continue
            block = _table(sizes, kg) + '\n<p class="note">%s</p>' % note
            io.open(p, "w", encoding="utf-8").write(s[:body.start()] + block + s[body.end():])
            print("  %-34s %3d型番%s ← 表を新しく作りました"
                  % (slug, len(sizes), "（全型番）" if complete else ""))
            n += 1
            continue
        s2 = s[:body.start(1)] + _table(sizes, kg) + s[body.end(1):]

        # 表のすぐ下の注記も作り直す。
        # 掲載が全型番かどうかと、床耐荷重の列を出すかどうかで文面が変わる。
        if not NOTE_RE.search(s2):
            raise SystemExit("[中止] %s にサイズ表の注記が見つかりません。"
                             "雛形を変えたなら、このスクリプトも直してください。" % slug)
        s2 = NOTE_RE.sub(lambda m: '<p class="note">%s</p>' % note, s2, count=1)

        if s2 != s:
            io.open(p, "w", encoding="utf-8").write(s2)
            print("  %-34s %3d型番%s" % (slug, len(sizes), "（全型番）" if complete else ""))
            n += 1
    print("[製品ページのサイズ表] %d ページを更新しました" % n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
