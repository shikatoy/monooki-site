#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
製品ページ（products/*.html）の「仕様」表と「特徴」を、index.html の PRODUCTS から作り直す。

サイズ表だけが同期されていて、仕様・特徴は手で直す作りだった。
2026-09-29、como lite の扉の記述（実際は GM タイプだけの説明だった）と
SMX のサイズ数が、データとページで食い違ったまま公開された。以後はここで作る。

    python3 tools/build-product-spec.py
"""
import os, re, io, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAKER_JP = {"takubo": "タクボ", "inaba": "イナバ", "yodoko": "ヨドコウ"}
ROWS = ("メーカー", "区分", "鋼板", "扉", "基礎")


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def products():
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    pages = dict(re.findall(r"'([a-z0-9\-]+)':\s*'(products/[^']+)'", s))
    i = s.index("const PRODUCTS"); i = s.index("[", i)
    depth, objs, buf = 0, [], None
    for j in range(i, len(s)):
        c = s[j]
        if c == "{":
            if depth == 0: buf = j
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: objs.append(s[buf:j + 1])
        elif c == "]" and depth == 0:
            break
    out = []
    for o in objs:
        pid = re.search(r"id:'([^']+)'", o).group(1)
        get = lambda k: (re.search(k + r":'([^']*)'", o).group(1)
                         if re.search(k + r":'", o) else "")
        fm = re.search(r"features:\[(.*?)\]", o, re.S)
        feats = re.findall(r"'([^']*)'", fm.group(1)) if fm else []
        out.append(dict(id=pid, page=pages.get(pid, ""),
                        vals={"メーカー": MAKER_JP.get(get("maker"), get("maker")),
                              "区分": get("cat"), "鋼板": get("steel"),
                              "扉": get("door"), "基礎": get("found")},
                        feats=feats))
    return out


def main():
    n = 0
    for p in products():
        if not p["page"]:
            raise SystemExit("[中止] %s に製品ページの対応が無い。index.html の対応表に足してください。"
                             % p["id"])
        f = os.path.join(ROOT, p["page"])
        if not os.path.exists(f):
            raise SystemExit("[中止] %s のページが見つかりません: %s" % (p["id"], p["page"]))
        s = io.open(f, encoding="utf-8").read()

        tbl = re.search(r'(<table class="spec">.*?</table>)', s, re.S)
        ul = re.search(r'(<h2>特徴</h2>\s*<ul>.*?</ul>)', s, re.S)
        if not tbl or not ul:
            raise SystemExit("[中止] %s に仕様表または特徴の並びがありません。"
                             "雛形を変えたなら、このスクリプトも直してください。" % p["page"])

        body = "\n".join("          <tr><th>%s</th><td>%s</td></tr>"
                         % (k, esc(p["vals"][k])) for k in ROWS if p["vals"][k])
        new_tbl = ('<table class="spec">\n          <tbody>\n%s\n'
                   '          </tbody>\n        </table>' % body)
        items = "\n".join("        <li>%s</li>" % esc(x) for x in p["feats"])
        new_ul = '<h2>特徴</h2>\n\n        <ul>\n%s\n        </ul>' % items

        s2 = s[:tbl.start(1)] + new_tbl + s[tbl.end(1):]
        ul = re.search(r'(<h2>特徴</h2>\s*<ul>.*?</ul>)', s2, re.S)
        s2 = s2[:ul.start(1)] + new_ul + s2[ul.end(1):]

        if s2 != s:
            io.open(f, "w", encoding="utf-8").write(s2)
            print("  %-36s 仕様%d行 / 特徴%d"
                  % (os.path.basename(p["page"]),
                     sum(1 for k in ROWS if p["vals"][k]), len(p["feats"])))
            n += 1
    print("[製品ページの仕様・特徴] %d ページを更新しました" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
