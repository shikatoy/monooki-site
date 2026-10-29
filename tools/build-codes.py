#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""型番から引ける索引（products/codes.html）を作る。

見積書や既存の物置に書かれた型番から、寸法とシリーズに辿り着けるようにする。
型番はカタログにしか載っていないことが多く、Web上で引ける場所が少ない。
データは index.html の PRODUCTS が唯一の出典。
"""
import importlib.util, json, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "_common_page.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

OUT = os.path.join(C.ROOT, "products", "codes.html")


def build():
    prods = C.load_products()
    LOAD = C.floor_load()
    groups = []
    total = 0
    for p in sorted(prods, key=lambda x: (x["maker"], x["name"])):
        if not p["sizes"]:
            continue
        pre = sorted({re.match(r"^[A-Za-z]+", c).group(0) for c, *_ in p["sizes"]
                      if re.match(r"^[A-Za-z]+", c)})
        groups.append((p, pre))
        total += len(p["sizes"])
    groups.sort(key=lambda g: g[1][0] if g[1] else "zz")

    # 接頭辞が同じシリーズが並ぶと見分けが付かないので、重複するものだけ名前を添える
    labels = ["／".join(g[1]) or g[0]["name"] for g in groups]
    dup = {x for x in labels if labels.count(x) > 1}
    jump = "".join(
        '<a href="#%s">%s%s</a>'
        % (g[0]["id"], C.esc(lab),
           ('<span class="jump-n">%s</span>' % C.esc(g[0]["name"])) if lab in dup else "")
        for g, lab in zip(groups, labels))

    body_parts = []
    for p, pre in groups:
        # 見出しは summary に。全型番は閉じた details の中に残す（HTMLからは消えない）
        head = ('<summary class="grp"><h2>%s</h2><p>%s — %s — %d型番%s</p>'
                '<span class="grpd-mk" aria-hidden="true"></span></summary>'
                % (C.esc(p["name"]),
                   C.MAKER_JP[p["maker"]], C.esc(C.KUBUN.get(p["cat"], p["cat"])), len(p["sizes"]),
                   "（型番の頭：" + "／".join(pre) + "）" if pre else ""))
        # 床耐荷重（タクボ公式の型番ページ）。そのシリーズの型番が全部そろって
        # いるときだけ列にする。一部だけだと空欄が0kgに見える。
        kg = all(c in LOAD for c, *_ in p["sizes"])
        rows = "".join(
            '<tr><td class="l m">%s</td><td>%s</td><td>%s</td><td>%s</td>%s</tr>'
            % (C.esc(c), "{:,}".format(w), "{:,}".format(d), "{:,}".format(h),
               ('<td>%skg</td>' % "{:,}".format(LOAD[c])) if kg else "")
            for c, w, d, h in sorted(p["sizes"], key=lambda s: s[0]))
        inner = ""
        if p["page"]:
            inner += ('<p class="grpd-to"><a href="%s">%sの寸法と仕様 →</a></p>'
                      % (os.path.basename(p["page"]), C.esc(p["name"])))
        if p.get("codeNote"):
            inner += '<p class="note">%s</p>' % p["codeNote"]
        if kg:
            inner += ('<p class="note">床耐荷重はタクボ公式の型番ページに載っている値です。'
                      '物置1棟あたりの合計で、面積あたりの値ではありません。</p>')
        inner += ('<table class="tbl"><thead><tr><th class="l">型番</th>'
                  '<th>間口 mm</th><th>奥行 mm</th><th>高さ mm</th>%s</tr></thead>'
                  '<tbody>%s</tbody></table>'
                  % ('<th>床耐荷重</th>' if kg else "", rows))
        body_parts.append('<details class="grpd" id="%s">%s<div class="grpd-in">%s</div></details>'
                          % (p["id"], head, inner))

    h1 = "型番から探す"
    desc = ("タクボ・イナバ・ヨドコウの物置 全型番の索引です。見積書やカタログに書かれた型番から、"
            "間口・奥行・高さとシリーズを引けます。")
    url = C.SITE + "products/codes.html"

    body = """
    <div class="page-head">
      <p class="page-kicker">Model Codes — 型番から探す</p>
      <h1 class="page-title">型番から探す。</h1>
      <p class="page-lead">見積書に書かれている記号、いま使っている物置に貼ってある型番。<b>それが何のシリーズで、どんな寸法なのか</b>を引くための索引です。タクボ・イナバ・ヨドコウの<b>全%(total)d型番</b>を、シリーズごとにまとめています。</p>
    </div>

    <div class="note">
      <label for="code-q" style="display:block;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#6b6b6b">型番で絞る</label>
      <input id="code-q" type="search" inputmode="latin" autocomplete="off" spellcheck="false"
             placeholder="例：FS-2215S／LMD-2515／GP-115D"
             style="width:100%%;margin-top:10px;padding:12px 2px;border:0;border-bottom:1px solid #161616;background:transparent;font-family:'IBM Plex Mono',monospace;font-size:20px;letter-spacing:.06em;outline:none;border-radius:0">
      <p id="code-hit" style="margin:10px 0 0;font-family:'IBM Plex Mono',monospace;font-size:11px;color:#6b6b6b;min-height:1.2em"></p>
      <p style="margin:14px 0 0">※打ち込んだ文字を含む型番だけが残ります。シリーズ名でも絞れます。該当するシリーズはひとりでにひらきます。検索から型番で来られた方は、すでに絞り込まれた状態で表示されます。<b>見当たらないときは、生産が終わっている可能性があります。</b>ただし、ここに並べているのは<b>一般型の型番だけ</b>です。タクボの多雪型（ND-S2215 のようにSが入るもの）は載せていません。Sを外した型番で引いてみてください。寸法は同じです。<a href="discontinued.html">廃盤・生産終了</a>のページに、公式発表で確認できたものを記録しています。</p>
      <p style="margin:14px 0 0">※旧型番の寸法は載せていません。買い替え先をさがすときは、<b>いま置いてある物置を実際に測って</b>、<a href="../size/">寸法から探す</a>で当たるのが確実です。型番の数字は、メーカーが違えば指す寸法も違います。</p>
    </div>

    <div class="note">
      <p style="margin:0">※型番の頭の英字でシリーズが分かります。たとえば <b>GP</b> はタクボのグランプレステージ ジャンプ、<b>FS</b> はイナバのフォルタ、<b>LMD</b> はヨドコウのエルモです。下のボタンから飛べます。</p>
      <p style="margin:14px 0 0">※<b>各社で数字の付け方が似ていても、実際の寸法は同じではありません。</b>たとえば型番に「2215」を含むものは3社にありますが、間口は2,200／2,210／2,220mm、奥行は1,530〜1,590mmと差があります。<b>買い替えのときは、型番の数字ではなく実寸で確認してください。</b></p>
      <p style="margin:14px 0 0">※寸法は各メーカーの公表値をもとにしています。ご購入前に必ず公式サイト・最新カタログでご確認ください。</p>
    </div>

    <div class="jump">%(jump)s</div>

    <div class="grpd-bar">
      <p class="grpd-note">全%(total)d型番は、シリーズごとに畳んであります。見出しを押すとひらきます。</p>
      <button type="button" id="code-all" class="grpd-all" aria-expanded="false">全部ひらく</button>
    </div>

