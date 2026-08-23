#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ペインタ（タクボ）の扉の柄6種を、製品ページに描き分けて載せる。

柄の構成はエクスショップの色見本（全12色＝6柄×本体色2色）に合わせている。
図はメーカーの色見本をもとにした描画であって写真ではない。その旨をページにも書く。
何度実行しても同じ絵になる（乱数は固定の種から作る）。
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "products", "takubo-peinte.html")
BEG, END = "<!-- AUTO_PEINTE_START -->", "<!-- AUTO_PEINTE_END -->"
CSSBEG, CSSEND = "/* AUTO_PEINTE_CSS_START */", "/* AUTO_PEINTE_CSS_END */"

W, H = 120, 150


class Rnd:
    """種を固定した擬似乱数。実行のたびに絵が変わらないようにする"""
    def __init__(self, seed):
        self.s = (seed + 1) * 9301

    def next(self):
        self.s = (self.s * 9301 + 49297) % 233280
        return self.s / 233280

    def pick(self, seq):
        return seq[int(self.next() * len(seq)) % len(seq)]

    def between(self, a, b):
        return a + (b - a) * self.next()


def metal(seed):
    """金属サイディング：濃色に等間隔の縦リブ。溝の片側だけ明るい（陰影）"""
    o = ['<rect width="%d" height="%d" fill="#2f3336"/>' % (W, H)]
    x = 3.0
    while x < W:
        o.append('<rect x="%.1f" y="0" width="1.7" height="%d" fill="#15181a"/>' % (x, H))
        o.append('<rect x="%.1f" y="0" width="0.9" height="%d" fill="#4d5255" opacity=".85"/>' % (x + 1.7, H))
        x += 7.0
    return "".join(o)


def ceramic(seed):
    """窯業系サイディング（積層タイプ）：細長い石片を段に積んだ柄"""
    r = Rnd(seed)
    pal = ["#e9e1d3", "#ddd3c2", "#cdc0a9", "#e3d9c8", "#d3c8b5"]
    o = ['<rect width="%d" height="%d" fill="#cfc4b0"/>' % (W, H)]
    y, rowh = 0.0, 6.4
    while y < H:
        x = -r.between(0, 18)
        while x < W:
            w = r.between(9, 21)
            o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>'
                     % (x, y, w - 0.7, rowh - 0.7, r.pick(pal)))
            x += w
        y += rowh
    return "".join(o)


def stone(seed):
    """窯業系サイディング（石積みタイプ）：大きさの揃わない石を乱れた目地で積む"""
    r = Rnd(seed)
    pal = ["#f3f2ee", "#e4e2dc", "#cfccc5", "#ecebe6", "#d9d6cf", "#c4c1ba"]
    o = ['<rect width="%d" height="%d" fill="#d5d5d0"/>' % (W, H)]
    y = 0.0
    while y < H:
        rowh = r.between(11, 20)
        x = -r.between(0, 30)
        while x < W:
            w = r.between(20, 50)
            c = r.pick(pal)
            o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>'
                     % (x, y, w - 1.2, rowh - 1.2, c))
            # 石の上端に光、下端に影を入れて厚みを出す
            o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="1.6" fill="#fff" opacity=".38"/>'
                     % (x, y, w - 1.2, ))
            o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="2.2" fill="#000" opacity=".07"/>'
                     % (x, y + rowh - 3.4, w - 1.2))
            x += w
        y += rowh
    return "".join(o)


def wood(seed, base, dark, grain):
    """木質系：縦の板張り。板ごとに濃さを少し変え、細い木目を入れる"""
    r = Rnd(seed)
    o = ['<rect width="%d" height="%d" fill="%s"/>' % (W, H, base)]
    pw = 17.0
    x = 0.0
    i = 0
    while x < W:
        shade = r.between(-0.06, 0.06)
        o.append('<rect x="%.1f" y="0" width="%.1f" height="%d" fill="%s" opacity="%.2f"/>'
                 % (x, pw, H, "#ffffff" if shade > 0 else "#000000", abs(shade)))
        # 板の境目
        o.append('<rect x="%.1f" y="0" width="1.0" height="%d" fill="%s" opacity=".75"/>' % (x, H, dark))
        # 木目（ゆるく蛇行する縦線）
        for k in range(3):
            gx = x + 3.0 + k * 3.6 + r.between(-0.8, 0.8)
            d = "M%.1f 0" % gx
            yy = 0.0
            while yy < H:
                yy += 24
                d += " Q%.1f %.1f %.1f %.1f" % (gx + r.between(-1.6, 1.6), yy - 12, gx + r.between(-0.7, 0.7), min(yy, H))
            o.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.2f" opacity="%.2f"/>'
                     % (d, grain, r.between(0.4, 0.9), r.between(0.18, 0.38)))
        x += pw
        i += 1
    return "".join(o)


