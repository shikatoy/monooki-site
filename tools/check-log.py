#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新履歴の台帳（data/update-log.json）を公開前に検査する。

台帳は 2026-10-16 に index.html から外へ出した。
画面には読み込んでから出すので、形が崩れていると更新履歴の欄が空になる。
壊れたまま公開しないよう、publish.sh から呼ばれる。

・公開する台帳に「改定」が混じっていないか（混じると読者に向けていない記録が出る）
・JSON として読めるか
・date / type / title が揃っているか。date は YYYY-MM-DD か
・type が決められた6種のどれかか
・新しい順に並んでいるか
・index.html に配列が残っていないか（二重管理を防ぐ）
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "data", "update-log.json")
PRIVATE = os.path.join(ROOT, "_ledger", "kaitei-log.json")
TYPES = {"公開", "新商品", "廃盤", "入替", "改定", "メーカー発表", "訂正"}
# data/ はサイトと一緒に公開される（誰でも・どのクローラーでも読める）。
# サイトの作りを変えたときの記録（改定）は読者に向けたものではないので、
# 公開しない _ledger/kaitei-log.json に置く。2026-10-19 に分けた
PUBLIC_TYPES = {"公開", "新商品", "廃盤", "入替", "メーカー発表", "訂正"}


def main():
    bad = []
    if not os.path.exists(LOG):
        print("[中止] data/update-log.json がありません")
        return 1
    try:
        with open(LOG, encoding="utf-8") as f:
            log = json.load(f)
    except Exception as e:
        print("[中止] data/update-log.json を読めません: %s" % e)
        return 1
    if not isinstance(log, list) or not log:
        print("[中止] data/update-log.json が配列ではありません")
        return 1

    for n, e in enumerate(log, 1):
        if not isinstance(e, dict):
            bad.append("%d件目: 記録になっていません" % n); continue
        for k in ("date", "type", "title"):
            if not e.get(k):
                bad.append("%d件目: %s がありません" % (n, k))
        d = e.get("date", "")
        if d and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            bad.append("%d件目: 日付の形が違います（%s）" % (n, d))
        t = e.get("type")
        if t and t not in TYPES:
            bad.append("%d件目: 知らない種類です（%s）" % (n, t))

    ds = [e.get("date", "") for e in log if isinstance(e, dict)]
    for i in range(len(ds) - 1):
        if ds[i] < ds[i + 1]:
            bad.append("並びが前後しています: %s のあとに %s" % (ds[i], ds[i + 1]))

    for n, e in enumerate(log, 1):
        if isinstance(e, dict) and e.get("type") not in PUBLIC_TYPES:
            bad.append("%d件目: 「%s」は公開する台帳に置けません（_ledger/kaitei-log.json へ）"
                       % (n, e.get("type")))

    idx = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    if re.search(r"const UPDATE_LOG\s*=\s*\[", idx):
        bad.append("index.html に配列が残っています（台帳は data/update-log.json だけに置く）")

    if bad:
        print("[中止] 更新履歴の台帳に問題があります")
        for b in bad[:20]:
            print("   -", b)
        if len(bad) > 20:
            print("   … ほか %d 件" % (len(bad) - 20))
        return 1

    from collections import Counter
    c = Counter(e["type"] for e in log)
    msg = "[更新履歴] 公開 %d 件 / %s" % (len(log), " ".join("%s%d" % (k, v) for k, v in c.most_common()))
    if os.path.exists(PRIVATE):
        try:
            with open(PRIVATE, encoding="utf-8") as f:
                msg += " ／ 公開しない台帳 %d 件" % len(json.load(f))
        except Exception as e:
            print("[中止] _ledger/kaitei-log.json を読めません: %s" % e)
            return 1
    else:
        msg += " ／ 公開しない台帳は見当たりません"
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
