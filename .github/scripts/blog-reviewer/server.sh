#!/usr/bin/env bash
# LangGraph サーバーの起動/停止スクリプト
#
# Usage:
#   ./server.sh start   - サーバーを起動
#   ./server.sh stop    - サーバーを停止
#   ./server.sh status  - 稼働状態を確認

set -euo pipefail

API_BASE="http://127.0.0.1:2024"
OPEN_DEEP_RESEARCH_DIR="/home/takumi/github/BLOG-TOOLS/open_deep_research"
PID_FILE="/tmp/langgraph_server.pid"

check_api() {
    curl -s "${API_BASE}/ok" 2>/dev/null | grep -q '"ok":true'
}

start_server() {
    if check_api; then
        echo "✅ API は既に稼働しています"
        return 0
    fi

    echo "🚀 LangGraph サーバーを起動中..."
    cd "$OPEN_DEEP_RESEARCH_DIR"
    source .venv/bin/activate
    nohup langgraph dev --allow-blocking > /tmp/langgraph_server.log 2>&1 &
    echo $! > "$PID_FILE"

    # 起動待機（最大30秒）
    for i in $(seq 1 30); do
        sleep 1
        if check_api; then
            echo "✅ API 稼働開始（${i}秒）"
            return 0
        fi
    done

    echo "❌ API の起動に失敗しました"
    return 1
}

stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🛑 LangGraph サーバーを停止中 (PID: $PID)..."
            kill "$PID"
            sleep 2
            # 強制終了
            if kill -0 "$PID" 2>/dev/null; then
                kill -9 "$PID" 2>/dev/null || true
            fi
            echo "✅ サーバーを停止しました"
        fi
        rm -f "$PID_FILE"
    else
        # PID ファイルがない場合、プロセス名で検索
        PIDS=$(pgrep -f "langgraph dev" 2>/dev/null || true)
        if [ -n "$PIDS" ]; then
            echo "🛑 LangGraph サーバーを停止中..."
            echo "$PIDS" | xargs kill 2>/dev/null || true
            sleep 2
            echo "✅ サーバーを停止しました"
        else
            echo "ℹ️  サーバーは稼働していません"
        fi
    fi
}

status_server() {
    if check_api; then
        echo "✅ API 稼働中: ${API_BASE}"
        return 0
    else
        echo "❌ API 停止中"
        return 1
    fi
}

case "${1:-status}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    status)
        status_server
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
