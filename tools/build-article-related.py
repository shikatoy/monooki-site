#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
記事の末尾に「あわせて読む」を作る。記事から記事への受けリンクを切らさないため。

build-crosslinks.py は本文中の言葉でリンクを張るが、手で書いた語の表（MAP）に
載っていない記事や、その語がほかの記事に出てこない記事は、どこからも張られない。
2026-10-08 時点で16本中7本が、受けリンクが記事一覧の1本だけだった
（black-monooki-size-lineup／homecenter-monooki-vs-major3／monooki-okenai-basho／
monooki-one-step-dimension／monooki-rust-where-and-how／
monooki-shutter-vs-slide-opening／takubo-garage-scudo-door-types）。

近さは「キーワード（meta keywords）の語の重なり」と「見出しの2文字の重なり」で測り、
そのうえで**どの記事も受けリンクが2本以上になるまで**差し込む。
近さだけで並べると、話題が孤立している記事（錆・オプション）が誰からも
指されないため、この均しが要る。

    python3 tools/build-article-related.py
"""
import glob, io, os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ART = os.path.join(ROOT, "articles")
START, END = "<!-- AUTO_ARTREL_START -->", "<!-- AUTO_ARTREL_END -->"
ANCHOR_AFTER = "<!-- AUTO_RELATED_END -->"
ANCHOR_BEFORE = "<!-- ═══════════ お問い合わせ導線 ═══════════ -->"
BASE, CAP, MIN_IN = 3, 5, 2
# どの記事にも出てくるので、近さの材料にならない語
STOP = {"物置", "サイズ", "寸法", ""}
# 語では重ならないが、読む筋としてつながっている組（点数を足すだけで、順序は自動）
PIN = [
    ("monooki-rust-where-and-how", "monooki-okenai-basho"),
    ("monooki-rust-where-and-how", "homecenter-monooki-vs-major3"),
    ("monooki-options-and-anchor", "monooki-okenai-basho"),
    ("monooki-options-and-anchor", "kogata-chugata-ogata-chigai"),
    ("monooki-front-clearance", "monooki-shutter-vs-slide-opening"),
    ("black-monooki-size-lineup", "yodo-shutter-height-one-step"),
]
CSS_MARK = "/* AUTO_ARTREL_CSS */"
CSS = CSS_MARK + """
  .rel.artrel { margin-top: 18px; }
"""


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def bigrams(t):
    t = re.sub(r"[\s、。「」『』（）()・/,．…—―\-]+", "", t)
    return {t[i:i + 2] for i in range(len(t) - 1)}


def tags_by_slug():
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    i = s.index("const ARTICLES")
    blk = s[i:s.index("];", i)]
    return dict((m.group(2), m.group(1)) for m in re.finditer(
        r"tag:'([^']*)',\s*\n?\s*title:'[^']*',\s*\n?\s*lead:'[^']*',\s*\n?\s*url:'articles/([^']+)\.html'",
        blk, re.S))


def load():
    tags = tags_by_slug()
    out = []
    for f in sorted(glob.glob(os.path.join(ART, "*.html"))):
        slug = os.path.basename(f)[:-5]
        if slug == "index":
            continue
        s = io.open(f, encoding="utf-8").read()
        kw = re.search(r'<meta name="keywords" content="(.*?)"', s)
        h1 = re.search(r"(?s)<h1[^>]*>(.*?)</h1>", s)
        h2 = re.findall(r"(?s)<h2[^>]*>(.*?)</h2>", s)
        title = re.sub(r"\s+", " ", re.sub("<[^>]+>", "", h1.group(1))).strip() if h1 else slug
        w = set()
        for k in (kw.group(1) if kw else "").split(","):
            for t in k.split():
                t = t.strip()
                if t and t not in STOP:
                    w.add(t)
        bg = bigrams(title + "".join(re.sub("<[^>]+>", "", x) for x in h2))
        out.append(dict(slug=slug, path=f, title=title, w=w, bg=bg,
                        tag=tags.get(slug, "")))
    return out


def sim(a, b):
    s = len(a["w"] & b["w"]) * 3
    s += len(a["bg"] & b["bg"]) / max(1, min(len(a["bg"]), len(b["bg"]))) * 10
    if (a["slug"], b["slug"]) in PINS:
        s += 20
    if a["tag"] and a["tag"] == b["tag"]:
        s += 1
    return s


PINS = set()
for x, y in PIN:
    PINS.add((x, y)); PINS.add((y, x))


def build(arts):
    by = {a["slug"]: a for a in arts}
    rel = {}
    for a in arts:
        rel[a["slug"]] = [b["slug"] for _, b in sorted(
            ((sim(a, b), b) for b in arts if b is not a),
            key=lambda x: (-x[0], x[1]["slug"]))[:BASE]]
    inb = defaultdict(set)
    for s_, ts in rel.items():
        for t in ts:
            inb[t].add(s_)
    # 受けが足りない記事を、いちばん近い記事の一覧に差し込む
    for slug in sorted((a["slug"] for a in arts), key=lambda s_: (len(inb[s_]), s_)):
        while len(inb[slug]) < MIN_IN:
            cand = sorted(((sim(by[slug], b), b["slug"]) for b in arts
                           if b["slug"] != slug and slug not in rel[b["slug"]]
                           and len(rel[b["slug"]]) < CAP),
                          key=lambda x: (-x[0], x[1]))
            if not cand:
                break
            rel[cand[0][1]].append(slug)
            inb[slug].add(cand[0][1])
    return rel, inb


def block(slugs, by):
    li = "\n".join(
        '        <li><a href="%s.html"><span class="rel-txt">'
        '<span class="rel-kicker">%s</span>'
        '<span class="rel-name">%s</span></span>'
        '<span class="rel-go">&rarr;</span></a></li>'
        % (s_, esc(by[s_]["tag"] or "記事"), esc(by[s_]["title"])) for s_ in slugs)
    return (START + "\n    <aside class=\"rel artrel\">\n"
            '      <p class="rel-label">Related — あわせて読む</p>\n'
            "      <ul class=\"rel-list\">\n%s\n      </ul>\n    </aside>\n    " % li + END)


def main():
    arts = load()
    if not arts:
        print("[中止] 記事が見つかりません")
        return 1
    by = {a["slug"]: a for a in arts}
    rel, inb = build(arts)
    n = 0
    for a in arts:
        s = io.open(a["path"], encoding="utf-8").read()
        orig = s
        s = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n*\s*", "", s, flags=re.S)
        blk = block(rel[a["slug"]], by)
        if ANCHOR_AFTER in s:
            s = s.replace(ANCHOR_AFTER, ANCHOR_AFTER + "\n\n    " + blk, 1)
        elif ANCHOR_BEFORE in s:
            s = s.replace(ANCHOR_BEFORE, blk + "\n\n    " + ANCHOR_BEFORE, 1)
        else:
            print("  [注意] 差し込み位置が無い:", a["slug"])
            continue
        if CSS_MARK not in s and "</style>" in s:
            s = s.replace("</style>", CSS + "</style>", 1)
        if s != orig:
            io.open(a["path"], "w", encoding="utf-8").write(s)
            n += 1
    worst = min(len(inb[a["slug"]]) for a in arts)
    print("[あわせて読む] %d 本の記事を更新／受けリンクは最少 %d 本" % (n, worst))
    for a in sorted(arts, key=lambda x: len(inb[x["slug"]])):
        print("  受け%2d  %-36s → %s" % (len(inb[a["slug"]]), a["slug"][:34],
                                        "／".join(rel[a["slug"]])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
