#!/bin/bash
# ============================================================
#  物置どれがいい？ — 製品データ定期確認
#  launchd から毎朝8:00に呼ばれる。手動実行も可（引数不要）。
#  変更が見つからなければ何も出さずに終わる。
#  ログ: monooki-site/tools/run.log
# ============================================================
set -u

# claude コマンドの場所を明示的に通す（launchd から起動されると PATH が最小限のため）
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

REPO="$HOME/Documents/monooki-site"
PROMPT="$REPO/tools/product-check-prompt.md"
LOG="$REPO/tools/run.log"

cd "$REPO" 2>/dev/null || { echo "[中止] リポジトリが見つかりません: $REPO"; exit 1; }
exec >>"$LOG" 2>&1
echo ""
echo "===== $(date '+%Y-%m-%d %H:%M:%S') 開始 ====="

command -v claude >/dev/null || { echo "[中止] claude コマンドが見つかりません（PATHを確認）"; exit 1; }
[ -f "$PROMPT" ] || { echo "[中止] プロンプトが見つかりません: $PROMPT"; exit 1; }

# 追跡中のファイルだけを見る（未追跡ファイルは無視）
dirty() { git status --porcelain --untracked-files=no; }

# --- 1. 作業前の状態を確認 ---
if [ -n "$(dirty)" ]; then
  echo "[中止] コミットしていない変更が残っています。片付けてから再実行してください。"
  dirty
  exit 1
fi

# --- 2. 最新化 ---
git pull --ff-only origin main || { echo "[中止] git pull に失敗しました"; exit 1; }

# --- 3. Claude に確認させる ---
echo "--- claude 実行 ---"
claude -p "$(cat "$PROMPT")" --permission-mode acceptEdits
echo "--- claude 終了 (rc=$?) ---"

# --- 4. 変更が無ければ正常終了（これが最も多い） ---
if [ -z "$(dirty)" ]; then
  echo "[正常] 変更なし。終了します。"
  exit 0
fi

# --- 5. index.html 以外が変わっていたら中止 ---
OTHER=$(dirty | awk '{print $NF}' | grep -v '^index\.html$' || true)
if [ -n "$OTHER" ]; then
  echo "[中止] 想定外のファイルが変更されました。push しません。手動で確認してください。"
  echo "$OTHER"
  exit 1
fi

# --- 6. index.html の変更が PRODUCTS / UPDATE_LOG の範囲内か確認 ---
if git diff -U0 -- index.html | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' \
   | grep -qE 'ARTICLES|PRODUCT_PAGES|renderArticles|<nav|<section|<header|<footer|<script|tailwind\.config'; then
  echo "[中止] PRODUCTS / UPDATE_LOG 以外が変更された疑いがあります。push しません。"
  git diff --stat -- index.html
  exit 1
fi

# --- 7. コミットして push ---
echo "--- 変更内容 ---"
git diff --stat -- index.html
git add index.html
git commit -m "auto: 製品データ定期確認 $(date '+%Y-%m-%d')" || { echo "[中止] commit に失敗"; exit 1; }
git push origin main || { echo "[中止] push に失敗しました（認証を確認）"; exit 1; }
echo "[完了] push しました。1〜3分でサイトに反映されます。"
