#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
記事ごとの OG 画像（SNS・LINE で共有したときに出る絵）を作る。

書き出し先は images/og-<slug>.png。記事側の og:image と JSON-LD の image を
その名前に差し替えれば、共有したときに記事ごとの絵が出る。
（差し替えないと全部 og-image.png のままになり、5本が同じ絵になる）

    python3 tools/build-og-images.py                 # TITLES 全部
    python3 tools/build-og-images.py monooki-...     # slug 指定

※ publish.sh の生成チェーンには入れていない。次の2つが要るため。
   1) playwright（chromium）
   2) Shippori Mincho B1 の woff2 を tools/_ogfonts/ に置く
        sm-jp-700.woff2 / sm-lat-700.woff2
        （npm の @fontsource/shippori-mincho-b1 の files/ から取れる。OFL）
   どちらも無い環境では動かないので、画像を足すときだけ手で回す。

寸法は最初に作った5枚を実測して合わせてある。触ると既存と揃わなくなる。
"""
import os, sys, re, json, asyncio

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "_ogfonts")
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "images")

# slug → OG に載せる見出し。\n を入れるとそこで改行する（入れなければ幅で自動改行）
# 1行は 32px で12字まで。はみ出したら自動で字を小さくする
TITLES = {
    "monooki-level-blocks":            "物置の水平出し｜設置の難所は組み立てではない",
    "monooki-diy-assembly":            "物置は自分で組み立てられる？ 大変なのは組み立てだけじゃない",
    "monooki-maker-assembly":          "物置の組みやすさは小型と中型・大型で逆転する",
    "monooki-options-and-anchor":      "物置のオプションは要る？基本は不要、でもアンカーは別",
    "monooki-size-and-placement":      "物置の置き方は誰が決める？サイズ選びの前に知ること",
    # ここから今回ぶん
    "kogata-chugata-ogata-chigai":     "小型と中型・大型は何が違う？\n物置は「区分」で見る",
    "homecenter-monooki-vs-major3":    "ホームセンターの物置と\n大手3社は、何が違うのか",
    "monooki-door-opening-side":       "物置の扉は、\nどっち側が開くのか",
    "monooki-removal-and-replacement": "古い物置は、\nどうやって撤去するのか",
    "monooki-okenai-basho":            "物置が置けない場所、\n置きにくい場所",
}

# 元の5枚を実測して合わせた寸法（600×315 を 2倍で書き出す）
PAGE = """<!doctype html><html><head><meta charset="utf-8">
<style>
  @font-face { font-family:'SMB1'; font-weight:700; font-display:block;
               src:url('_ogfonts/sm-lat-700.woff2') format('woff2');
               unicode-range:U+0000-00FF,U+2018-2019,U+201C-201D,U+2026; }
  @font-face { font-family:'SMB1'; font-weight:700; font-display:block;
               src:url('_ogfonts/sm-jp-700.woff2') format('woff2'); }
  * { margin:0; padding:0; box-sizing:border-box; }
  html,body { width:600px; height:315px; }
  body { background:#f8f6f0; -webkit-font-smoothing:antialiased; }
  .frame { position:absolute; left:11px; top:11px; right:11px; bottom:11px;
           border:1px solid #101010; }
  .hdr, .ftr { position:absolute; left:38px; right:38px;
               display:flex; justify-content:space-between; align-items:baseline; }
  .hdr { top:35px; }
  .ftr { top:267.5px; }
  .mono { font-family:'DejaVu Sans Mono',monospace; font-size:10px; line-height:14px;
          letter-spacing:.2em; color:#101010; }
  .rust { color:#a3512b; }
  .ftr .jp { font-family:'SMB1',serif; font-weight:700; font-size:9.5px;
             line-height:14px; letter-spacing:0; color:#101010; }
  .rule { position:absolute; left:38px; right:38px; height:1px; background:#101010; }
  .r1 { top:58px; } .r2 { top:256px; }
  .ttl { position:absolute; left:38px; top:58px; height:198px; width:400px;
         display:flex; flex-direction:column; justify-content:center;
         font-family:'SMB1',serif; font-weight:700; color:#101010;
         font-size:32px; line-height:46.5px; letter-spacing:0; }
  .ttl .ln { white-space:nowrap; }
  .ttl.s2 { font-size:28px; line-height:41px; }
  .ttl.s3 { font-size:25px; line-height:37px; }
  .shed { position:absolute; left:457px; top:196px; }
</style></head><body>
  <div class="frame"></div>
  <div class="hdr"><span class="mono">STORAGE CONCIERGE — 読みもの</span><span class="mono rust">JP</span></div>
  <div class="rule r1"></div>
  <div class="ttl __CLS__">__TITLE__</div>
  <svg class="shed" width="105" height="41" viewBox="0 0 105 41" fill="none"
       stroke="#7d7b76" stroke-width="1">
    <rect x="4.5" y="0.5" width="96" height="5.5"/>
    <rect x="8.5" y="12.5" width="87" height="25"/>
    <line x1="52" y1="12.5" x2="52" y2="37.5"/>
    <line x1="41.5" y1="18.5" x2="41.5" y2="31.5" stroke-width="2"/>
    <line x1="62.5" y1="18.5" x2="62.5" y2="31.5" stroke-width="2"/>
    <line x1="0" y1="40.5" x2="105" y2="40.5"/>
  </svg>
  <div class="rule r2"></div>
  <div class="ftr"><span class="jp">物置どれがいい？</span><span class="mono rust">TAKUBO / INABA / YODOKO</span></div>
</body></html>"""


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def run(slugs):
    from playwright.async_api import async_playwright
    for f in ("sm-jp-700.woff2", "sm-lat-700.woff2"):
        if not os.path.exists(os.path.join(FONTS, f)):
            print("[中止] フォントがありません:", os.path.join(FONTS, f))
            print("       docstring の手順で tools/_ogfonts/ に置いてください")
            return
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(HERE, "_page.html")
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 600, "height": 315}, device_scale_factor=2)
        for slug in slugs:
            title = TITLES[slug]
            # \n を入れた見出しは、そこで必ず折る（勝手に折り返させない）
            html = ("".join('<div class="ln">%s</div>' % esc(l) for l in title.split("\n"))
                    if "\n" in title else esc(title))
            # 3行に収まらなければ字を小さくする（元の5枚は 32px / 2行）
            cls = ""
            for c in ("", "s2", "s3"):
                open(tmp, "w", encoding="utf-8").write(
                    PAGE.replace("__TITLE__", html).replace("__CLS__", c))
                await pg.goto("file://" + tmp)
                await pg.wait_for_timeout(120)
                m = await pg.evaluate(
                    "(()=>{const e=document.querySelector('.ttl');"
                    "const r=document.createRange();r.selectNodeContents(e);"
                    "const w=Math.max(...[...r.getClientRects()].map(x=>x.width));"
                    "return [e.scrollHeight, Math.max(w, e.scrollWidth)]})()")
                cls = c
                if m[0] <= 198 and m[1] <= 400:
                    break
            dst = os.path.join(OUT, "og-%s.png" % slug)
            await pg.screenshot(path=dst)
            print("  %-34s %s  %s" % (slug, cls or "32px", dst))
        await b.close()
    if os.path.exists(tmp):
        os.replace(tmp, os.path.join(HERE, "_ogpage.last.html"))


def main():
    slugs = [a for a in sys.argv[1:] if not a.startswith("-")] or list(TITLES)
    print("[OG画像] %d 枚" % len(slugs))
    asyncio.run(run(slugs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
