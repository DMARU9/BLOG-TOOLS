# Contracts: Trend Researcher Web UI

**Date**: 2026-08-31
**Feature**: 003-trend-researcher-web-ui

## LangGraph Graph Contract

### エントリポイント

```python
# graph.py
trend_researcher = build_graph()  # CompiledStateGraph
```

### グラフ構造

```
START → parse_instruction → plan_search → search → fetch → analyze_content → extract_common → compile_report → END
```

### 入力

```python
{
    "messages": [{"role": "user", "content": "リサーチ指示テキスト"}]
}
```

### 出力

```python
{
    "messages": [...],           # 進捗・結果メッセージ
    "report": ResearchReport,    # 最終レポート
    "candidates": [...],         # 候補リスト
    "analyses": [...],           # 分析結果
    "common_themes": [...],      # 共通ネタ
}
```

### Configuration（config_schema）

```python
{
    "configurable": {
        "platform": "x",           # "x" | "youtube"
        "output_format": "markdown", # "markdown" | "json"
        "max_results": 5,
        "sort_by": "relevance",    # "relevance" | "likes"
        "transcript_language": " "ja"",
        "use_trends": false,
        "cache_dir": null
    }
}
```

## CLI Contract

### コマンド

```bash
python -m trend_researcher <instruction> [options]
```

### オプション

| オプション | 型 | 既定値 | 説明 |
|-----------|-----|--------|------|
| `instruction` | str | （必須） | リサーチ指示テキスト |
| `--platform` | choice | `x` | 対象プラットフォーム（x/youtube） |
| `--output` | str | stdout | レポート書き込み先ファイル |
| `--format` | choice | `markdown` | 出力形式（markdown/json） |
| `--max-results` | int | `5` | 解析対象件数 |
| `--lang` | str | `ja` | 字幕優先言語（YouTube 用） |
| `--since` | str | None | 投稿日下限（YYYY-MM-DD） |
| `--cache-dir` | str | `cache/` | 中間成果物の永続化先 |
| `--trends` | flag | False | トレンドワード探索モード（X 用） |
| `--sort` | choice | `relevance` | 選定基準（relevance/likes） |

### 終了コード

| コード | 説明 |
|--------|------|
| 0 | 正常終了 |
| 1 | 実行時エラー |
| 2 | 引数エラー |

## Configuration Contract

### クラス定義

```python
class Configuration(BaseModel):
    platform: str = "x"
    output_format: str = "markdown"
    max_results: int = 5
    sort_by: str = "relevance"
    transcript_language: str = "ja"
    use_trends: bool = False
    cache_dir: str | None = None
    
    @classmethod
    def from_runnable_config(cls, config: RunnableConfig) -> "Configuration":
        ...
```

### 使用方法

```python
# 各ノードで設定値を取得
configurable = Configuration.from_runnable_config(config)
platform = configurable.platform
```

## langgraph.json Contract

```json
{
    "dockerfile_lines": [],
    "graphs": {
        "Trend Researcher": "./src/trend_researcher/graph.py:trend_researcher"
    },
    "python_version": "3.11",
    "env": "./.env",
    "dependencies": ["."],
    "config_schema": "./src/trend_researcher/configuration.py:Configuration"
}
```
