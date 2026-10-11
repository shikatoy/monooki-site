#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""製品ページに「寸法の近い他社の型番」を出す。

サイズ帯のページ（size/band-*.html）は0.3m刻みの帯で他社を横に並べているが、
帯の中では実寸が最大300mm違う。買い替えや置き換えを考えるときに知りたいのは
「いま使っているこの型番に、他社だとどれが一番近いか」という型番どうしの対応。

同じ区分（KUBUN）で、メーカーが違うシリーズだけを相手にする。
間口と奥行が ±TOL_WD、高さが ±TOL_H の範囲に収まる型番の組を数え、
いちばん近い組を例として出す。データは index.html の PRODUCTS が唯一の出典。

publish.sh から自動で呼ばれる。--dry を付けると書き込まずに結果だけ出す。
"""
import importlib.util, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

TOL_WD = 60      # 間口・奥行の許容差（mm）
TOL_H = 120      # 高さの許容差（mm）
TOP = 4          # 1ページに出す他社シリーズの数

START = "<!-- NEARCODES_START -->"
END = "<!-- NEARCODES_END -->"
ANCHOR = "<!-- SIZELINKS_START -->"
# サイズ帯の導線が無いページ（物置以外の区分）用。本文の終わりに差し込む
ANCHOR2 = "\n      </div>\n    </article>"


def fm(n):
    return "{:,}".format(n)


def near(p, others):
    """p に対して、他社シリーズごとの「重なる型番数」と「いちばん近い組」を出す"""
    out = []
    for q in others:
        cnt, best = 0, None
        for pc, pw, pd, ph in p["sizes"]:
            for qc, qw, qd, qh in q["sizes"]:
                dw, dd, dh = abs(pw - qw), abs(pd - qd), abs(ph - qh)
                if dw <= TOL_WD and dd <= TOL_WD and dh <= TOL_H:
                    cnt += 1
                    s = dw + dd + dh
                    if best is None or s < best[0]:
                        best = (s, (pc, pw, pd, ph), (qc, qw, qd, qh))
        if cnt:
            out.append((cnt, best, q))
    out.sort(key=lambda x: (-x[0], x[1][0]))
    return out[:TOP]


def block(p, rows):
    if not rows:
        return ("\n        <h2>寸法の近い他社の型番</h2>\n"
                "        <p>同じ区分で、間口と奥行が±%dmm・高さが±%dmm に収まる他社の型番は、"
                "当サイトの掲載分には見当たりませんでした。</p>\n" % (TOL_WD, TOL_H))
    tr = []
    for cnt, (_, a, b), q in rows:
        name = ('<a href="%s">%s</a>' % (os.path.basename(q["page"]), C.esc(q["name"]))
                if q.get("page") else C.esc(q["name"]))
        tr.append(
            "<tr><td class=\"l\">%s<br><span class=\"m\" style=\"font-size:11px;color:#6b6b66\">%s</span></td>"
            "<td class=\"l m\">%s<br>%s×%s×%s</td>"
            "<td class=\"l m\">%s<br>%s×%s×%s</td>"
            "<td>%d</td></tr>"
            % (name, C.MAKER_JP[q["maker"]],
               C.esc(a[0]), fm(a[1]), fm(a[2]), fm(a[3]),
               C.esc(b[0]), fm(b[1]), fm(b[2]), fm(b[3]), cnt))
    return (
        "\n        <h2>寸法の近い他社の型番</h2>\n"
        "        <p>同じ区分のなかで、<b>間口と奥行が±%dmm、高さが±%dmm</b> に収まる他社の型番を数えました。"
        "サイズ帯のページは0.3m刻みなので帯のなかで最大300mm違いますが、ここは型番どうしの対応です。</p>\n"
        "        <div class=\"table-wrap\"><table class=\"tbl\"><thead><tr>"
        "<th class=\"l\">他社のシリーズ</th><th class=\"l\">%s のいちばん近い型番</th>"
        "<th class=\"l\">相手のいちばん近い型番</th><th>重なる組</th>"
        "</tr></thead><tbody>%s</tbody></table></div>\n"
        "        <p class=\"note\">寸法は本体の外寸（mm、間口×奥行×高さ）です。"
        "扉の形や有効開口は別なので、置き換えられるという意味ではありません。"
        "「重なる組」は、この許容差に収まる型番の組み合わせの数です。</p>\n"
        % (TOL_WD, TOL_H, C.esc(p["name"]), "".join(tr)))


def main():
    dry = "--dry" in sys.argv
    prods = [p for p in C.load_products() if p.get("page") and p["sizes"]]
    n_w = 0
    for p in prods:
        g = C.KUBUN.get(p["cat"], p["cat"])
        others = [q for q in prods
                  if q["id"] != p["id"] and q["maker"] != p["maker"]
                  and C.KUBUN.get(q["cat"], q["cat"]) == g]
        rows = near(p, others)
        if dry:
            print("%-26s %-12s 他社候補%2d → %s"
                  % (p["name"][:26], g, len(others),
                     "／".join("%s(%d組)" % (q["name"][:14], c) for c, _, q in rows) or "なし"))
            continue
        path = os.path.join(C.ROOT, p["page"])
        s = io.open(path, encoding="utf-8").read()
        body = "\n        " + START + "\n" + block(p, rows) + "\n        " + END + "\n"
        if START in s and END in s:
            i, j = s.find(START), s.find(END) + len(END)
            new = s[:i] + body.strip("\n").lstrip() + s[j:]
        elif ANCHOR in s:
            new = s.replace(ANCHOR, body.strip("\n").lstrip() + "\n\n        " + ANCHOR, 1)
        elif s.count(ANCHOR2) == 1:
            new = s.replace(ANCHOR2, "\n        " + body.strip("\n").lstrip() + ANCHOR2, 1)
        else:
            print("[警告] %s に差し込む場所が見つかりません" % p["page"])
            continue
        if new != s:
            io.open(path, "w", encoding="utf-8").write(new)
            n_w += 1
    if dry:
        return 0
    print("[近い他社型番] %d ページを更新しました（許容差 間口・奥行±%dmm／高さ±%dmm）"
          % (n_w, TOL_WD, TOL_H))
    return 0


if __name__ == "__main__":
    sys.exit(main())
