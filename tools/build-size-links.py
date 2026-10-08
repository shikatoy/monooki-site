#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
製品ページから、その機種が入る size/ のページへリンクを張る。

2026-10-04：size/ 配下の40ページに、size/ の外からのリンクが1本も無かった。
size/index.html からぶら下がるだけで、Search Console では
「検出 - インデックス未登録」のまま止まっていた。
製品ページは既に拾われているので、そこから文脈のあるリンクを張る。

読者にとっても、「この機種が入る寸法帯で、他社に何があるか」への近道になる。

    python3 tools/build-size-links.py
"""
import importlib.util, os, re, io, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

SIZED = os.path.join(C.ROOT, "size")
STEP = 300
START = "<!-- SIZELINKS_START -->"
END = "<!-- SIZELINKS_END -->"
ANCHOR = "<h2>設置にあたって</h2>"
GAP = "\n\n        "

# build-size-pages.py の PAGES と同じ条件。増やすときは両方直すこと。
AXIS_PAGES = [
    ("depth-600",   "d",  600, "奥行60cm以下"),
    ("depth-900",   "d",  900, "奥行90cm以下"),
    ("height-1400", "h", 1400, "高さ1.4m以下"),
    ("height-1900", "h", 1900, "高さ1.9m以下"),
    ("width-1200",  "w", 1200, "間口1.2m以下"),
    ("width-1500",  "w", 1500, "間口1.5m以下"),
]


def m(v):
    return ("%.1f" % (v / 1000.0)).rstrip("0").rstrip(".")


def exists(slug):
    return os.path.exists(os.path.join(SIZED, slug + ".html"))


def links_for(p):
    """その機種の型番が入る size/ ページを (帯, 一軸) に分けて返す。
    実在するページだけ（帯は2メーカー・5型番以上でしか作られない）。"""
    bands, axes, seen = [], [], set()
    if p["cat"] in C.CAT_OK:
        for bw, bd in sorted({(w // STEP * STEP, d // STEP * STEP)
                              for _, w, d, _ in p["sizes"]}):
            slug = "band-w%d-d%d" % (bw // 10, bd // 10)
            if slug in seen or not exists(slug):
                continue
            seen.add(slug)
            bands.append((slug, "間口%s〜%sm × 奥行%s〜%sm"
                          % (m(bw), m(bw + STEP), m(bd), m(bd + STEP))))
    # 一軸のページも物置だけの一覧（size/ の各ページに「この一覧は物置のみです」と
    # 書いてある）。帯だけを CAT_OK で絞っていたため、宅配ボックス・断熱物置・
    # バイク車庫のページから、その機種が載っていない一覧へリンクが張られていた
    # （2026-10-06 に気づいた。2026-10-04 の宅配ボックスの件と同じ原因）
    if p["cat"] not in C.CAT_OK:
        return bands, axes
    col = {"w": 1, "d": 2, "h": 3}
    for slug, axis, limit, label in AXIS_PAGES:
        if slug in seen or not exists(slug):
            continue
        if any(s[col[axis]] <= limit for s in p["sizes"]):
            seen.add(slug)
            axes.append((slug, label))
    return bands, axes


def render(bands, axes):
    def row(title, items):
        if not items:
            return ""
        a = "／".join('<a href="../size/%s.html">%s</a>' % (slug, C.esc(lab))
                      for slug, lab in items)
        return "        <p><b>%s</b><br>%s</p>%s" % (title, a, GAP)
    # 多い機種で26本になる。箇条書きだと縦に長いので「／」区切りの段落にする。
    return ("%s%s        <h2>この機種が入るサイズ帯</h2>%s"
            "        <p>同じ寸法に収まる他社の機種を、まとめて見られます。"
            "実寸はメーカーごとに少しずつ違うので、横並びで確かめてください。</p>%s"
            "%s%s%s"
            % (START, GAP, GAP, GAP,
               row("間口と奥行の組み合わせで見る", bands),
               row("一つの寸法だけで見る", axes), END))


def main():
    prods = C.load_products()
    if not prods:
        raise SystemExit("[中止] PRODUCTS を読めませんでした。")
    n, total = 0, 0
    reach = set()
    # 既存ブロックと前後の空白をまとめて外してから入れ直す。
    # 空白を残すと、実行のたびに改行が増えていく（2026-10-04 に踏んだ）。
    strip = re.compile(r"\s*" + re.escape(START) + r".*?" + re.escape(END) + r"\s*(?="
                       + re.escape(ANCHOR) + r")", re.S)
    for p in prods:
        if not p["page"]:
            continue
        f = os.path.join(C.ROOT, p["page"])
        if not os.path.exists(f):
            raise SystemExit("[中止] %s のページがありません: %s" % (p["id"], p["page"]))
        s = io.open(f, encoding="utf-8").read()
        s2 = strip.sub(GAP, s)
        if ANCHOR not in s2:
            raise SystemExit('[中止] %s に「設置にあたって」の見出しがありません。'
                             "雛形を変えたなら、このスクリプトも直してください。" % p["page"])
        bands, axes = links_for(p)
        if bands or axes:
            reach.update(slug for slug, _ in bands + axes)
            total += len(bands) + len(axes)
            s2 = s2.replace(ANCHOR, render(bands, axes) + GAP + ANCHOR, 1)
        if s2 != s:
            io.open(f, "w", encoding="utf-8").write(s2)
            n += 1

    allp = {os.path.splitext(x)[0] for x in os.listdir(SIZED)
            if x.endswith(".html") and x != "index.html"}
    orphan = sorted(allp - reach)
    print("[サイズ帯への導線] %d ページを更新 ／ リンク %d 本" % (n, total))
    if orphan:
        print("  [注意] 製品ページから届かない size/ ページ: %s" % "／".join(orphan))
    else:
        print("  size/ の %d ページすべてに、製品ページからの導線があります" % len(allp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
