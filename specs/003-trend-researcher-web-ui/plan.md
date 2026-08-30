# Implementation Plan: Trend Researcher Web UI

**Branch**: `003-trend-researcher-web-ui` | **Date**: 2026-08-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-trend-researcher-web-ui/spec.md`

## Summary

`trend_researcher` に LangGraph Studio UI を追加し、ブラウザからリサーチ指示・進捗確認・結果閲覧が可能にする。既存の `State` TypedDict を `MessagesState` ベースの `AgentState` に統一し、CLI と Web UI で同一のグラフを使用する。`langgraph.json` を追加して `langgraph dev` で起動可能にし、`Configuration` クラスで Studio UI 上のパラメータ変更に対応する。

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: LangGraph, LangChain, langgraph-cli[inmem]（dev 依存）

**Storage**: ファイルシステム（cache/）+ twscrape accounts.db

**Testing**: pytest（既存のテストフレームワークを維持）

**Target Platform**: ローカル開発環境（Linux/macOS）

**Project Type**: CLI + Web UI（LangGraph Studio）ツール

**Performance Goals**: リサーチ実行時間は CLI と同等（最大 100 分）

**Constraints**: ローカル開発・個人利用が目的。認証不要。

**Scale/Scope**: 1 ユーザー（個人利用）。trend_researcher パッケージ内のみの変更。

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Purpose-Bound Tools | ✅ PASS | ブログ運用（DMARU9.github.io）のコンテンツリサーチを支援するツール |
| II. Centralized Tool Management | ✅ PASS | BLOG-TOOLS プロジェクト配下（trend_researcher）で管理 |
| III. Modular Architecture | ✅ PASS | 既存モジュールを維持し、langgraph.json と Configuration を追加 |
| IV. Quality Standards | ✅ PASS | 既存テストを維持し、新的テストを追加。ruff/mypy 準拠 |
| V. Simplicity & Pragmatism | ✅ PASS | LangGraph Studio の標準機能を利用し、過度な抽象化を回避 |

**Gate Result**: ✅ ALL PASS — Phase 0 に進む

## Project Structure

### Documentation (this feature)

```text
specs/003-trend-researcher-web-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
trend_researcher/
├── langgraph.json              # NEW: LangGraph Studio 定義
├── pyproject.toml              # MODIFY: langgraph-cli[inmem] を dev 依存に追加
├── src/trend_researcher/
│   ├── __init__.py
│   ├── __main__.py             # MODIFY: asyncio.run() + ainvoke() ベースに変更
│   ├── graph.py                # MODIFY: MessagesState ベースのグラフに一本化
│   ├── state.py                # MODIFY: AgentState (MessagesState + 追加フィールド) に変更
│   ├── configuration.py        # NEW: Configuration クラス（config_schema 対応）
│   ├── config.py               # KEEP: 既存 Config（内部使用）
│   ├── models.py               # KEEP: 既存モデル定義
│   ├── prompts.py              # KEEP: 既存プロンプト
│   ├── progress.py             # MODIFY: LangGraph ストリーミング対応
│   ├── nodes/                  # KEEP: 既存ノード（シグネチャ変更あり）
│   ├── providers/              # KEEP: 既存プロバイダ
│   └── tools/                  # KEEP: 既存ツール
└── tests/
    ├── test_graph.py           # NEW: グラフ統合テスト
    └── test_configuration.py   # NEW: Configuration テスト
```

**Structure Decision**: 既存の trend_researcher パッケージ構造を維持し、`langgraph.json` と `configuration.py` を追加するのみ。過度な構造変更は行わない。

## Complexity Tracking

> Constitution Check に違反なし。Complexity tracking は不要。
