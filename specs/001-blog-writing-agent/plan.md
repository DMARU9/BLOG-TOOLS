# Implementation Plan: ブログ作成エージェント

**Branch**: `001-blog-writing-agent` | **Date**: 2026-08-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-blog-writing-agent/spec.md`

## Summary

トピック（必須）と補足情報（プロジェクト名、ディレクトリパス、詳細な内容指定）を入力とし、リサーチ→執筆→品質チェック→SEO→修正のフローを自動実行するブログ作成エージェントを構築する。フロー管理は VS Code の GitHub Copilot エージェント機能（`.github/agents/`）に委ね、分析・検証用のツールアプリケーションのみ `src/blog_writer/` に構築する。

**アーキテクチャの考え方**:
- **フロー管理**: Copilot エージェント（`.agent.md`）が手順を順に実行し、サブエージェント呼び出しでフェーズを分離
- **ユーザー入口は 1 つ**: `blog-writer` のみユーザーが直接実行。他のエージェントはすべてサブエージェントとして内部呼び出し
- **ツールアプリ**: Python で作成したスタンドアロンスクリプトをエージェントが `run_in_terminal` で呼び出す
- **LangGraph は不使用**: Copilot の自然な会話フローで十分であり、過度なフレームワーク導入を避ける

## Technical Context

**Language/Version**: Python 3.11+（ツールアプリ）, Markdown（エージェント定義）

**Primary Dependencies**: pytrends, searchstack-aeo, markdownlint, website-seo-audit, open_deep_research (API)

**Storage**: ファイルベース（Markdown ファイル、JSON レポート）

**Testing**: pytest, ruff, mypy

**Target Platform**: ローカル環境（DMARU9.github.io ブログプロジェクト向け）

**Project Type**: Copilot エージェント + Python ツールアプリ

**Performance Goals**: トピック入力から完成記事まで 10 分以内

**Constraints**: BLOG-TOOLS Constitution 準拠（Python 3.11+, uv, ruff, mypy, pytest）

**Scale/Scope**: 個人ブログ運用向け、月数本の記事生成

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Purpose-Bound Tools | ✅ PASS | DMARU9.github.io のブログ運用に特化 |
| II. Centralized Tool Management | ✅ PASS | BLOG-TOOLS プロジェクト配下に構築 |
| III. Modular Architecture | ✅ PASS | 各エージェントは独立したモジュールとして設計 |
| IV. Quality Standards | ✅ PASS | テスト、ドキュメント、型安全性を担保 |
| V. Simplicity & Pragmatism | ✅ PASS | 必要十分な機能のみ実装 |

## Project Structure

### Documentation (this feature)

```text
specs/001-blog-writing-agent/
├── plan.md              # このファイル
├── spec.md              # 仕様書
├── research.md          # Phase 0 出力
├── data-model.md        # Phase 1 出力
├── quickstart.md        # Phase 1 出力
├── contracts/           # Phase 1 出力
└── checklists/
    └── requirements.md  # 品質チェックリスト
```

### Source Code (repository root)

```text
.github/
├── agents/
│   ├── blog-writer.agent.md              # メインエージェント（ユーザー実行のみ）
│   ├── blog-researcher.agent.md          # サブエージェント（blog-writer 内から呼び出し）
│   ├── blog-quality-checker.agent.md     # サブエージェント（blog-writer 内から呼び出し）
│   └── blog-reviewer.agent.md            # 既存: 事実確認エージェント（ユーザー実行 / サブエージェント）
├── prompts/
│   ├── blog-writer.prompt.md             # ブログ作成プロンプト（スタイルガイド等を含む）
│   ├── blog-researcher.prompt.md         # リサーチプロンプト
│   └── blog-quality-checker.prompt.md    # 品質チェックプロンプト
├── scripts/
│   └── blog-reviewer/
│       ├── server.sh                     # open_deep_research サーバー管理（blog-writer からも流用）
│       └── run_review.sh                 # 既存: ブログレビュースクリプト
└── styles/
    └── blog-style-guide.md               # ブログスタイルガイド

