# Quickstart: ブログ作成エージェント

**Feature**: 001-blog-writing-agent  
**Date**: 2026-08-06

## Prerequisites

- Python 3.11+
- uv (パッケージ管理)
- Node.js (markdownlint 用)
- open_deep_research サーバー (`http://127.0.0.1:2024`)

## Setup

### 1. 依存関係のインストール

```bash
cd /home/takumi/github/BLOG-TOOLS

# Python 依存関係
uv sync

# Node.js ツール
npm install -g markdownlint-cli
```

### 2. 外部ツールのインストール

```bash
# website-seo-audit
pip install website-seo-audit

# pytrends
pip install pytrends

# searchstack-aeo
pip install searchstack
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

## Validation Scenarios

### Scenario 1: 基本的な記事生成

**目的**: トピックから記事が生成されることを確認

```bash
# 実行
python -m blog_writer.cli --topic "Obsidian でナレッジ管理"

# 期待される結果
# - /home/takumi/github/DMARU9.github.io/src/content/blog/obsidian-knowledge-management.md が生成される
# - frontmatter が正しく設定されている
# - Mermaid ダイアグラムが 1 つ以上含まれる
# - SEO スコアが 80 点以上
```

**検証コマンド**:

```bash
# frontmatter 検証
head -20 /home/takumi/github/DMARU9.github.io/src/content/blog/obsidian-knowledge-management.md

# Mermaid ダイアグラム検証
grep -c "mermaid" /home/takumi/github/DMARU9.github.io/src/content/blog/obsidian-knowledge-management.md

# markdownlint 検証
npx markdownlint-cli /home/takumi/github/DMARU9.github.io/src/content/blog/obsidian-knowledge-management.md
```

---

### Scenario 2: 補足情報付き記事生成

**目的**: プロジェクト名やディレクトリパスを指定した場合の動作確認

```bash
# 実行
python -m blog_writer.cli \
  --topic "open_deep_research" \
  --project-name "open_deep_research" \
  --detailed-spec "LangGraph のアーキテクチャについて"

# 期待される結果
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
