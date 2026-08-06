# Data Model: ブログ作成エージェント

**Feature**: 001-blog-writing-agent  
**Date**: 2026-08-06

## Entities

### 1. BlogInput

ブログ作成エージェントへの入力データ。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| topic | str | Yes | ブログ記事のトピック |
| project_name | Optional[str] | No | 関連するプロジェクト名 |
| directory_path | Optional[str] | No | 参照するディレクトリパス |
| detailed_spec | Optional[str] | No | 詳細な内容指定 |

**Validation Rules**:
- topic は空文字不可
- directory_path は存在するディレクトリでなければならない

---

### 2. TrendResult

トレンド分析結果。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| topic | str | Yes | 分析対象のトピック |
| interest_over_time | List[dict] | Yes | 時系列の興味度データ |
| related_queries | List[str] | Yes | 関連クエリ一覧 |
| high_trend_topics | List[str] | No | 関連する高トレンドトピック |
| trend_score | float | Yes | トレンドスコア (0-100) |
| recommendation | str | Yes | トレンドに基づく推奨事項 |

**State Transitions**:
- ANALYZING → COMPLETED
- ANALYZING → ERROR (API エラー時)

---

### 3. ResearchResult

リサーチ結果。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| topic | str | Yes | リサーチ対象のトピック |
| summary | str | Yes | リサーチの要約 |
| sources | List[Source] | Yes | 参考文献一覧 |
| key_findings | List[str] | Yes | 主要な発見事項 |
| project_info | Optional[ProjectInfo] | No | プロジェクト情報 |

**Relationships**:
- BlogInput → ResearchResult (1:1)
- ResearchResult → Source (1:N)

---

### 4. Source

参考文献。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| url | str | Yes | ソースの URL |
| title | str | Yes | ソースのタイトル |
| reliability | float | Yes | 信頼度 (0-1) |
| excerpt | str | Yes | 抜粋 |

---

### 5. ProjectInfo

プロジェクト/ディレクトリ情報。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | プロジェクト名 |
| description | str | Yes | プロジェクトの説明 |
| tech_stack | List[str] | Yes | 技術スタック |
| readme_summary | str | Yes | README の要約 |
| directory_structure | Optional[str] | No | ディレクトリ構造 |

---

### 6. BlogPost

生成されたブログ記事。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | str | Yes | 記事タイトル (30-60 文字) |
| description | str | Yes | 記事の説明 (120-160 文字) |
| pubDate | str | Yes | 公開日 (ISO 8601) |
| tags | List[str] | Yes | タグ一覧 |
| draft | bool | Yes | 下書きフラグ |
| enableComments | bool | Yes | コメント有効フラグ |
| content | str | Yes | Markdown 本文 |
| slug | str | Yes | URL スラッグ |
| mermaid_diagrams | List[str] | No | Mermaid ダイアグラム（空リスト許容） |

**Validation Rules**:
- title は 30-60 文字
- description は 120-160 文字
- H1 は 1 つだけ
- H2→H3 の順序が正しい

**State Transitions**:
- DRAFT → REVIEWING → APPROVED → PUBLISHED

---

### 7. QualityReport

品質チェック結果。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fact_check | FactCheckResult | Yes | 事実確認結果 |
| format_check | FormatCheckResult | Yes | フォーマット検証結果 |
| overall_score | float | Yes | 総合スコア (0-100) |
| issues | List[Issue] | Yes | 検出された問題一覧 |

---

### 8. FactCheckResult

事実確認結果。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| checked_items | List[CheckedItem] | Yes | 確認済み項目一覧 |
| errors | List[str] | Yes | 誤り一覧 |
| warnings | List[str] | Yes | 警告一覧 |

---

### 9. CheckedItem

確認済み項目。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| statement | str | Yes | 確認対象の記述 |
| status | Literal["correct", "incorrect", "unverifiable"] | Yes | 判定結果 |
| source | Optional[str] | No | 根拠となるソース |

---

### 10. FormatCheckResult

フォーマット検証結果。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| markdown_errors | List[str] | Yes | Markdown エラー一覧 |
| frontmatter_valid | bool | Yes | frontmatter 検証結果 |
| heading_structure_valid | bool | Yes | 見出し構造の検証結果 |

---

### 11. Issue

検出された問題。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | Literal["error", "warning", "info"] | Yes | 問題の種類 |
| category | str | Yes | 問題のカテゴリ |
| message | str | Yes | 問題の説明 |
| line | Optional[int] | No | 問題が発生した行番号 |
| fix_suggestion | Optional[str] | No | 修正提案 |

---

### 12. SEOReport

SEO チェック結果。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title_length | int | Yes | タイトルの文字数 |
| description_length | int | Yes | 説明の文字数 |
| heading_count | dict | Yes | 見出しの数 (H1, H2, H3) |
| alt_text_coverage | float | Yes | alt テキストのカバレッジ (0-1) |
| score | float | Yes | SEO スコア (0-100) |
| recommendations | List[str] | Yes | 推奨事項一覧 |

---

### 13. FixReport

自動修正結果。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fixes_applied | List[Fix] | Yes | 適用された修正一覧 |
| fixes_skipped | List[Fix] | No | スキップされた修正一覧 |
| original_content | str | Yes | 修正前のコンテンツ |
| fixed_content | str | Yes | 修正後のコンテンツ |

---

### 14. Fix

個別の修正。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| issue | Issue | Yes | 修正対象の問題 |
| action | str | Yes | 実行された修正内容 |
| reason | str | Yes | 修正理由 |

---

### 15. ExecutionLog

実行ログ。

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | str | Yes | 実行日時 (ISO 8601) |
| agent | str | Yes | 実行されたエージェント名 |
| status | Literal["success", "error", "skipped"] | Yes | 実行ステータス |
| duration_seconds | float | Yes | 実行時間（秒） |
| details | Optional[str] | No | 詳細情報 |

---

## Relationships Diagram

```
BlogInput ──→ TrendResult
    │
    └──→ ResearchResult ──→ Source (N)
            │
            └──→ ProjectInfo
            
BlogPost ──→ QualityReport
    │           ├──→ FactCheckResult ──→ CheckedItem (N)
    │           └──→ FormatCheckResult
    │
    └──→ SEOReport

BlogPost ──→ FixReport ──→ Fix (N)

ExecutionLog (独立)
```

## State Machine

```
[START]
    │
    ▼
[ANALYZING TRENDS] ──→ [RESEARCHING] ──→ [WRITING]
    │                       │                  │
    │ (error)               │ (error)          │ (error)
    ▼                       ▼                  ▼
[ERROR] ◄──────────────────────────────────────┘
    │
    ▼
[QUALITY CHECK] ──→ [SEO CHECK] ──→ [FIXING] ──→ [OUTPUT]
    │                  │                │
    │ (issues found)   │ (issues found) │ (unfixable)
    ▼                  ▼                ▼
[REVIEW] ◄────────────────────────────────┘
    │
    ▼
[COMPLETE]
```
