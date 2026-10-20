#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全ページに Google アナリティクス（GA4）のタグを入れる。

2026-09-29 導入。それまで計測タグが1枚も入っておらず、
読者がサイト内のどこで離脱しているかも、提携先を押した回数も
分からない状態だった。

    python3 tools/build-analytics.py

タグを変えるときは MEASUREMENT_ID だけ直せばよい。
プライバシーポリシー（privacy.html）にも記載があるので、
外すときはそちらも直すこと。
"""
import os, re, io, glob, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MEASUREMENT_ID = "G-B5453D0GBM"

START = "<!-- ANALYTICS_START -->"
END = "<!-- ANALYTICS_END -->"

BLOCK = """%s
<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', '%s');
  /* 提携先（バリューコマース経由）のクリックを数える。
     読者が最後まで進んだかを見る唯一の出口なので、ここだけは必ず取る。
     2026-10-20 まで page_path と URL しか送っておらず、
     「どのページ種別の、どの置き場所で、どのシリーズが押されたか」が分からなかった。
     提携リンクは33ページから90ページに増えたので、ここを分けないと次の判断ができない。 */
  function adPageType(p) {
    if (p === '/' || p === '/index.html') return 'top';
    if (p.indexOf('/articles/') === 0) return 'article';
    if (p === '/products/codes.html') return 'codes';
    if (p === '/products/discontinued.html') return 'discontinued';
    if (p.indexOf('/products/') === 0) return 'product';
    if (p.indexOf('/size/band-') === 0) return 'size_band';
    if (p.indexOf('/size/') === 0) return 'size';
    return 'other';
  }
  function adPlacement(a) {
    var c = ' ' + (a.getAttribute('class') || '') + ' ';
    if (c.indexOf(' band-ad ') >= 0) return 'band_row';      /* サイズ帯のシリーズ行 */
    if (c.indexOf(' vis-tag ') >= 0) return 'index_tag';     /* 索引カードの絵の右上 */
    if (c.indexOf(' aff-quiz ') >= 0) return 'quiz_result';  /* 診断の結果 */
    if (c.indexOf(' hero-photo ') >= 0) return 'hero_photo'; /* 製品ページの写真 */
    if (c.indexOf(' shop ') >= 0) return 'product_exit';     /* 製品ページの出口 */
    if (a.closest && a.closest('.rel-ad-list')) return 'article_tail';
    return 'other';
  }
  function adDest(href) {
    /* 行き先は vc_url に入っている。何重かエンコードされているので戻してから読む */
    var s = String(href), i, d;
    for (i = 0; i < 4; i++) {
      try { d = decodeURIComponent(s); } catch (err) { break; }
      if (d === s) break;
      s = d;
    }
    var m = s.match(/se_series=series:([A-Za-z0-9_]+)/);
    var series = m ? m[1] : '';
    if (!series) { m = s.match(/search_word_like_ex=([^&]+)/); if (m) series = 'word:' + m[1]; }
    return {
      series: series.slice(0, 100),
      cat: /public_item_wh_/.test(s) ? 'wh' : (/public_item_mo_/.test(s) ? 'mo' : '')
    };
  }
  document.addEventListener('click', function (e) {
    try {
      var t = e.target;
      var a = (t && t.closest) ? t.closest('a[href]') : null;
      if (!a || !/valuecommerce\\.com/.test(a.href)) return;
      var d = adDest(a.href);
      gtag('event', 'affiliate_click', {
        page_path: location.pathname,
        page_type: adPageType(location.pathname),
        ad_placement: adPlacement(a),
        ad_series: d.series,
        ad_cat: d.cat,
        link_url: String(a.href).slice(0, 100)
      });
    } catch (err) { /* 計測で本文の動きを止めない */ }
  }, true);
</script>
%s""" % (START, MEASUREMENT_ID, MEASUREMENT_ID, END)


def main():
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html"))
                   + glob.glob(os.path.join(ROOT, "*", "*.html")))
    if not pages:
        raise SystemExit("[中止] ページが1枚も見つかりません。")
    n, skipped = 0, []
    for p in pages:
        s = io.open(p, encoding="utf-8").read()
        # いったん外してから入れ直す。差し込み位置を変えたときに
        # 古い位置に残らないようにするため。
        s2 = re.sub(r"\n?" + re.escape(START) + r".*?" + re.escape(END), "", s,
                    flags=re.S)
        # charset の宣言は先頭付近に置く決まりなので、その後ろに入れる。
        # viewport があればさらにその後ろ。
        m = (re.search(r'<meta name="viewport"[^>]*>\s*\n', s2)
             or re.search(r"<meta charset=[^>]*>\s*\n", s2))
        if not m:
            skipped.append(os.path.relpath(p, ROOT)); continue
        s2 = s2[:m.end()] + BLOCK + "\n" + s2[m.end():]
        if s2 != s:
            io.open(p, "w", encoding="utf-8").write(s2)
            n += 1
    if skipped:
        raise SystemExit("[中止] <head> が見つからないページがあります: %s"
                         % "／".join(skipped))
    have = sum(1 for p in pages
               if START in io.open(p, encoding="utf-8").read())
    if have != len(pages):
        raise SystemExit("[中止] %d ページ中 %d ページにしか入っていません。"
                         % (len(pages), have))
    print("[アナリティクス] %s ／ %d ページ中 %d ページを更新（全ページ設置済み）"
          % (MEASUREMENT_ID, len(pages), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
