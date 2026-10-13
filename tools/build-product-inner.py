#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""製品ページに「内寸と開口部」の表を入れる。index.html の INNER から作る。

外形寸法のサイズ表（build-product-sizes.py）とは別の表にしている。
1つの表に9列にすると390pxで横にはみ出すため。

INNER に1件も無いシリーズのページには、何も入れない（印も残さない）。

    python3 tools/build-product-inner.py
"""
import importlib.util, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

START = "<!-- INNER_START -->"
END = "<!-- INNER_END -->"
# 外形寸法の表のすぐ下の注記。この段落の直後に差し込む
AFTER = re.compile(r'<p class="note">[^<]*寸法は本体の外寸（mm）です。.*?</p>', re.S)


def fmt(v):
    if v is None:
        return "&mdash;"
    return format(int(v), ",") if float(v) == int(v) else format(v, ",")


def table(rows, src, origin):
    head = ('<tr><th>型番</th><th>内寸 W</th><th>内寸 D</th><th>内寸 H</th>'
            '<th>開口 W</th><th>開口 H</th></tr>')
    body = "\n".join(
        "          <tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (c, fmt(iw), fmt(idp), fmt(ih), fmt(kw), fmt(kh))
        for c, iw, idp, ih, kw, kh in rows)
    return (START + '\n'
            '      <h2>内寸と開口部</h2>\n'
            '      <div style="overflow-x:auto;-webkit-overflow-scrolling:touch">\n'
            '      <table class="sizes" style="min-width:340px">\n        <thead>\n          %s\n        </thead>\n'
            '        <tbody>\n%s\n        </tbody>\n      </table>\n'
            '      </div>\n'
            '      <p class="note">%s%s'
            '内寸は中に入る大きさ、開口は入口の大きさです。'
            '内寸の高さは梁下などの一番低いところ、開口の高さは扉のところで測った値なので、'
            '型番によっては開口の高さが内寸の高さより大きくなります（公式の表記どおりです）。'
            '<strong>&mdash;</strong> は公式に記載が見当たらないものです。</p>\n'
            '      ' + END) % (head, body, src, origin)


def main():
    inner = C.load_inner()
    if not inner:
        print("[内寸と開口部] INNER が空です"); return 0
    n = 0
    for p in C.load_products():
        if not p["page"]:
            continue
        path = os.path.join(C.ROOT, p["page"])
        if not os.path.exists(path):
            continue
        rows = [(c,) + inner[c] for c, w, d, h in p["sizes"] if c in inner]
        s = io.open(path, encoding="utf-8").read()
        if not rows:
            # 以前入っていた表を取り除く（INNER から外した場合）
            s2 = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?\s*", "", s, flags=re.S)
            if s2 != s:
                io.open(path, "w", encoding="utf-8").write(s2)
                print("  %-34s 表を外しました" % os.path.basename(p["page"]))
                n += 1
            continue
        miss = len(p["sizes"]) - len(rows)
        src = ("全 %d 型番ぶんあります。" % len(rows) if not miss
               else "%d 型番のうち %d 型番ぶんです（残りは公式に見当たりません）。"
                    % (len(p["sizes"]), len(rows)))
        mk = {"takubo": "タクボ公式の型番ページ", "inaba": "イナバ公式の寸法表",
              "yodoko": "ヨドコウ公式の仕様図（DXF）"}.get(p["maker"], "メーカー公式")
        blk = table(rows, src, "出典は%sです。" % mk)
        if START in s:
            s2 = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _m: blk, s, flags=re.S)
        else:
            m = AFTER.search(s)
            if not m:
                print("  [飛ばす] 差し込み位置が見つかりません:", os.path.basename(p["page"]))
                continue
            s2 = s[:m.end()] + "\n\n      " + blk + s[m.end():]
        if s2 != s:
            io.open(path, "w", encoding="utf-8").write(s2)
            print("  %-34s %3d型番" % (os.path.basename(p["page"]), len(rows)))
            n += 1
    print("[内寸と開口部] %d ページを更新しました" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
