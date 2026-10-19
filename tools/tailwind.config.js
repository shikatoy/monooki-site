/* Tailwind の設定。
   2026-10-16 まで index.html の中に書いていた（cdn.tailwindcss.com がブラウザで読む形）。
   公式が「Play CDN は開発用で、本番向きではない」としているため、
   publish.sh で assets/tw.css に書き出す形に変えた。設定はここが唯一の出典。
   色や字間を変えるときはこのファイルを直し、tools/build-tailwind.py を通すこと。 */
module.exports = {
  /* Tailwind のクラスを使っているのはこの4ページだけ。
     products/ articles/ size/ は tools/_common_page.py の手書きCSSで作っている */
  content: ['index.html', 'about.html', 'privacy.html', 'contact.html'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Noto Sans JP"', 'sans-serif'],
        serif: ['"Shippori Mincho B1"', 'serif'],
        mono: ['"IBM Plex Mono"', 'monospace']
      },
      colors: {
        ink: '#161616',
        paper: '#ffffff',
        line: '#161616',
        linesoft: '#e0e0e0',
        rust: '#a3512b'
      },
      letterSpacing: { widest2: '.2em' }
    }
  }
}
