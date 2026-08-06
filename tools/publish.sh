#!/bin/bash
# ============================================================
#  サイトへ反映（add → commit → push）
#  使い方: bash ~/Documents/monooki-site/tools/publish.sh
#          bash ~/Documents/monooki-site/tools/publish.sh "コミットメッセージ"
# ============================================================
set -u
REPO="$HOME/Documents/monooki-site"
TARGETS=(articles index.html sitemap.xml llms.txt robots.txt contact.html tools .gitignore)

cd "$REPO" 2>/dev/null || { echo "[中止] リポジトリが見つかりません: $REPO"; exit 1; }
MSG="${1:-site: 記事とデータを更新 $(date '+%Y-%m-%d')}"

CHANGED=$(git status --porcelain -- "${TARGETS[@]}")
if [ -z "$CHANGED" ]; then
  echo "変更はありません。何もせず終了します。"
  exit 0
fi

echo "--- 反映する変更 ---"
echo "$CHANGED"
echo "--------------------"

git add -A -- "${TARGETS[@]}" || { echo "[中止] git add に失敗"; exit 1; }
git commit -m "$MSG" || { echo "[中止] commit に失敗"; exit 1; }
git push origin main || { echo "[中止] push に失敗しました（認証を確認してください）"; exit 1; }

echo ""
echo "[完了] push しました。1〜3分でサイトに反映されます。"
echo "       https://shikatoy.github.io/monooki-site/"
