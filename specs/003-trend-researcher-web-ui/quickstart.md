# Quickstart: Trend Researcher Web UI

**Date**: 2026-08-31
**Feature**: 003-trend-researcher-web-ui

## 前提条件

- Python 3.11+
- `uv` インストール済み
- `.env` ファイルに API キー設定済み

## セットアップ

```bash
cd /home/takumi/github/BLOG-TOOLS

# 依存関係インストール（langgraph-cli[inmem] を含む）
uv pip install -e trend_researcher[dev]
```

## 検証シナリオ

### Scenario 1: LangGraph Studio でブラウザからリサーチ実行

**目的**: P1 User Story 1 の検証

```bash
cd trend_researcher
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking
```

**期待結果**:
- API エンドポイント: `http://127.0.0.1:2024`
- Studio UI: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

**ブラウザでの操作**:
1. Studio UI を開く
2. `messages` フィールドにリサーチ指示を入力（例: "AI エージェントの最新トレンドを調査して"）
3. Submit をクリック
4. 進捗がストリーミングで表示されることを確認
5. 完了後に Markdown レポートが表示されることを確認

### Scenario 2: CLI でリサーチ実行

**目的**: P1 User Story 2 の検証

```bash
cd trend_researcher
python -m trend_researcher "AI エージェントの最新トレンドを調査して" --platform youtube --format markdown
```

**期待結果**:
- 進捗メッセージが stderr に出力される
- 最終レポートが stdout に出力される（または `--output` で指定したファイルに書き込まれる）

### Scenario 3: 設定の変更

**目的**: P2 User Story 3 の検証

```bash
# JSON 形式で出力
python -m trend_researcher "テスト指示" --format json

# 件数を指定
python -m trend_researcher "テスト指示" --max-results 10

# YouTube を指定
python -m trend_researcher "テスト指示" --platform youtube
```

**期待結果**:
- 指定した設定が反映されたレポートが出力される

### Scenario 4: エラーハンドリング

**目的**: エッジケースの検証

```bash
# 不正なプラットフォーム指定
python -m trend_researcher "テスト指示" --platform invalid
```

**期待結果**:
- エラーメッセージが表示される（終了コード 2）

## トラブルシューティング

### ポート競合

```bash
# ポート 2024 が使用中の場合
lsof -i :2024
# 使用中のプロセスを終了してから再実行
```

### 依存関係エラー

```bash
# クリーンインストール
uv pip uninstall trend-researcher
uv pip install -e trend_researcher[dev]
```

### .env ファイルの読み込み

```bash
# .env ファイルが正しく設定されているか確認
cat trend_researcher/.env
```
