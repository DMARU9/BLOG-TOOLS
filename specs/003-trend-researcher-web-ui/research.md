# Research: Trend Researcher Web UI

**Date**: 2026-08-31
**Feature**: 003-trend-researcher-web-ui

## 1. LangGraph Studio UI の仕組み

### Decision
`langgraph.json` でグラフエントリポイントを定義し、`langgraph dev` コマンドで LangGraph Studio UI を提供する。

### Rationale
- `open_deep_research` と同等のアプローチを採用することで、ユーザーの学習コストを最小化
- LangGraph Studio は LangGraph 標準の UI であり、追加のフロントエンド実装が不要
- `langgraph-cli[inmem]` を使えば、外部サーバーなしでローカル起動が可能

### Alternatives Considered
- **FastAPI + カスタムフロントエンド**: 開発コストが高い。YAGNI 原則に反する
- **Streamlit/Gradio**: LangGraph のストリーミングやステート管理と相性が悪い
- **Jupyter Notebook**: 対話型だが、GUI としての利便性が不足

## 2. State の統一パターン

### Decision
既存の `State` TypedDict を `MessagesState` ベースの `AgentState` に変更する。`messages` フィールドでユーザー入力を受け取り、追加フィールドで内部状態を管理する。

### Rationale
- `open_deep_research` の `AgentState` パターンに準拠することで、LangGraph Studio との互換性を確保
- CLI と Web UI で同一のグラフを使用し、コードの保守性を向上
- `messages` はユーザー入力に専念し、内部状態は分離されたまま整理できる

### Implementation Pattern
```python
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    # 内部状態フィールド
    provider: Provider
    config: Any
    instruction: ResearchInstruction
    candidates: list[Candidate]
    contexts: list[Context]
    analyses: list[AnalysisFinding]
    common_themes: list[CommonTheme]
    report: ResearchReport
    notes: list[str]
```

## 3. Configuration クラスの設計

### Decision
既存の `Config` クラスを LangGraph の `config_schema` に対応した `Configuration` クラスにリファクタリングする。

### Rationale
- `config_schema` をグラフに渡すことで、Studio UI の「Manage Assistants」タブからパラメータ変更が可能に
- `open_deep_research` の `Configuration` パターンに準拠し、一貫性を確保
- `from_runnable_config()` メソッドで `RunnableConfig` から安全に設定値を取得

### Implementation Pattern
```python
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig

class Configuration(BaseModel):
    platform: str = Field(default="x")
    output_format: str = Field(default="markdown")
    max_results: int = Field(default=5)
    sort_by: str = Field(default="relevance")
    transcript_language: str = Field(default="ja")
    
    @classmethod
    def from_runnable_config(cls, config: RunnableConfig) -> "Configuration":
        configurable = config.get("configurable", {})
        return cls(**{k: v for k, v in configurable.items() if v is not None})
```

## 4. CLI の非同期実行

### Decision
`asyncio.run()` で `ainvoke()` を呼び出す。`open_deep_research` の `run_research.py` パターンに準拠する。

### Rationale
- LangGraph のグラフは非同期 (`ainvoke`) での実行を前提としている
- `asyncio.run()` は Python 標準の非同期実行方法であり、追加依存が不要
- CLI と Web UI で同一のグラフを使用するため、非同期対応が必須

### Implementation Pattern
```python
import asyncio
from langchain_core.messages import HumanMessage

async def run_async(instruction: str, config: dict) -> dict:
    graph = build_graph()
    return await graph.ainvoke(
        {"messages": [HumanMessage(content=instruction)]},
        config,
    )

def main():
    asyncio.run(run_async(instruction, config))
```

## 5. 進捗表示の LangGraph 対応

### Decision
既存の `ProgressEmitter` を改良し、LangGraph のメッセージストリーミングに対応させる。各ノードの開始・完了を `AIMessage` として `messages` に追加する。

### Rationale
- LangGraph Studio は `messages` フィールドのストリーミングを自動的に表示
- 既存の stderr への出力を廃止し、メッセージベースの進捗表示に統一
- ユーザーは Studio UI 上ですべての進捗を確認できる

### Implementation Pattern
各ノードで `update` 辞書に `messages` を追加：
```python
async def parse_instruction(state: AgentState, config: RunnableConfig):
    # ... ノード処理 ...
    return {
        "instruction": parsed_instruction,
        "messages": [AIMessage(content=f"[1/7] 指示を解析しました: {topic}")],
    }
```

## 6. langgraph.json の定義

### Decision
`open_deep_research` と同一パターンで `langgraph.json` を定義する。認証は不要。

### Rationale
- `"dependencies": ["."]` で自身のパッケージを参照
- `config_schema` で `Configuration` クラスを指定
- 認証なし（ローカル開発・個人利用が目的）

### Implementation
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
