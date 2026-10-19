#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tailwind のCSSを assets/tw.css に書き出す。

2026-10-16 まで、トップ・運営者情報・プライバシー・お問い合わせの4ページは
cdn.tailwindcss.com を読み込み、ブラウザの中でCSSを組み立てていた。
Tailwind 公式が「Play CDN は開発用で、本番向きではない」としているため、
公開のたびにここで書き出す形にした。

・設定は tools/tailwind.config.js が唯一の出典
・npx（node）が無い、またはネットに出られないときは、いま置いてある
  assets/tw.css をそのまま使い、警告だけ出す（公開は止めない）
・そのかわり tools/check-tailwind.py が「元のページが変わったのに
  CSSが古いまま」を見つけて、公開を止める
"""
import hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CFG = os.path.join(HERE, "tailwind.config.js")
SRC = os.path.join(HERE, "tailwind-in.css")
OUT = os.path.join(ROOT, "assets", "tw.css")
STAMP = OUT + ".stamp"
VERSION = "tailwindcss@3.4.17"
PAGES = ["index.html", "about.html", "privacy.html", "contact.html"]


def stamp_now():
    """設定と、CSSの元になる4ページの中身から指紋を作る"""
    h = hashlib.sha256()
    h.update(VERSION.encode())
    for p in [CFG] + [os.path.join(ROOT, x) for x in PAGES]:
        h.update(b"\0")
        if os.path.exists(p):
            with open(p, "rb") as f:
                h.update(f.read())
    return h.hexdigest()


def main():
    if not os.path.exists(CFG) or not os.path.exists(SRC):
        print("[警告] Tailwind の設定が見つかりません（tools/tailwind.config.js）")
        return 0
    if not shutil.which("npx"):
        print("[警告] npx が見つかりません。いまの assets/tw.css をそのまま使います")
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cmd = ["npx", "--yes", VERSION, "-c", CFG, "-i", SRC, "-o", OUT, "--minify"]
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=240)
    except Exception as e:
        print("[警告] Tailwind を動かせませんでした（%s）。いまの assets/tw.css を使います" % e)
        return 0
    if r.returncode != 0:
        print("[警告] Tailwind の書き出しに失敗しました。いまの assets/tw.css を使います")
        print((r.stderr or r.stdout or "").strip()[:400])
        return 0
    with open(STAMP, "w", encoding="utf-8") as f:
        f.write(stamp_now() + "\n")
    print("[Tailwind] assets/tw.css を書き出しました（%.1f KB）" % (os.path.getsize(OUT) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
