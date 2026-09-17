#!/bin/bash
# ============================================================
#  1シリーズだけ、寸法を取り切る
#  使い方: bash ~/Documents/monooki-site/tools/fill-sizes.sh y-ese
#  ログ  : monooki-site/tools/run.log
#  commit も push もしません。
# ============================================================
set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

REPO="$HOME/Documents/monooki-site"
PROMPT="$REPO/tools/fill-sizes-prompt.md"
LOG="$REPO/tools/run.log"
ID="${1:-}"

cd "$REPO" 2>/dev/null || { echo "[中止] リポジトリが見つかりません: $REPO"; exit 1; }
command -v claude >/dev/null || { echo "[中止] claude コマンドが見つかりません"; exit 1; }
[ -n "$ID" ] || { echo "使い方: bash tools/fill-sizes.sh <id>   例) y-ese"; exit 1; }
grep -q "id:'$ID'" index.html || { echo "[中止] PRODUCTS に $ID がありません"; exit 1; }

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "[中止] コミットしていない変更が残っています。先に publish.sh を流してください。"
  git status --short
  exit 1
fi

{ echo ""; echo "===== $(date '+%Y-%m-%d %H:%M:%S') 寸法収集 $ID 開始 ====="; } | tee -a "$LOG"

claude -p "$(cat "$PROMPT")
**対象の id は \`$ID\` です。この1機種だけを扱ってください。**" \
  --permission-mode acceptEdits 2>&1 | tee -a "$LOG"

{ echo "===== $(date '+%Y-%m-%d %H:%M:%S') 寸法収集 $ID 終了 ====="; } | tee -a "$LOG"

echo ""
echo "--- 変更ファイル ---"
git status --short
echo ""
echo "問題なければ: cd ~/Documents/monooki-site && bash tools/publish.sh"
