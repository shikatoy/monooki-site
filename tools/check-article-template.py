#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
記事の雛形（tools/_article_template.html）が、まだ記事を出せる形かを確かめる。

なぜ必要か（2026-10-29）
  記事の公開は publish-article.py が雛形を1か所ずつ差し替えて作る。
  その雛形を、publish.sh の中の別の生成スクリプトが書き換えることがある。
  実際 build-breadcrumbs.py が雛形にも BreadcrumbList の構造化データを足し、
  ld+json の塊が2つになった。publish-article.py は「ld+json はひとつ」を
  当てにしていたので、どの記事を流しても

      [中止] 差し替え箇所が 2 件: JSON-LD

  で止まる状態になった。publish-article.py は publish.sh から呼ばれないため、
  公開のたびの検査では一度も触れられず、10日のあいだ誰も気づかなかった。

  壊れていることが分かるのを「次に記事を出そうとしたとき」ではなく
  「次に publish.sh を流したとき」にするのが、この検査の目的。

見るもの
  1. publish-article.py の SLOTS が、雛形にちょうど1か所ずつ見つかるか
  2. 仮の記事を1本、最後まで組み立てられるか（書き出しはしない）

    python3 tools/check-article-template.py
"""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PUB = os.path.join(HERE, "publish-article.py")

# 組み立てが最後まで通るか試すための仮の記事。どこにも書き出さない。
DUMMY_FM = {
    "slug": "_template-check",
    "title": "雛形の点検用",
    "description": "この記事は書き出されません。雛形が壊れていないかを確かめるためだけのものです。",
    "keywords": ["点検"],
    "date": "2026-01-01",
}
DUMMY_BODY = "<p>点検用の本文です。</p>"


def load_publisher():
    if not os.path.exists(PUB):
        print("[中止] tools/publish-article.py がありません。")
        return None
    spec = importlib.util.spec_from_file_location("publish_article", PUB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    P = load_publisher()
    if P is None:
        return 1

    if not os.path.exists(P.TEMPLATE):
        print("[中止] 記事の雛形がありません: %s" % os.path.relpath(P.TEMPLATE, ROOT))
        return 1

    shell = P.template_shell()
    bad = []
    for label, pat in P.SLOTS:
        n = len(re.findall(pat, shell, flags=re.S))
        if n != 1:
            bad.append((label, n))

    if bad:
        print("[中止] 記事の雛形の差し替え箇所が、1か所ずつになっていません。")
        for label, n in bad:
            print("       %-20s %d件" % (label, n))
        print("       このままだと publish-article.py が止まり、記事を1本も出せません。")
        print("       tools/_article_template.html を直してください。")
        print("       直前に雛形を書き換えた生成スクリプトがないか、")
        print("       publish.sh の build-* を疑うと早いです。")
        return 1

    # 差し替えが1か所ずつでも、組み立ての途中で落ちることはある。最後まで通す。
    try:
        page = P.build_page(DUMMY_FM, None, DUMMY_BODY, P.TAGS[0])
    except SystemExit as e:
        print("[中止] 仮の記事を組み立てられませんでした。")
        print("       %s" % e)
        return 1
    except Exception as e:
        print("[中止] 仮の記事の組み立てで例外が出ました: %s: %s"
              % (type(e).__name__, e))
        return 1

    for must in (DUMMY_FM["title"], DUMMY_FM["date"], DUMMY_BODY):
        if must not in page:
            print("[中止] 組み立てた記事に「%s」が入っていません。"
                  "差し替えが効いていない箇所があります。" % must)
            return 1

    print("[記事の雛形] 差し替え箇所 %d か所、仮の記事の組み立てまで通りました"
          % len(P.SLOTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
