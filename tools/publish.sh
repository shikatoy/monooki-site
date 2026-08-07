#!/bin/bash
# ============================================================
#  サイトへ反映（add → commit → push）
#  使い方: bash ~/Documents/monooki-site/tools/publish.sh
#          bash ~/Documents/monooki-site/tools/publish.sh "コミットメッセージ"
# ============================================================
set -u
REPO="$HOME/Documents/monooki-site"
# 反映する対象。新しいフォルダやページを作ったら、ここに必ず足すこと。
# ここに無いものは、commit されてもサイトに上がらない（過去に products/ と about.html が漏れた）
TARGETS=(index.html about.html privacy.html contact.html \
         articles products images \
         sitemap.xml llms.txt robots.txt tools .gitignore)

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

# --- 対象漏れの自己点検（.gitignore 済みのものは除く）---
LEFT=$(git ls-files --others --exclude-standard)
if [ -n "$LEFT" ]; then
  echo ""
  echo "[注意] 次のファイルはサイトに上がっていません。"
  echo "       意図的でなければ、tools/publish.sh の TARGETS に足してください。"
  echo "$LEFT" | sed 's/^/       /'
fi