blog_writer/
├── src/
│   └── blog_writer/                          # ツールアプリ群
│       ├── __init__.py
│       ├── __main__.py                       # CLI エントリーポイント
│       ├── trend_analyzer.py                 # pytrends ベースのトレンド分析
│       ├── project_analyzer.py               # プロジェクト/ディレクトリ解析
│       ├── seo_checker.py                    # SEO チェック（searchstack-aeo + カスタム）
│       ├── markdown_validator.py             # Markdown フォーマット検証
│       └── config.py                         # 設定管理
├── tests/
│   ├── unit/
│   │   ├── test_trend_analyzer.py
│   │   ├── test_project_analyzer.py
│   │   ├── test_seo_checker.py
│   │   └── test_markdown_validator.py
│   ├── integration/
│   │   └── test_full_flow.py
│   └── conftest.py
├── pyproject.toml
├── .markdownlint.json
└── README.md
```

**Structure Decision**:
- **フロー管理は Copilot エージェントに委ねる**: `.github/agents/blog-writer.agent.md` がリサーチ→執筆→品質チェック→SEO→修正の手順を指示し、各フェーズでサブエージェントやツールアプリを呼び出す
- **ツールアプリはスタンドアロン**: `blog_writer/src/blog_writer/` には分析・検証用の Python スクリプトのみ配置。各スクリプトは独立して実行可能（`python -m blog_writer.trend_analyzer` 等）
- **LangGraph は不使用**: Copilot の自然な会話フローでフロー管理が可能であり、過度なフレームワーク導入を避ける
- **拡張性**: ツールアプリの追加・変更は `blog_writer/` ディレクトリ内で完結し、エージェント定義の手順に追加するだけで連携可能

### エージェントの役割分担

| エージェント | ユーザー実行 | 役割 | 呼び出し元 |
|-------------|:-----------:|------|-----------|
| `blog-writer` | ✅ **のみ** | メインオーケストレーター。フロー全体を管理し、各フェーズを順次実行する | ユーザー |
| `blog-researcher` | ❌ | トピックリサーチとトレンド分析を実行する | blog-writer からサブエージェントとして呼び出し |
| `blog-quality-checker` | ❌ | Markdown 検証・SEO チェック・品質レポート生成を実行する | blog-writer からサブエージェントとして呼び出し |
| `blog-reviewer` | ✅（既存） | 事実確認と自動修正を実行する。open_deep_research API 連携済み | ユーザー直接 or blog-writer からサブエージェントとして呼び出し |

**設計思想**: ユーザーが直接実行するのは `blog-writer` のみ。リサーチ・品質チェック等の内部フェーズはサブエージェントとして `blog-writer` 内から `runSubagent` で呼び出すことで、ユーザーは「記事を書いて」という入口だけで一気通貫のフローを実行できる。

**⚠️ open_deep_research サーバー利用時の注意**: 必ず起動→利用→停止の順で実行すること。`blog-reviewer` で使用されている `.github/scripts/blog-reviewer/server.sh` を流用する。

## Complexity Tracking

> Constitution Check に違反はなし。このセクションは不要。

## Phase 0: Research

### リサーチ課題

1. **✅ open_deep_research API の利用方法**: 既存の `blog-reviewer.agent.md` で実装済み。起動→停止の手順は blog-reviewer のスクリプト（`.github/scripts/blog-reviewer/server.sh`）を流用する
2. **pytrends のレートリミット対策**: Google Trends API の制限と回避策
3. **searchstack-aeo の無料コマンド仕様**: Markdown ベースでの実行方法
4. **markdownlint の Python からの呼び出し**: Node.js ツールとの連携方法
5. **既存ブログのスタイルガイド抽出**: 既存記事からルールを自動抽出する方法

### 既存リソースの流用

- **open_deep_research API 連携**: `blog-reviewer.agent.md` の手順を参照。blog-writer からも同じ API エンドポイント（`http://127.0.0.1:2024`）を使用
- **サーバー管理スクリプト**: `.github/scripts/blog-reviewer/server.sh` を blog-writer からも利用可能にする
- **⚠️ 起動→停止の手順**: サーバーは必ず起動→利用→停止の順で実行すること。常時稼働させない

