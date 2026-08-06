# Quickstart: ブログ作成エージェント

**Feature**: 001-blog-writing-agent  
**Date**: 2026-08-06  
**Status**: 実装完了

## 概要

VS Code Copilot のエージェント機能を活用したブログ作成フロー。
トピックを入力するだけで、リサーチ→執筆→品質チェック→SEO最適化まで自動実行します。

## Prerequisites

- Python 3.11+
- uv (パッケージ管理)
- Node.js (markdownlint 用)
- VS Code + GitHub Copilot 拡張機能
- open_deep_research サーバー (`http://127.0.0.1:2024`)

## Setup

### 1. 依存関係のインストール

```bash
cd /home/takumi/github/BLOG-TOOLS

# Python 依存関係
uv sync

# 開発用依存関係 (テスト、lint用)
uv sync --extra dev
```

### 2. 外部ツールの確認

```bash
# markdownlint-cli の確認
npx markdownlint --version

# Python パッケージの確認
uv pip list | grep -E "pytrends|httpx|beautifulsoup4"
```

### 3. open_deep_research サーバーの管理

```bash
cd /home/takumi/github/BLOG-TOOLS

# サーバー起動
bash .github/scripts/blog-reviewer/server.sh start

# サーバー状態確認
bash .github/scripts/blog-reviewer/server.sh status

# サーバー停止
bash .github/scripts/blog-reviewer/server.sh stop
```

> ⚠️ サーバーは必ず起動→利用→停止の順で実行すること。常時稼働させない。

---

## 使用方法

### 方法 1: VS Code Copilot エージェント (推奨)

VS Code の Copilot チャットで以下のコマンドを実行します：

```
/blog-writer "Obsidian でナレッジ管理"
```

**オプション付き**:

```
/blog-writer "open_deep_research" --project-name "open_deep_research" --directory "/path/to/project"
```

### 方法 2: Python CLI (ツールの個別実行)

各ツールはスタンドアロンで実行可能です：

```bash
# トレンド分析
python -m blog_writer.trend_analyzer "Python プログラミング"

# プロジェクト解析
python -m blog_writer.project_analyzer /path/to/project

# SEO チェック
python -m blog_writer.seo_checker /path/to/blog-post.md

# Markdown 検証
python -m blog_writer.markdown_validator /path/to/blog-post.md
```

---

## Validation Scenarios

### Scenario 1: 基本的な記事生成

**目的**: トピックから記事が生成されることを確認

```bash
# 実行 (VS Code Copilot)
/blog-writer "Obsidian でナレッジ管理"

# 期待される結果
# - output/obsidian-knowledge-management.md が生成される
# - frontmatter が正しく設定されている
# - Mermaid ダイアグラムが 1 つ以上含まれる
# - SEO スコアが 80 点以上
```

**検証コマンド**:

```bash
# frontmatter 検証
head -10 output/obsidian-knowledge-management.md

# Mermaid ダイアグラム検証
grep -c "mermaid" output/obsidian-knowledge-management.md

# SEO スコア確認
python -m blog_writer.seo_checker output/obsidian-knowledge-management.md
```

---

### Scenario 2: 補足情報付き記事生成

**目的**: プロジェクト名やディレクトリパスを指定した場合の動作確認

```bash
# 実行 (VS Code Copilot)
/blog-writer "open_deep_research" --project-name "open_deep_research" --detailed-spec "LangGraph のアーキテクチャについて"
```

**期待される結果**:
- プロジェクトの README が参照される
- 技術スタックが記事に反映される
- ディレクトリ構造が説明に含まれる

---

### Scenario 3: 個別ツールの実行

**目的**: 各ツールが独立して動作することを確認

```bash
# トレンド分析
python -m blog_writer.trend_analyzer "AI エージェント"
# → JSON 形式でトレンド結果が出力される

# プロジェクト解析
python -m blog_writer.project_analyzer /home/takumi/github/BLOG-TOOLS
# → JSON 形式でプロジェクト情報が出力される

# SEO チェック
python -m blog_writer.seo_checker src/content/blog/test.md
# → JSON 形式で SEO スコアが出力される
```

---

## 開発者向け

### テストの実行

```bash
# 全テスト実行
uv run pytest tests/ -v

# ユニットテストのみ
uv run pytest tests/unit/ -v

# 統合テストのみ
uv run pytest tests/integration/ -v
```

