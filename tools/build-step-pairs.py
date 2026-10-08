#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
製品ページに「寸法を一段動かすとどう変わるか」の節を差し込む。

読者の質問でいちばん多いのが「同じシリーズで奥行だけが違う2機種のどちら」
（2026-10-05 の市場調査）。同じシリーズで1寸法だけが違う隣り合わせの組は
3社あわせて994組あり、組ごとのページは作れない。
そこで、すでにインデックスされている製品ページの中に節として置く。
新しいURLは1本も増やさない。

出す数字は床面積と寸法の差だけ。床面積は本体の外寸から出した値で、
メーカー公式のサイズ表に載っている床面積と一致する（GP-115D 1120×530＝0.59m² など）。
内部寸法は3社のうちタクボしか公表していないため、ここでは出さない。

同じ段の組み合わせは間口ごとに何通りもあるため、段ごとにまとめて
「この2段が両方ある床の組み合わせが何通りか」と「床面積の増え方の幅」を出す。

    python3 tools/build-step-pairs.py
"""
import importlib.util, io, os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

START = "<!-- STEPPAIRS_START -->"
END = "<!-- STEPPAIRS_END -->"
ANCHOR_1 = "<!-- SIZELINKS_START -->"
ANCHOR_2 = "<h2>設置にあたって</h2>"
GAP = "\n\n        "

AX = [("d", "奥行", ("w", "h")),
      ("w", "間口", ("d", "h")),
      ("h", "高さ", ("w", "d"))]
JP = {"w": "間口", "d": "奥行", "h": "高さ"}


def fmt(n):
    return "{:,}".format(int(n))


def area(w, d):
    return w * d / 1000000.0


def steps(szs, ax, fixed):
    """軸 ax の隣り合う2段ごとに、(組の数, 床面積の増え方の最小, 最大) を返す。"""
    g = defaultdict(dict)
    for s in szs:
        g[tuple(s[k] for k in fixed)][s[ax]] = s
    out = defaultdict(lambda: [0, None, None])
    for key, by in g.items():
        vals = sorted(by)
        for a, b in zip(vals, vals[1:]):
            sa, sb = by[a], by[b]
            rec = out[(a, b)]
            rec[0] += 1
            if ax != "h":
                dz = area(sb["w"], sb["d"]) - area(sa["w"], sa["d"])
                rec[1] = dz if rec[1] is None else min(rec[1], dz)
                rec[2] = dz if rec[2] is None else max(rec[2], dz)
    return out


def merge_near(rows, tol=5):
    """1mmだけ違う段をまとめる。

    エスモとエルモの高さは屋根の勾配で型番ごとに1mmずれるため、
    「1,113→1,313」と「1,114→1,314」が別の行として並んでいた（2026-10-06）。
    読む意味がないので、始点と終点がどちらも tol 以内なら同じ段として扱う。"""
    out = []
    for a, b in sorted(rows):
        n, lo, hi = rows[(a, b)]
        hit = None
        for r in out:
            if abs(a - r["a0"]) <= tol and abs(b - r["b0"]) <= tol:
                hit = r
                break
        if hit is None:
            out.append(dict(a0=a, a1=a, b0=b, b1=b, d0=b - a, d1=b - a,
                            n=n, lo=lo, hi=hi))
            continue
        hit["a1"] = max(hit["a1"], a)
        hit["b1"] = max(hit["b1"], b)
        # 差は行ごとの実際の差からとる。a0〜a1 と b0〜b1 を突き合わせると、
        # 実在しない「+199〜201mm」のような幅が出てしまう
        hit["d0"] = min(hit["d0"], b - a)
        hit["d1"] = max(hit["d1"], b - a)
        hit["n"] += n
        if lo is not None:
            hit["lo"] = lo if hit["lo"] is None else min(hit["lo"], lo)
            hit["hi"] = hi if hit["hi"] is None else max(hit["hi"], hi)
    return out


def span(lo, hi):
    return "%smm" % fmt(lo) if lo == hi else "%s〜%smm" % (fmt(lo), fmt(hi))


def table(ax, jp, rows):
    head = ["%sの段" % jp, "次の段", "差", "この2段が両方ある床の組み合わせ"]
    if ax != "h":
        head.append("床面積の増え方")
    # 製品ページの表の体裁は .sizes が持っている（table-wrap は記事側のクラス）。
    # 横に広いので、はみ出す端末では横スクロールさせる
    out = ['<div style="overflow-x:auto">', '<table class="sizes">', "<thead><tr>"]
    out += ["<th>%s</th>" % h for h in head]
    out += ["</tr></thead>", "<tbody>"]
    for r in rows:
        tds = [span(r["a0"], r["a1"]), span(r["b0"], r["b1"]),
               "+%s" % span(r["d0"], r["d1"]), "%d通り" % r["n"]]
        if ax != "h":
            tds.append("+%.2f m²" % r["lo"] if abs(r["hi"] - r["lo"]) < 0.005
                       else "+%.2f〜+%.2f m²" % (r["lo"], r["hi"]))
        out.append("<tr>" + "".join("<td>%s</td>" % t for t in tds) + "</tr>")
    out += ["</tbody>", "</table>", "</div>"]
    return "".join(out)


def section(p):
    szs = [dict(code=c, w=w, d=d, h=h) for c, w, d, h in p["sizes"]]
    blocks, total, got = [], 0, set()
    for ax, jp, fixed in AX:
        raw = steps(szs, ax, fixed)
        if not raw:
            continue
        rows = merge_near(raw)
        got.add(ax)
        total += sum(v[0] for v in raw.values())
        other = "・".join(JP[k] for k in fixed)
        blocks.append("<h3>%sだけを一段</h3>" % jp)
        blocks.append("<p>%sを変えずに、%sだけを動かせる段です。</p>" % (other, jp))
        # 段の差がすべて同じなら、同じ数字が並ぶだけなので一文で出す
        deltas = {r["d0"] for r in rows} | {r["d1"] for r in rows}
        if len(deltas) == 1:
            dv = deltas.pop()
            lo = min(r["a0"] for r in rows)
            hi = max(r["b1"] for r in rows)
            n = sum(r["n"] for r in rows)
            blocks.append("<p>どの段も差は<b>%smm</b>です。%sは%smmから%smmの間にあり、"
                          "%d通りの組み合わせがこの差で隣り合っています。</p>"
                          % (fmt(dv), jp, fmt(lo), fmt(hi), n))
        else:
            blocks.append(table(ax, jp, rows))
    if not blocks:
        return ""
    lead = ("<h2>寸法を一段動かすとどう変わるか</h2>"
            "<p>間口・奥行・高さのうち<b>一つだけが違う</b>型番の、隣り合わせの組が"
            "このシリーズに<b>%d組</b>あります。他の二つを変えずに一段動かすと、"
            "寸法と床面積がどれだけ変わるかを出しました。"
            "床面積は本体の外寸から出した値で、メーカー公式のサイズ表の床面積と一致します。</p>"
            "<p class=\"note\">同じ段でも間口や高さの組み合わせによって何通りもあるため、"
            "段ごとにまとめています。すべての組み合わせで全段がそろっているわけではありません。"
            "どの寸法が実在するかは、上のサイズ一覧でご確認ください。</p>") % total
    # 補足は、その機種に実際にある軸についてだけ書く。
    # 高さの段が無いシリーズに「高さの段では」と書くと、ありもしない選択肢を示すことになる。
    notes = []
    if "h" in got:
        notes.append("高さの段では床の寸法が変わらないため、床面積は同じです。")
    if p["maker"] == "takubo" and ("w" in got or "d" in got):
        # 内部の高さは屋根の勾配でわずかに動く（ND-1815の1,882mmがND-1822では1,868mm）。
        # 「内部も同じだけ変わる」と書くと高さにも当てはまると読めてしまう
        notes.append("間口や奥行の段では、内部の間口・奥行も外寸と同じだけ変わります"
                     "（タクボは公式の型番ページに内部寸法を載せていて、同じシリーズの中では"
                     "外寸と内部寸法の差が一定でした。内部の高さだけは屋根の勾配でわずかに動きます）。")
    tail = "<p>%s</p>" % "".join(notes) if notes else ""
    return lead + "".join(blocks) + tail


def main():
    n = 0
    for p in C.load_products():
        if p["cat"] not in C.CAT_OK or not p["page"]:
            continue
        path = os.path.join(C.ROOT, p["page"])
        if not os.path.exists(path):
            print("[注意] 製品ページが無い: %s" % p["page"])
            continue
        body = section(p)
        if not body:
            continue
        s = io.open(path, encoding="utf-8").read()
        blk = START + GAP + body.replace("</p><", "</p>" + GAP + "<") + GAP + END
        if START in s and END in s:
            i, j = s.index(START), s.index(END) + len(END)
            new = s[:i] + blk + s[j:]
        else:
            k = s.find(ANCHOR_1)
            if k < 0:
                k = s.find(ANCHOR_2)
            if k < 0:
                print("[注意] 差し込み位置が見つからない: %s" % p["page"])
                continue
            new = s[:k] + blk + GAP + s[k:]
        if new != s:
            io.open(path, "w", encoding="utf-8").write(new)
            n += 1
        print("  %-26s %s" % (p["name"], p["page"]))
    print("[寸法の段] %d ページを更新しました" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
