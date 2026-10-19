#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assets/tw.css が、いまのページと設定から作られたものかを見る。

書き出しに失敗したまま公開すると、クラスを足したところだけ素のまま出る。
画面では気づきにくいので、ここで止める。
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util
spec = importlib.util.spec_from_file_location("bt", os.path.join(HERE, "build-tailwind.py"))
bt = importlib.util.module_from_spec(spec); spec.loader.exec_module(bt)


def main():
    if not os.path.exists(bt.OUT):
        print("[中止] assets/tw.css がありません。python3 tools/build-tailwind.py を実行してください")
        return 1
    if not os.path.exists(bt.STAMP):
        print("[中止] assets/tw.css.stamp がありません。python3 tools/build-tailwind.py を実行してください")
        return 1
    with open(bt.STAMP, encoding="utf-8") as f:
        old = f.read().strip()
    now = bt.stamp_now()
    if old != now:
        print("[中止] assets/tw.css が、いまのページより古いままです。")
        print("       ページか tools/tailwind.config.js が変わったのに、CSSを書き出せていません。")
        print("       ネットに出られる場所で python3 tools/build-tailwind.py を実行してから公開してください。")
        return 1
    print("[Tailwind] assets/tw.css は最新です（%.1f KB）" % (os.path.getsize(bt.OUT) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
