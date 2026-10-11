#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事の見出しを、文節のうしろで区切る。

日本語は既定だと文字単位で折り返すので、見出しが「でもアンカー／は別」のように
語の途中で切れる。word-break: auto-phrase は文節で折り返す指定だが、
対応しているのは Chrome 系だけで、Safari と Firefox には効かない。

そこで見出しを句読点と助詞（を・に・は・が・で・と・へ・も・の）のうしろで区切り、inline-block の塊にしておく。
塊の中は優先的に切れないので、どのブラウザでも区切った位置で折り返す。
助詞の直前がひらがなのときは区切らない（「ありがとう」の「が」で切ると
「ありが／とうございました」になるため）。index.html の診断側と同じ規則。

対象は articles/*.html の記事タイトルと本文の h2・h3、
それに記事一覧のカードの見出し。何度流しても結果は同じ。
publish.sh から自動で呼ばれる。
"""
import glob, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STOP = set('、。？！')
JOSHI = set('をにはがでとへもの')
CSS_MARK = '.article-title, .article-lead, .article-body h2, .article-body h3,'
PB_CSS = '  .pb { display: inline-block; }\n'


def kana(c):
    return 'ぁ' <= c <= 'ん'


def chunks(t):
    """文節のうしろで切る。切れ目が無ければ1つだけ返す"""
    parts, cur = [], ''
    n = len(t)
    for i, c in enumerate(t):
        cur += c
        if i + 1 >= n:
            break
        nx, pv = t[i + 1], (t[i - 1] if i else '')
        if c in STOP or (c in JOSHI and pv and not kana(pv) and nx not in STOP):
            parts.append(cur)
            cur = ''
    if cur:
        parts.append(cur)
    return parts


def wrap(t):
    cs = chunks(t)
    if len(cs) < 2:
        return None
    return ''.join('<span class="pb">%s</span>' % c for c in cs)


PATS = [
    r'(<h1 class="article-title">)(.*?)(</h1>)',
    r'(<h2 class="card-title">)(.*?)(</h2>)',
    r'(<h2>)([^<]*?)(</h2>)',
    r'(<h3>)([^<]*?)(</h3>)',
]


def main():
    files = [f for f in sorted(glob.glob(os.path.join(ROOT, 'articles', '*.html')))]
    n_files, n_heads = 0, 0
    for f in files:
        s = io.open(f, encoding='utf-8').read()
        orig = s

        def sub(m):
            global_n = None
            head, body, tail = m.group(1), m.group(2), m.group(3)
            if '<' in body or 'class="pb"' in body:
                return m.group(0)
            w = wrap(body)
            return m.group(0) if w is None else head + w + tail

        for pat in PATS:
            s, k = re.subn(pat, sub, s, flags=re.S)
        n = s.count('<span class="pb">') - orig.count('<span class="pb">')

        # .pb のCSSを足す（折り返しの指定を入れた場所の隣に）
        if '.pb { display: inline-block; }' not in s:
            if CSS_MARK in s:
                i = s.find(CSS_MARK)
                j = s.find('}', i) + 1
                s = s[:j] + '\n' + PB_CSS.rstrip('\n') + s[j:]
            elif '</style>' in s:
                j = s.find('</style>')
                s = s[:j] + PB_CSS + s[j:]

        if s != orig:
            io.open(f, 'w', encoding='utf-8').write(s)
            n_files += 1
            n_heads += n
    print('[見出しの折り返し] %d ファイル／見出し %d 個を区切りました' % (n_files, n_heads))
    return 0


if __name__ == '__main__':
    sys.exit(main())