PATTERNS = [
    ("サイディングメタル", "金属サイディング調", lambda: metal(1)),
    ("サイディングセラミック", "窯業系サイディング調", lambda: ceramic(2)),
    ("サイディングストーン", "窯業系サイディング調", lambda: stone(3)),
    ("ウッドテイスト グレー", "木質系（木目調）", lambda: wood(4, "#a7a7a2", "#78786f", "#84847d")),
    ("ウッドテイスト キャメル", "木質系（木目調）", lambda: wood(5, "#9d6c33", "#6f4a20", "#7b5223")),
    ("ウッドテイスト ブラックチェリー", "木質系（木目調）", lambda: wood(6, "#4e2c1b", "#301a10", "#331d11")),
]

CSS = CSSBEG + """
  /* ───── 扉の柄（tools/build-peinte-patterns.py が生成） ───── */
  .pat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 24px 0 0; }
  @media (min-width: 700px) { .pat-grid { grid-template-columns: repeat(3, 1fr); gap: 14px; } }
  .pat svg { display: block; width: 100%; height: auto; }
  .pat { margin: 0; border: 1px solid var(--line); background: #fff; display: flex; flex-direction: column; }
  .pat figcaption { flex: 1 1 auto; padding: 9px 11px; border-top: 1px solid var(--linesoft);
    background: #efe9dc; display: flex; flex-direction: column; justify-content: center; }
  .pat-cat { display: block; font-family: 'IBM Plex Mono', monospace; font-size: 9px;
    letter-spacing: .1em; color: var(--mute); }
  .pat-name { display: block; margin-top: 3px; font-family: 'Shippori Mincho B1', serif;
    font-weight: 700; font-size: 13px; line-height: 1.45; }
  .pat-body { margin: 22px 0 0; display: flex; gap: 10px; flex-wrap: wrap; }
  .pat-body span { display: inline-flex; align-items: center; gap: 8px; border: 1px solid var(--linesoft);
    background: #fff; padding: 7px 12px; font-size: 12.5px; }
  .pat-body i { width: 15px; height: 15px; border: 1px solid var(--linesoft); font-style: normal; }
  .pat-note { margin: 18px 0 0; font-size: 12px; line-height: 1.95; color: var(--mute); }
""" + CSSEND + "\n"


def build():
    tiles = []
    for name, cat, fn in PATTERNS:
        tiles.append(
            '<figure class="pat">\n'
            '          <svg viewBox="0 0 %d %d" role="img" aria-label="%s の柄">%s</svg>\n'
            '          <figcaption><span class="pat-cat">%s</span><span class="pat-name">%s</span></figcaption>\n'
            '        </figure>' % (W, H, name, fn(), cat, name))
    return (BEG + """
        <h2>扉の柄は6種類</h2>

        <p>ペインタは、扉にUVインクジェットで柄を印刷したモデルです。<strong>柄が6種類、本体色が2色</strong>あり、組み合わせは全12通りになります。同じ寸法・同じ構造のまま、外壁や庭の雰囲気に合わせて見た目だけを選べる、という位置づけの機種です。</p>

        <div class="pat-grid">
        """ + "\n        ".join(tiles) + """
        </div>

        <p class="pat-note">※ 上の図は、販売店が公開している色見本をもとに<strong>柄の出方が分かるように描いたもの</strong>で、写真ではありません。実際の色味・目地の出方・光の当たり方は現物と異なります。色で選ぶときは、必ず販売店で現物の色見本をご確認ください。</p>

        <p>本体色は、柄とは別に次の2色から選びます。扉以外の側面・背面・屋根がこの色になります。</p>

        <div class="pat-body">
          <span><i style="background:#efeadf"></i>ムーンホワイト</span>
          <span><i style="background:#232323"></i>アイボリーブラック</span>
        </div>

        """ + END + "\n\n")


def main():
    if not os.path.exists(PAGE):
        print("[中止] ページが見つかりません:", PAGE); return 1
    s = open(PAGE, encoding="utf-8").read()
    orig = s
    s = re.sub(re.escape(BEG) + r".*?" + re.escape(END) + r"\s*", "", s, flags=re.S)
    s = re.sub(re.escape(CSSBEG) + r".*?" + re.escape(CSSEND) + r"\n?", "", s, flags=re.S)
    if "</style>" not in s:
        print("[中止] <style> が見つかりません"); return 1
    s = s.replace("</style>", CSS + "</style>", 1)
    anchor = '<a class="shop"'
    if anchor not in s:
        print("[中止] 差し込み位置（提携リンク）が見つかりません"); return 1
    s = s.replace(anchor, build() + "        " + anchor, 1)
    if s != orig:
        open(PAGE, "w", encoding="utf-8").write(s)
        print("[ペインタ] 扉の柄 %d 種を書き出しました（%d 文字）" % (len(PATTERNS), len(s)))
    else:
        print("[ペインタ] 変更はありません")
    return 0


if __name__ == "__main__":
    sys.exit(main())
