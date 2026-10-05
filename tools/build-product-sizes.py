#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
製品ページ（products/*.html）の「サイズ一覧」表を、index.html の PRODUCTS から作り直す。

これまで手で同期していたため、PRODUCTS を直しても製品ページが古いまま残った。
（2026-09-17：エスモを 5→90 型番に直したのに、製品ページは 5 行のままだった）

    python3 tools/build-product-sizes.py
"""
import os, re, io, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# PRODUCTS の id → products/ のファイル名
PAGES = {
    "t-gp": "takubo-grand-prestage-jump", "t-nd": "takubo-mr-stockman-dandy",
    "t-jn": "takubo-mr-tallman-dandy",    "t-bs": "takubo-bike-shutterman",
    "t-belos": "takubo-belos",            "t-lsn": "takubo-leisure",
    "t-pe": "takubo-peinte",
    "i-mjx": "inaba-simply",              "i-fs": "inaba-forta",
    "i-fxn": "inaba-bike-hokanko",        "i-grn": "inaba-garudia",
    "i-tbj": "inaba-takuhai-box",         "i-dm": "inaba-arcia-fit",
    "y-ese": "yodoko-esmo",               "y-lmd": "yodoko-elmo",
    "y-lod": "yodoko-elmo-shutter",
    "y-vgc": "yodoko-lavige",
    "i-smx": "inaba-nyso-smx",            "i-sml": "inaba-como-lite",
}

# 表がまだ無いページに差し込むときの目印。型番0件で作ったページは
# 「サイズ一覧」の下がこの注記1行だけになっている。
PLACEHOLDER = re.compile(
    r'<p class="note">現時点でサイズ表は公開されていません。[^<]*</p>')


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
    missing = [pid for pid, (sizes, _) in data.items()
               if sizes and pid not in PAGES]
    if missing:
        raise SystemExit("[中止] PAGES に無い機種に型番が入っています: %s。"
                         "tools/build-product-sizes.py の PAGES に"
                         "製品ページのファイル名を足してください。" % "／".join(missing))
    n = 0
    for pid, slug in PAGES.items():
        if pid not in data: continue
        sizes, complete = data[pid]
        if not sizes: continue
        p = os.path.join(ROOT, "products", slug + ".html")
        if not os.path.exists(p): continue
        s = io.open(p, encoding="utf-8").read()

        rows = "\n".join(
            "          <tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (c, format(w, ","), format(d, ","), format(h, ","))
            for c, w, d, h in sorted(sizes, key=lambda x: (x[1], x[2], x[3])))

        body = re.search(r"(<table class=\"sizes\">.*?</table>)", s, re.S)
        if not body:
            # 型番0件のまま作ったページ。注記の位置に表と注記を新しく置く。
            body = PLACEHOLDER.search(s)
            if not body:
                print("  [飛ばす] 表も差し込み位置も見つかりません:", slug); continue
            note = ("全 %d 型番を掲載しています。" % len(sizes) if complete
                    else "公式で確認できた %d 型番を掲載しています。"
                         "<strong>これ以外の型番もあります。</strong>" % len(sizes))
            rows = "\n".join(
                "          <tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                % (c, format(w, ","), format(d, ","), format(h, ","))
                for c, w, d, h in sorted(sizes, key=lambda x: (x[1], x[2], x[3])))
            block = ('<table class="sizes">\n        <thead>\n'
                     '          <tr><th>型番</th><th>間口 W</th><th>奥行 D</th>'
                     '<th>高さ H</th></tr>\n        </thead>\n        <tbody>\n'
                     '%s\n        </tbody>\n      </table>\n'
                     '<p class="note">%s寸法は本体の外寸（mm）です。'
                     '実際の設置高さは、基礎ブロック分（基本 高さ約10cm）を'
                     '足した値になります。</p>' % (rows, note))
            io.open(p, "w", encoding="utf-8").write(s[:body.start()] + block + s[body.end():])
            print("  %-34s %3d型番%s ← 表を新しく作りました"
                  % (slug, len(sizes), "（全型番）" if complete else ""))
            n += 1
            continue
        tbl = ('<table class="sizes">\n        <thead>\n'
               '          <tr><th>型番</th><th>間口 W</th><th>奥行 D</th><th>高さ H</th></tr>\n'
               '        </thead>\n        <tbody>\n%s\n        </tbody>\n      </table>' % rows)
        s2 = s[:body.start(1)] + tbl + s[body.end(1):]

        # 表のすぐ下の注記も、掲載が全型番かどうかで書き分ける
        head = ("全 %d 型番を掲載しています。" % len(sizes) if complete
                else "公式で確認できた %d 型番を掲載しています。<strong>これ以外の型番もあります。</strong>" % len(sizes))
        s2 = re.sub(r'(<p class="note">).*?(寸法は本体の外寸（mm）です。)',
                    lambda m: m.group(1) + head + m.group(2), s2, count=1, flags=re.S)

        if s2 != s:
            io.open(p, "w", encoding="utf-8").write(s2)
            print("  %-34s %3d型番%s" % (slug, len(sizes), "（全型番）" if complete else ""))
            n += 1
    print("[製品ページのサイズ表] %d ページを更新しました" % n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
