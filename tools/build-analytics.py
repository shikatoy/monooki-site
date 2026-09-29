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
     読者が最後まで進んだかを見る唯一の出口なので、ここだけは必ず取る。 */
  document.addEventListener('click', function (e) {
    var t = e.target;
    var a = (t && t.closest) ? t.closest('a[href]') : null;
    if (!a || !/valuecommerce\\.com/.test(a.href)) return;
    gtag('event', 'affiliate_click', {
      page_path: location.pathname,
      link_url: String(a.href).slice(0, 100)
    });
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
