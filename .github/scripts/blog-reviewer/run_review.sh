#!/usr/bin/env bash
# Blog Reviewer - API Client Script
# Open Deep Research API を利用してブログ記事をレビューする
#
# Usage:
#   ./run_review.sh <blog_file_path>
#
# Prerequisites:
#   - Open Deep Research API が http://127.0.0.1:2024 で起動していること
#   - curl がインストールされていること
#   - jq がインストールされていること

set -euo pipefail

API_BASE="http://127.0.0.1:2024"
PROMPT_FILE="$(dirname "$0")/../../prompts/blog-reviewer.prompt.md"

# 引数チェック
if [ $# -lt 1 ]; then
    echo "Usage: $0 <blog_file_path>"
    echo "Example: $0 /path/to/blog-article.md"
    exit 1
fi

BLOG_FILE="$1"

if [ ! -f "$BLOG_FILE" ]; then
    echo "Error: File not found: $BLOG_FILE"
    exit 1
fi

echo "📝 ブログファイル: $BLOG_FILE"

# API ヘルスチェック
echo "🔍 API ヘルスチェック..."
HEALTH=$(curl -s "${API_BASE}/ok" 2>/dev/null || echo "FAILED")
if [ "$HEALTH" != '{"ok":true}' ]; then
    echo "❌ API が起動していません: ${API_BASE}"
    echo "   以下のコマンドで起動してください:"
    echo "   cd /home/takumi/github/BLOG-TOOLS/open_deep_research && source .venv/bin/activate && langgraph dev --allow-blocking"
    exit 1
fi
echo "✅ API 稼働中"

# スレッド作成
echo "🧵 スレッド作成中..."
THREAD_RESPONSE=$(curl -s "${API_BASE}/threads" -X POST -H 'Content-Type: application/json' -d '{}')
THREAD_ID=$(echo "$THREAD_RESPONSE" | jq -r '.thread_id')

if [ -z "$THREAD_ID" ] || [ "$THREAD_ID" = "null" ]; then
    echo "❌ スレッド作成に失敗しました"
    echo "   Response: $THREAD_RESPONSE"
    exit 1
fi
echo "✅ スレッド作成: $THREAD_ID"

# ブログコンテンツ読み込み
CONTENT=$(cat "$BLOG_FILE")

# ペイロード作成
PAYLOAD=$(cat <<EOF
{
  "assistant_id": "Deep Researcher",
  "input": {
    "messages": [
      {
        "role": "user",
        "content": "以下のブログ記事の内容をレビューしてください。記載されている事実に誤りがないか、ウェブ上の信頼できるソースを参照して確認してください。\n\n## レビュー時に確認してほしいポイント\n\n1. 各セクションの記述は正確か（ツールやサービスの仕様と一致しているか）\n2. 記載されている公式情報の帰属は正しいか（第三者によるものではないか）\n3. コマンド一覧や機能一覧は正確か\n4. ファイル構成やディレクトリ構造の記述は正しいか\n5. 機能説明は正確か（実装されている機能と一致しているか）\n6. インストール方法やコマンドは正しいか\n7. 最新の情報に基づいているか\n\n各項目について、誤りがある場合は「誤り」、要確認の場合は「要確認」、正確の場合は「正確」と分類してください。\n\n最終的に、修正が必要な箇所を具体的にリストアップしてください。\n\n---\n\n## ブログ記事の内容\n\n$(echo "$CONTENT" | jq -Rs . | sed 's/^"//;s/"$//')"
      }
    ]
  },
  "config": {
    "configurable": {
      "search_api": "openai",
      "allow_clarification": false,
      "max_researcher_iterations": 6,
      "max_react_tool_calls": 10
    }
  },
  "stream_mode": "values"
}
EOF
)

# レビュー実行
echo "🔍 レビュー実行中（1〜3分かかります）..."
REVIEW_RESPONSE=$(curl -s "${API_BASE}/threads/${THREAD_ID}/runs/wait" \
    -X POST \
    -H 'Content-Type: application/json' \
    -d "$PAYLOAD" \
    --max-time 300)

# レスポンスから最終的な AI メッセージを抽出
REVIEW_REPORT=$(echo "$REVIEW_RESPONSE" | jq -r '
    [.[] | select(.type == "ai" and (.content | length > 200))]
    | last
    | .content
' 2>/dev/null)

if [ -z "$REVIEW_REPORT" ] || [ "$REVIEW_REPORT" = "null" ]; then
    echo "❌ レビュー結果の取得に失敗しました"
    echo "   Response: $(echo "$REVIEW_RESPONSE" | head -c 500)"
    exit 1
fi

# 結果を一時ファイルに保存
OUTPUT_FILE="/tmp/blog_review_$(date +%Y%m%d_%H%M%S).md"
cat > "$OUTPUT_FILE" <<EOF
# ブログレビュー結果

- **対象ファイル**: ${BLOG_FILE}
- **レビュー実行日**: $(date '+%Y-%m-%d %H:%M:%S')
- **API**: Open Deep Research (search_api: openai)

---

## レビューレポート

${REVIEW_REPORT}
EOF

echo ""
echo "✅ レビュー完了"
echo "📄 レポート: ${OUTPUT_FILE}"
echo ""
echo "---"
echo "$REVIEW_REPORT"