%(groups)s

    <div class="cta">
      <p class="cta-label">Next — 次に</p>
      <p class="cta-title">型番が分かったら。</p>
      <p class="cta-text">シリーズごとの仕様は機種ごとのページに、置ける寸法から絞り込む一覧は「寸法から探す」にまとめています。廃盤になった物置は別ページに記録しています。</p>
      <a class="cta-btn" href="./">製品一覧を見る <span class="arrow">→</span></a>
    </div>

    <script>
    /* 型番の絞り込みと開閉。
       全型番はHTMLに残したまま、既定では閉じた details の中に置いている。
       打った文字を含む行だけ残し、該当するシリーズはひらく。残りが無いシリーズは隠す */
    (function(){
      var q   = document.getElementById('code-q');
      var hit = document.getElementById('code-hit');
      var all = document.getElementById('code-all');
      var secs = [].map.call(document.querySelectorAll('.grpd'), function(d){
        var tbl = d.querySelector('table.tbl');
        var sum = d.querySelector('summary');
        return { d: d,
                 rows: tbl ? [].slice.call(tbl.tBodies[0].rows) : [],
                 name: ((sum || d).textContent || '').toUpperCase() };
      });
      if(!secs.length) return;
      var norm = function(t){ return t.toUpperCase().replace(/[\s　ー−―‐]/g, ''); };
      function anyOpen(){ return secs.some(function(s){ return s.d.open && s.d.style.display !== 'none'; }); }
      function sync(){
        if(!all) return;
        var o = anyOpen();
        all.textContent = o ? '全部たたむ' : '全部ひらく';
        all.setAttribute('aria-expanded', o ? 'true' : 'false');
      }
      var lastV = '';
      function run(){
        var v = q ? norm(q.value.trim()) : '';
        var n = 0, k = 0;
        secs.forEach(function(s){
          var shown = 0;
          var byName = v && s.name.indexOf(v) >= 0;
          s.rows.forEach(function(r){
            var ok = !v || byName || norm(r.cells[0].textContent).indexOf(v) >= 0;
            r.style.display = ok ? '' : 'none';
            if(ok) shown++;
          });
          var vis = !v || shown > 0;
          s.d.style.display = vis ? '' : 'none';
          if(v){ s.d.open = vis; }
          else if(lastV){ s.d.open = false; }   /* 絞り込みを消したら畳んだ状態に戻す */
          n += shown;
          if(vis) k++;
        });
        lastV = v;
        if(hit) hit.textContent = v
          ? (n ? n.toLocaleString() + '型番 ／ ' + k + 'シリーズ'
               : '見当たりません。廃盤のページも見てみてください')
          : '';
        sync();
      }
      /* ?q=ESF-1805A で来たとき、または #ESF-1805A のとき、最初から絞り込んだ状態で出す。
         2026-10-19 にシリーズごとに畳む形へ変えたため、型番で検索して着地した人が
         畳まれた画面に当たり、もう一度打ち直す必要が出ていた */
      function seed(){
        if(!q) return false;
        var v = '';
        try {
          v = new URLSearchParams(location.search).get('q') || '';
        } catch(e){}
        if(!v){
          var h = decodeURIComponent(location.hash.slice(1) || '');
          /* 見出しのidは英小文字と「-」だけ。型番は英大文字と数字を含むので見分けられる */
          if(h && /[A-Z0-9]/.test(h) && !document.getElementById(h)) v = h;
        }
        if(!v) return false;
        q.value = v;
        run();
        return true;
      }
      if(q) q.addEventListener('input', run);
      if(all) all.addEventListener('click', function(){
        var o = anyOpen();
        secs.forEach(function(s){ if(s.d.style.display !== 'none') s.d.open = !o; });
        sync();
      });
      secs.forEach(function(s){ s.d.addEventListener('toggle', sync); });
      /* #FS のような指定で来たとき、頭文字のボタンを押したときは、そのシリーズをひらく */
      function openHash(){
        var id = location.hash.slice(1);
        if(!id) return;
        var el = document.getElementById(id);
        if(el && el.tagName === 'DETAILS'){ el.open = true; el.scrollIntoView(); sync(); }
      }
      [].forEach.call(document.querySelectorAll('.jump a'), function(a){
        a.addEventListener('click', function(){
          var el = document.getElementById((a.getAttribute('href') || '').slice(1));
          if(el && el.tagName === 'DETAILS'){ el.open = true; sync(); }
        });
      });
      window.addEventListener('hashchange', openHash);
      if(!seed()){ run(); openHash(); }
    })();
    </script>

    <div class="links">
      <a href="./">製品一覧</a>
      <a href="../size/">寸法から探す</a>
      <a href="discontinued.html">廃盤・生産終了</a>
      <a href="../#shindan">物置マッチング診断</a>
    </div>
""" % dict(total=total, jump=jump, groups="\n".join(body_parts))

    coll = {"@context": "https://schema.org", "@type": "CollectionPage", "name": h1,
            "description": desc, "url": url, "inLanguage": "ja",
            "isPartOf": {"@type": "WebSite", "name": C.NAME, "url": C.SITE},
            "publisher": {"@type": "Organization", "name": C.NAME}}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "トップ", "item": C.SITE},
        {"@type": "ListItem", "position": 2, "name": "製品", "item": C.SITE + "products/"},
        {"@type": "ListItem", "position": 3, "name": "型番から探す"}]}

    html = C.shell(h1, desc, url, "../",
                   '<a href="../">トップ</a><span>/</span><a href="./">製品</a><span>/</span>型番から探す',
                   body, C.load_style(),
                   [json.dumps(coll, ensure_ascii=False, indent=2),
                    json.dumps(crumb, ensure_ascii=False, indent=2)])

    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
    if old != html:
        open(OUT, "w", encoding="utf-8").write(html)
        print("[型番] products/codes.html を更新しました（%d型番 / %dシリーズ）" % (total, len(groups)))
    else:
        print("[型番] 変更はありません（%d型番）" % total)


if __name__ == "__main__":
    build()
