#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""git に入れていないファイルの控えを取る。

リポジトリ（shikatoy/monooki-site）は公開設定なので、次の2つは git に入れていない。
  _ledger/   サイトの作りを変えたときの記録（改定）。読者に向けたものではない
  _output/   記事の原稿（.md）。下書きを公開リポジトリに上げない

そのぶん、バージョン履歴もバックアップも無い状態になっていた。

置き場所はリポジトリの隣（Documents/monooki-private-backups）。
消し間違いや取り違えからは守れるが、同じディスクなのでディスクごと失う事故には備えていない。
そこまで必要になったら DESTS に行き先を足せばよい（書けた場所すべてに置く作り）。

1か所も書けなかったときだけ警告を出す。公開そのものは止めない。
日付ごとに1つ作り、同じ日に2回目を実行しても上書きしない（その日の最初の状態が残る）。
latest/ は毎回上書きするので、いまの中身はここを見れば分かる。

    python3 tools/backup-private.py
"""
import datetime, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = ["_ledger", "_output"]
# ~ を使うと、実行した場所によって別のホームに解決されてしまう。
# リポジトリの隣に置く形にすれば、どこから走らせても同じ場所になる。
# 2026-10-20 まで外付け（/Volumes/Untitled/backups）も行き先に入れていたが、
# 中身が空のまま一度も使われておらず、抜くたびに警告が出るだけだったので外した。
# 増やすときはこの配列に1行足せばよい（書けた場所すべてに置く作り）
DESTS = [os.path.join(os.path.dirname(ROOT), "monooki-private-backups")]


def copy_into(base, sub):
    out = os.path.join(base, sub)
    n = 0
    for name in SRC:
        s = os.path.join(ROOT, name)
        if not os.path.isdir(s):
            continue
        d = os.path.join(out, name)
        try:
            # 消してから作り直すと、削除が禁止されている置き場所（接続フォルダなど）で失敗する。
            # 上書きで重ねる。元から消えたファイルは控えに残るが、
            # _ledger も _output も増える一方なので実害は無い
            shutil.copytree(s, d, dirs_exist_ok=True)
            n += sum(len(f) for _, _, f in os.walk(d))
        except Exception as e:
            raise RuntimeError("%s へ書けません: %s" % (d, e))
    return n


def main():
    if not any(os.path.isdir(os.path.join(ROOT, x)) for x in SRC):
        print("[控え] 控えるものがありません"); return 0
    today = datetime.date.today().isoformat()
    ok, ng = [], []
    for base in DESTS:
        try:
            os.makedirs(base, exist_ok=True)
            n = copy_into(base, "latest")
            dated = os.path.join(base, today)
            if not os.path.isdir(dated):
                copy_into(base, today)
                tag = "＋%s" % today
            else:
                tag = "（%s は作成済み）" % today
            ok.append("%s %d件%s" % (base, n, tag))
        except Exception as e:
            ng.append("%s … %s" % (base, str(e)[:70]))
    for x in ok:
        print("[控え] ", x)
    for x in ng:
        print("[控え] 書けませんでした: ", x)
    if not ok:
        print("[警告] どこにも控えを取れませんでした。置き場所を確認してください。")
        return 0          # 公開そのものは止めない
    return 0


if __name__ == "__main__":
    sys.exit(main())