### コード品質チェック

```bash
# リントチェック
uv run ruff check src/blog_writer/

# 型チェック
uv run mypy src/blog_writer/
```

### プロジェクト構造

```
BLOG-TOOLS/
├── src/blog_writer/              # Python ツールアプリ群
│   ├── __init__.py
│   ├── config.py                 # 設定管理
│   ├── trend_analyzer.py         # トレンド分析
│   ├── project_analyzer.py       # プロジェクト解析
│   ├── seo_checker.py            # SEO チェック
│   └── markdown_validator.py     # Markdown 検証
├── .github/
│   ├── agents/                   # Copilot エージェント定義
│   │   ├── blog-writer.agent.md
│   │   ├── blog-researcher.agent.md
│   │   └── blog-quality-checker.agent.md
│   ├── prompts/                  # エージェントプロンプト
│   │   ├── blog-writer.prompt.md
│   │   ├── blog-researcher.prompt.md
│   │   └── blog-quality-checker.prompt.md
│   └── styles/
│       └── blog-style-guide.md
├── tests/
│   ├── unit/                     # ユニットテスト
│   └── integration/              # 統合テスト
└── specs/001-blog-writing-agent/ # 仕様書
```

---

## トラブルシューティング

### Q: サーバーが起動しない
```bash
# ログを確認
bash .github/scripts/blog-reviewer/server.sh status

# 手動で起動確認
cd /home/takumi/github/BLOG-TOOLS/open_deep_research
uv run langgraph dev
```

### Q: SEO スコアが低い
- タイトルが30文字以上60文字以内か確認
- 説明が120文字以上160文字以内か確認
- H1 が1つだけか確認
- 画像に alt テキストが設定されているか確認

### Q: Markdownlint エラー
```bash
# 設定ファイルを確認
cat .markdownlint.json

# 特定ルールを無効化
npx markdownlint --disable MD025 file.md
```
# - プロジェクトの README とソースコードが参照される
# - LangGraph 関連の情報が記事に反映される
```

---

### Scenario 3: トレンド分析の確認

**目的**: pytrends によるトレンド分析が正しく動作することを確認

```bash
# 実行
python -m blog_writer.cli --topic "AI エージェント" --verbose

# 期待される結果
# - トレンド分析結果が表示される
# - 関連クエリが表示される
# - 関連高トレンドトピックが提案される
```

---

### Scenario 4: 品質チェックレポートの取得

**目的**: 品質チェック結果がレポートされることを確認

```bash
# 実行
python -m blog_writer.cli --topic "TypeScript 入門" --report

# 期待される結果
# - 事実確認結果が表示される
# - フォーマット検証結果が表示される
# - SEO チェック結果が表示される
# - 修正内容が表示される
```

---

### Scenario 5: エラーハンドリングの確認

**目的**: エラー時に適切に処理されることを確認

```bash
# 空のトピックで実行
python -m blog_writer.cli --topic ""

# 期待される結果
# - ValueError が発生し、適切なエラーメッセージが表示される

# 存在しないディレクトリを指定
python -m blog_writer.cli --topic "テスト" --directory-path /nonexistent

# 期待される結果
# - エラーメッセージが表示される
```

## Performance Validation

### SC-001: 10 分以内に完了

```bash
# 実行時間の計測
time python -m blog_writer.cli --topic "Obsidian でナレッジ管理"

# 期待される結果
# - real    0mXXs (10 分以内)
```

### SC-005: SEO スコア 80 点以上

```bash
# SEO スコアの確認
python -m blog_writer.cli --topic "テスト" --check-seo

# 期待される結果
# - SEO Score: 80+ / 100
```

## Troubleshooting

### open_deep_research サーバーに接続できない

```bash
# サーバーの状態確認
bash .github/scripts/blog-reviewer/server.sh status

# サーバーの再起動
bash .github/scripts/blog-reviewer/server.sh stop
bash .github/scripts/blog-reviewer/server.sh start
```

### pytrends で 429 エラーが発生する

- 少なくとも 5 秒待ってからリトライ
- リクエスト頻度を下げる

### markdownlint が見つからない

```bash
# インストール
npm install -g markdownlint-cli

# 確認
npx markdownlint-cli --version
```
