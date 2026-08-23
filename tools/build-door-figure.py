#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
「扉はどっち側が開くのか」の記事に、右開き／左開きの模式図を入れる。

“右開き” は戸を右へ引くこと。開くのは反対の左側になる。
名前と開く場所が逆になるので、文字だけだと読者がまず引っかかる。
そこで「引いたあとの状態」を描いて、開口がどちら側にできるかを見せる。
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "articles", "monooki-door-opening-side.html")
BEG, END = "<!-- AUTO_DOORFIG_START -->", "<!-- AUTO_DOORFIG_END -->"
CSSBEG, CSSEND = "/* AUTO_DOORFIG_CSS_START */", "/* AUTO_DOORFIG_CSS_END */"

CSS = CSSBEG + """
  /* ───── 扉の開き方の図（tools/build-door-figure.py が生成） ───── */
  .dfig { margin: 34px 0 0; }
  .dfig-grid { display: grid; grid-template-columns: 1fr; gap: 14px; }
  @media (min-width: 620px) { .dfig-grid { grid-template-columns: 1fr 1fr; } }
  .dfig figure { margin: 0; border: 1px solid var(--line); background: #fff; }
  .dfig svg { display: block; width: 100%; height: auto; }
  .dfig figcaption { padding: 11px 14px; border-top: 1px solid var(--linesoft); background: #efe9dc; }
  .dfig-t { display: block; font-family: 'Shippori Mincho B1', serif; font-weight: 700; font-size: 14px; }
  .dfig-s { display: block; margin-top: 4px; font-size: 12px; line-height: 1.8; color: var(--mute); }
  .dfig-note { margin: 14px 0 0; font-size: 12px; line-height: 1.95; color: var(--mute); }
""" + CSSEND + "\n"

W, H = 260, 172
ROOF_Y, BODY_Y, BODY_B = 26, 38, 148
X1, X2 = 22, 238
MID = (X1 + X2) / 2


def panel(mirror):
    """引いたあとの状態を描く。mirror=False が右開き（戸を右へ引く／開くのは左）"""
    def fx(x):
        return (X1 + X2 - x) if mirror else x

    o = []
    # 地面
    o.append('<line x1="10" y1="%d" x2="%d" y2="%d" stroke="#101010" stroke-width="2"/>' % (BODY_B, W - 10, BODY_B))
    # 屋根
    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="#101010" stroke-width="1.6"/>'
             % (X1 - 8, ROOF_Y, (X2 - X1) + 16, BODY_Y - ROOF_Y))
    # 本体の外枠
    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="#101010" stroke-width="1.6"/>'
             % (X1, BODY_Y, X2 - X1, BODY_B - BODY_Y))
    # 開口（戸が退いてできた空き。中は暗がり）
    ox1, ox2 = sorted([fx(X1), fx(MID)])
    o.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="#2b2b2b"/>'
             % (ox1 + 1, BODY_Y + 1, ox2 - ox1 - 1, BODY_B - BODY_Y - 2))
    # 戸が重なっている側（固定パネル＋引いてきた戸の2枚）
    dx1, dx2 = sorted([fx(MID), fx(X2)])
    o.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="#ffffff" stroke="#101010" stroke-width="1.4"/>'
             % (dx1, BODY_Y, dx2 - dx1, BODY_B - BODY_Y))
    inner = fx(MID + (X2 - MID) * 0.42)
    o.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#101010" stroke-width="1.2" opacity=".55"/>'
             % (inner, BODY_Y + 4, inner, BODY_B - 4))
    # 取っ手
    gx = fx(MID + 7)
    o.append('<line x1="%.1f" y1="86" x2="%.1f" y2="104" stroke="#101010" stroke-width="2.6"/>' % (gx, gx))
    # 引いた向きの矢印
    ay = BODY_B + 14
    a1, a2 = fx(MID - 34), fx(MID + 40)
    o.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#a3512b" stroke-width="2"/>' % (a1, ay, a2, ay))
    # 矢印の頭は、進む向きの先端が尖るように置く（符号を逆にすると逆向きになる）
    hd = 7 if mirror else -7
    o.append('<path d="M%.1f %d l%d -5 l0 10 Z" fill="#a3512b"/>' % (a2, ay, hd))
    return "".join(o)


def fig(mirror, title, sub):
    return ('<figure>\n'
            '          <svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>\n'
            '          <figcaption><span class="dfig-t">%s</span><span class="dfig-s">%s</span></figcaption>\n'
            '        </figure>' % (W, H, title, panel(mirror), title, sub))


BLOCK = (BEG + """
        <div class="dfig">
          <div class="dfig-grid">
        """ + fig(False, "標準の向き",
                  "右側が固定パネル。左の戸が右へ動いて、<strong>開くのは左側</strong>。カタログの「右側固定パネル」はこの向きのこと。")
        + "\n        " + fig(True, "逆向き",
                             "左側が固定パネル。<strong>開くのは右側</strong>。"
                             "希望があるとき、扉の前に障害物があるときに、こちらにする。")
        + """
          </div>
          <p class="dfig-note">※ 開けたあとの状態を、正面から見た模式図です。黒く塗った側が開口になります。実際の戸の枚数・重なり方は機種によって異なります。</p>
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
        print("[中止] <style> がありません"); return 1
    s = s.replace("</style>", CSS + "</style>", 1)
    # 用語の説明の直後に置く（読んだ直後に絵で確かめられる位置）
    anchor = "と言うほうが、行き違いが起きません。</p>"
    if anchor not in s:
        print("[中止] 差し込み位置（用語の説明）が見つかりません"); return 1
    s = s.replace(anchor, anchor + "\n\n        " + BLOCK, 1)
    if s != orig:
        open(PAGE, "w", encoding="utf-8").write(s)
        print("[扉の図] 右開き／左開きの模式図を入れました（%d 文字）" % len(s))
    else:
        print("[扉の図] 変更はありません")
    return 0


if __name__ == "__main__":
    sys.exit(main())
