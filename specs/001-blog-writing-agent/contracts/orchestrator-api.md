# Contract: Orchestrator Interface

**Feature**: 001-blog-writing-agent
**Type**: Agent Interface + Tool App CLI
**Version**: 2.0.0

## Overview

ブログ作成フローの公開インターフェース定義。
フロー管理は Copilot エージェント（`.agent.md`）が担当し、Python ツールアプリはスタンドアロンの CLI として提供する。

**アーキテクチャ**: LangGraph は不使用。フロー管理は Copilot の自然な会話フローで実現。

---

## Agent Interfaces

### blog-writer (メインエージェント)

- **実行方法**: `/blog-writer "トピック"` (VS Code Copilot)
- **ユーザー実行**: ✅ のみ
- **フロー**: 入力解析 → トレンド分析 → リサーチ → 執筆 → 品質チェック → 出力

**入力**:
| パラメータ | 型 | 必須 | 説明 |
|-----------|------|:----:|------|
| topic | str | Yes | ブログ記事のトピック |
| project_name | str | No | 関連するプロジェクト名 |
| directory_path | str | No | 参照するディレクトリパス |
| detailed_spec | str | No | 詳細な内容指定 |

**出力**: Markdown ファイル + 実行レポート（標準出力）

**フロー内呼び出し**:
```
blog-writer
  ├─ runSubagent("blog-researcher") → TrendResult, ResearchResult
  ├─ (LLM) → BlogPost 生成
  ├─ runSubagent("blog-quality-checker") → QualityReport, SEOReport
  └─ (LLM) → Auto Fix → Markdown ファイル出力
```

### blog-researcher (サブエージェント)

- **実行方法**: `runSubagent("blog-researcher")` (blog-writer 内から呼び出し)
- **ユーザー実行**: ❌
- **ツール**: trend_analyzer.py, project_analyzer.py, open_deep_research API

### blog-quality-checker (サブエージェント)

- **実行方法**: `runSubagent("blog-quality-checker")` (blog-writer 内から呼び出し)
- **ユーザー実行**: ❌
- **ツール**: markdown_validator.py, seo_checker.py, searchstack-aeo, blog-reviewer

---

## Tool App CLI Interfaces

### trend_analyzer.py

```bash
# 基本実行
python -m blog_writer.trend_analyzer <topic>

# 出力: JSON (TrendResult)
# {
#   "topic": "string",
#   "interest_over_time": [{"date": "YYYY-MM-DD", "value": int}],
#   "related_queries": ["string"],
#   "high_trend_topics": ["string"],
#   "trend_score": float,
#   "recommendation": "string"
# }
```

### project_analyzer.py

```bash
# ディレクトリ解析
python -m blog_writer.project_analyzer <path>

# 出力: JSON (ProjectInfo)
# {
#   "name": "string",
#   "description": "string",
#   "tech_stack": ["string"],
#   "readme_summary": "string",
#   "directory_structure": "string"
# }
```

### seo_checker.py

```bash
# Markdown ベース SEO チェック
python -m blog_writer.seo_checker <file>

# 出力: JSON (SEOReport)
# {
#   "title_length": int,
#   "description_length": int,
#   "heading_count": {"h1": int, "h2": int, "h3": int},
#   "alt_text_coverage": float,
#   "score": float,
#   "recommendations": ["string"]
# }
```

### markdown_validator.py

```bash
# Markdown フォーマット検証
python -m blog_writer.markdown_validator <file>

# 出力: JSON
# {
#   "frontmatter_valid": bool,
#   "markdownlint_errors": [{"line": int, "rule": "string", "message": "string"}],
#   "overall_valid": bool
# }
```

---

## Output Data Types

```python
@dataclass
class TrendResult:
    topic: str
    interest_over_time: List[dict]
    related_queries: List[str]
    high_trend_topics: List[str]
    trend_score: float          # 0-100
    recommendation: str

@dataclass
class ResearchResult:
    topic: str
    summary: str
    sources: List[Source]
    key_findings: List[str]
    project_info: Optional[ProjectInfo]

@dataclass
class SEOReport:
    title_length: int
    description_length: int
    heading_count: dict
    alt_text_coverage: float    # 0-1
    score: float                # 0-100
    recommendations: List[str]

@dataclass
class QualityReport:
    fact_check: dict
    format_check: dict
    seo_check: SEOReport
    overall_score: float
    issues: List[dict]
```

---

## Usage Example

VS Code Copilot で `/blog-writer` コマンドを実行:

```
/blog-writer "Obsidian でナレッジ管理"

# 補足情報付き:
/blog-writer "open_deep_research" --project-name "open_deep_research" --detailed-spec "LangGraph のアーキテクチャについて"
```

## Error Handling

| Error Type | Condition | Recovery |
|------------|-----------|----------|
| ValueError | topic が空 | エージェントがユーザーに確認 |
| API Error | open_deep_research API エラー | server.sh で再起動 |
| Rate Limit | pytrends 429 エラー | 5 秒待機後にリトライ |
| Format Error | Markdown フォーマット不備 | quality-checker が自動修正 |
