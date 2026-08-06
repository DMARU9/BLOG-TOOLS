# Tasks: プロジェクト構造の再構築 + 追加開発

**Date**: 2026-08-06  
**Reason**: ユーザー要望 - open_deep_research と同じ構造にすること + 未実装機能の確認

---

## 現状の問題

### 1. プロジェクト構造の問題
現在の構造:
```
BLOG-TOOLS/
├── src/
│   └── blog_writer/  ← ルート直下
├── tests/             ← ルート直下
├── open_deep_research/
│   ├── src/
│   └── tests/
└── pyproject.toml
```

期望される構造 (open_deep_research と同じ):
```
BLOG-TOOLS/
├── blog_writer/
│   ├── src/
│   │   └── blog_writer/
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   └── pyproject.toml
├── open_deep_research/
│   ├── src/
│   └── tests/
└── ...
```

### 2. 未実装機能の問題
spec.md で定義されているが、実装されていない機能:
- `__main__.py` の欠如 (python -m blog_writer が動作しない)
- searchstack-aeo の統合 (FR-013a)
- website-seo-audit の統合 (FR-014) - スコープ外だが要確認

---

## T023: プロジェクト構造の再構築

### タスク一覧

- [ ] T023-1: `blog_writer/` ディレクトリの作成
- [ ] T023-2: `src/blog_writer/` → `blog_writer/src/blog_writer/` に移動
- [ ] T023-3: `tests/` → `blog_writer/tests/` に移動
- [ ] T023-4: `pyproject.toml` → `blog_writer/pyproject.toml` に移動
- [ ] T023-5: `__main__.py` の追加
- [ ] T023-6: `.markdownlint.json` の移動
- [ ] T023-7: テストの実行確認
- [ ] T023-8: ruff/mypy の設定更新
- [ ] T023-9: .github/agents/ のエージェント定義更新
- [ ] T023-10: specs/001-blog-writing-agent/ のドキュメント更新

---

## T024: 追加開発の確認

### 未実装機能

- [ ] T024-1: `__main__.py` の作成 → `python -m blog_writer` で実行可能にする
- [ ] T024-2: searchstack-aeo 統合の検討 (FR-013a)
  - searchstack パッケージが利用可能か確認
  - 無料コマンド (meta, schema, links, onpage) の動作確認
  - seo_checker.py への統合
- [ ] T024-3: website-seo-audit 統合の検討 (FR-014)
  - スコープ外だが、将来の実装に備えて調査
- [ ] T024-4: エージェントの動作確認
  - `/blog-writer` コマンドの動作テスト
  - サブエージェント呼び出しの動作確認

---

## 移動後のファイル構成

### blog_writer/
```
blog_writer/
├── src/
│   └── blog_writer/
│       ├── __init__.py
│       ├── __main__.py      ← 新規追加
│       ├── config.py
│       ├── trend_analyzer.py
│       ├── project_analyzer.py
│       ├── seo_checker.py
│       └── markdown_validator.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_trend_analyzer.py
│   │   ├── test_project_analyzer.py
│   │   ├── test_seo_checker.py
│   │   └── test_markdown_validator.py
│   └── integration/
│       └── test_full_flow.py
├── pyproject.toml
├── .markdownlint.json
└── README.md
```

---

## 注意事項

1. **インポートパス**: `from blog_writer.xxx` → 変更なし
2. **pytest**: `cd blog_writer && uv run pytest tests/ -v`
3. **ruff/mypy**: `cd blog_writer && uv run ruff check src/`
4. **エージェント**: `.github/agents/` 内のコマンドパスを更新
5. **CLI**: `cd blog_writer && python -m blog_writer xxx`