### 予想される知見

- open_deep_research は HTTP API で呼び出し可能（blog-reviewer で実証済み）
- pytrends はレートリミットが厳しく、sleep が必要
- searchstack-aeo は CLI として実行可能
- markdownlint は Node.js プロセスとして呼び出すか、Python ラッパーを使用
- スタイルガイドは既存記事の構造を解析して抽出可能

## Phase 1: Design

### データフロー

```
📝 ユーザー入力
  ├─ topic (必須)
  ├─ project_name (補足)
  ├─ directory_path (補足)
  └─ detailed_spec (補足)
         ↓
┌─────────────────────────────────────────┐
│  🎛️  blog-writer (Copilot Agent)       │
│                                         │
│  1. 📊 Trend Analysis (pytrends)        │
│     ├─ Interest Over Time               │
│     ├─ Related Queries                  │
│     └─ 関連トピック提案                   │
│                                         │
│  2. 🔍 Research (open_deep_research)    │
│     ├─ トピックリサーチ                   │
│     ├─ プロジェクト/ディレクトリ解析       │
│     └─ 出典記録                          │
│                                         │
│  3. ✍️ Writing (LLM)                   │
│     ├─ スタイルガイド準拠                 │
│     ├─ Mermaid ダイアグラム生成           │
│     └─ frontmatter 生成                 │
│                                         │
│  4. 🧪 Quality Check                    │
│     ├─ blog-reviewer (事実確認)          │
│     ├─ markdownlint (フォーマット)       │
│     ├─ searchstack meta/schema/links    │
│     └─ Python SEO カスタムチェック       │
│                                         │
│  5. 🔧 Auto Fix                         │
│     └─ 指摘事項を自動修正                 │
│                                         │
│  6. 📤 Output                           │
│     ├─ Markdown ファイル生成             │
│     └─ 実行レポート出力                  │
└─────────────────────────────────────────┘
         ↓
📤 DMARU9.github.io/src/content/blog/
```

### ステート定義

```python
class BlogWriterState(TypedDict):
    # 入力
    topic: str                          # トピック（必須）
    project_name: Optional[str]         # プロジェクト名（補足）
    directory_path: Optional[str]       # ディレクトリパス（補足）
    detailed_spec: Optional[str]        # 詳細な内容指定（補足）

    # リサーチ結果
    trend_result: TrendResult           # トレンド分析結果
    research_result: ResearchResult     # リサーチ結果
    project_info: Optional[ProjectInfo] # プロジェクト/ディレクトリ情報

    # 執筆結果
    blog_post: BlogPost                 # 生成された記事
    mermaid_diagrams: List[str]         # Mermaid ダイアグラム

    # 品質チェック結果
    quality_report: QualityReport       # 品質チェック結果
    seo_report: SEOReport               # SEO チェック結果
    fix_report: FixReport               # 修正結果

    # 出力
    output_path: str                    # 出力ファイルパス
    execution_log: List[ExecutionLog]   # 実行ログ
```

## Phase 2: Tasks

> `/speckit.tasks` コマンドで生成される。このセクションは `/speckit.plan` では作成しない。

## Success Criteria

| ID | Criteria | Measurement |
|----|----------|-------------|
| SC-001 | トピック入力から完成記事まで 10 分以内 | 実行時間計測 |
| SC-002 | frontmatter スキーマ検証 100% 通過 | pytest テスト |
| SC-003 | Markdown フォーマットエラー 0 件 | markdownlint 実行結果 |
| SC-004 | 事実確認で「誤り」0 件（修正後） | blog-reviewer 実行結果 |
| SC-005 | SEO スコア 80 点以上 | searchstack-aeo + website-seo-audit |
| SC-006 | Astro content.config.ts スキーマ適合 | Zod スキーマ検証 |
| SC-007 | Mermaid ダイアグラム最低 1 つ | 生成記事の内容検証 |
