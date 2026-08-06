# blog_writer

ブログ記事作成支援ツール

## 概要

ブログ記事の作成、品質チェック、SEO 検証を行う Python パッケージです。

## インストール

```bash
cd blog_writer
uv sync
```

## 使い方

### CLI

```bash
# トレンド分析
uv run python -m blog_writer trend "トピック名"

# SEO チェック
uv run python -m blog_writer seo article.md

# Markdown バリデーション
uv run python -m blog_writer validate article.md

# プロジェクト分析
uv run python -m blog_writer analyze /path/to/project
```

### テスト

```bash
uv run pytest tests/ -v
```

## 開発

```bash
# リント
uv run ruff check src/

# 型チェック
uv run mypy src/
```
