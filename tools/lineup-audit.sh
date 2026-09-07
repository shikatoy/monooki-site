#!/bin/bash
# ============================================================
#  一度きり：3社の現行ラインアップを公式で洗い直す
#  使い方: bash ~/Documents/monooki-site/tools/lineup-audit.sh inaba
#          （inaba / yodoko / takubo のどれか1社ずつ）
#  ログ  : monooki-site/tools/run.log
#  commit も push もしません。中身を見てから publish.sh を流してください。
# ============================================================
set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

REPO="$HOME/Documents/monooki-site"
PROMPT="$REPO/tools/lineup-audit-prompt.md"
LOG="$REPO/tools/run.log"
M="${1:-}"

case "$M" in
  inaba)  LABEL="イナバ（稲葉製作所） maker:'inaba'" ;;
  yodoko) LABEL="ヨドコウ（淀川製鋼所） maker:'yodoko'" ;;
  takubo) LABEL="タクボ（田窪工業所） maker:'takubo'" ;;
  *) echo "使い方: bash tools/lineup-audit.sh inaba|yodoko|takubo"; exit 1 ;;
esac

cd "$REPO" 2>/dev/null || { echo "[中止] リポジトリが見つかりません: $REPO"; exit 1; }
command -v claude >/dev/null || { echo "[中止] claude コマンドが見つかりません"; exit 1; }
[ -f "$PROMPT" ] || { echo "[中止] 指示書がありません: $PROMPT"; exit 1; }

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "[中止] コミットしていない変更が残っています。先に publish.sh を流してください。"
  git status --short
  exit 1
fi

{ echo ""; echo "===== $(date '+%Y-%m-%d %H:%M:%S') ラインアップ洗い直し $M 開始 ====="; } | tee -a "$LOG"

claude -p "$(cat "$PROMPT")
$LABEL

**このメーカーだけを対象にしてください。他社の行は1文字も触らないこと。**" \
  --permission-mode acceptEdits 2>&1 | tee -a "$LOG"

{ echo "===== $(date '+%Y-%m-%d %H:%M:%S') ラインアップ洗い直し $M 終了 ====="; } | tee -a "$LOG"

echo ""
echo "--- 変更ファイル ---"
git status --short
echo ""
echo "中身を確認したら、次で反映します:"
echo "  cd ~/Documents/monooki-site && bash tools/publish.sh"
