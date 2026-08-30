# Data Model: Trend Researcher Web UI

**Date**: 2026-08-31
**Feature**: 003-trend-researcher-web-ui

## AgentState (LangGraph State)

`MessagesState` をベースとし、内部状態フィールドを追加したグラフの状態定義。

### フィールド定義

| フィールド | 型 | 説明 |  mutate |
|-----------|-----|------|---------|
| `messages` | `list[BaseMessage]` | ユーザー入力・AI応答・進捗メッセージ（MessagesState 標準） | `add_messages` |
| `provider` | `Provider` | プラットフォームプロバイダ（X/YouTube） | 通常更新 |
| `config` | `Any` | 実行設定 | 通常更新 |
| `instruction` | `ResearchInstruction` | 解析済みリサーチ指示 | 通常更新 |
| `search_query` | `str` | 検索クエリ（単数） | 通常更新 |
| `search_queries` | `list[str]` | 検索クエリ（複数） | 通常更新 |
| `published_after` | `datetime \| None` | 投稿日下限 | 通常更新 |
| `max_results` | `int` | 解析対象件数 | 通常更新 |
| `output_format` | `OutputFormat` | 出力形式（markdown/json） | 通常更新 |
| `candidates` | `list[Candidate]` | 検索結果の候補リスト | 通常更新 |
| `contexts` | `list[Context]` | 要約用ソース（スレッド/字幕） | 通常更新 |
| `analyses` | `list[AnalysisFinding]` | 各候補の分析結果 | 通常更新 |
| `common_themes` | `list[CommonTheme]` | 共通ネタ | 通常更新 |
| `report` | `ResearchReport` | 最終レポート | 通常更新 |
| `notes` | `list[str]` | メモ・エラー情報 | 通常更新 |
| `use_trends` | `bool` | トレンドワード探索モード | 通常更新 |
| `sort_by` | `str` | 選定基準（relevance/likes） | 通常更新 |
| `transcript_language` | `str` | 字幕優先言語 | 通常更新 |
| `cache_dir` | `str \| None` | 中間成果物の永続化先 | 通常更新 |

### 遷移パターン

```
parse_instruction → plan_search → search → fetch → analyze_content → extract_common → compile_report
```

各ノードは `AgentState` を受け取り、更新したフィールドを含む辞書を返す。

## Configuration

LangGraph の `config_schema` として使用される設定クラス。

### フィールド定義

| フィールド | 型 | 既定値 | 説明 |
|-----------|-----|--------|------|
| `platform` | `str` | `"x"` | 対象プラットフォーム（x/youtube） |
| `output_format` | `str` | `"markdown"` | 出力形式（markdown/json） |
| `max_results` | `int` | `5` | 解析対象件数 |
| `sort_by` | `str` | `"relevance"` | 選定基準（relevance/likes） |
| `transcript_language` | `str` | `"ja"` | 字幕優先言語 |
| `use_trends` | `bool` | `False` | トレンドワード探索モード |
| `cache_dir` | `str \| None` | `None` | 中間成果物の永続化先 |

### 使用方法

```python
# RunnableConfig から取得
configurable = Configuration.from_runnable_config(config)

# 各ノードで設定値を参照
platform = configurable.platform
max_results = configurable.max_results
```

## 既存モデル（変更なし）

以下のモデルは変更せず維持：

- `ResearchInstruction`: リサーチ指示の構造化
- `Candidate`: 検索結果の候補（ツイート/動画）
- `Context`: 要約用ソース（スレッド/字幕）
- `AnalysisFinding`: 各候補の分析結果
- `CommonTheme`: 共通ネタ
- `ResearchReport`: 最終レポート
- `OutputFormat`: 出力形式の列挙型
