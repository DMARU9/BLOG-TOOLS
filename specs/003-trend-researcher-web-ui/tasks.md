# Tasks: Trend Researcher Web UI

**Input**: Design documents from `/specs/003-trend-researcher-web-ui/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: プロジェクト初期化と基本構造の整備

- [x] T001 [P] `trend_researcher/langgraph.json` を作成し、LangGraph Studio 用のグラフエントリポイントを定義する（FR-001）
- [x] T002 [P] `trend_researcher/pyproject.toml` の `[project.optional-dependencies].dev` に `langgraph-cli[inmem]>=0.3.1` を追加する
- [x] T003 [P] `trend_researcher/src/trend_researcher/configuration.py` を新規作成し、`Configuration` クラス（`config_schema` 対応）を実装する（FR-006）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: すべてのユーザーストーリーの前提となるコアインフラ

**⚠️ CRITICAL**: このフェーズが完了するまでユーザーストーリーの作業は開始できない

- [x] T004 `trend_researcher/src/trend_researcher/state.py` を `MessagesState` ベースの `AgentState` に変更する。既存の `State` TypedDict を置き換え、`messages` フィールドを追加する（data-model.md 準拠）
- [x] T005 `trend_researcher/src/trend_researcher/graph.py` を `MessagesState` ベースのグラフに変更する。既存の `build_graph()` / `run()` を削除し、新しい `trend_researcher` エントリポイントを追加する（FR-007, contracts/api.md 準拠）
- [x] T006 `trend_researcher/src/trend_researcher/nodes/` 配下の各ノードのシグネチャを `AgentState` + `RunnableConfig` に変更する。`Configuration.from_runnable_config(config)` で設定値を取得するように修正する
- [x] T007 `trend_researcher/src/trend_researcher/progress.py` を LangGraph ストリーミング対応に変更する。stderr 出力を廃止し、`messages` リストへの `AIMessage` 追加に切り替える（FR-004）

**Checkpoint**: ファンデーション準備完了 — ユーザーストーリーの実装を並行で開始できる

---

## Phase 3: User Story 1 - LangGraph Studio でブラウザからリサーチ実行 (Priority: P1) 🎯 MVP

**Goal**: `langgraph dev` で起動し、Studio UI からリサーチ指示を入力してレポートを受け取る

**Independent Test**: `langgraph dev` を起動し、Studio UI の `messages` フィールドにリサーチ指示を入力 → Submit することで、進捗表示とともに Markdown/JSON レポートが返されることを確認する

### Implementation for User Story 1

- [x] T008 [P] [US1] `trend_researcher/langgraph.json` の `config_schema` フィールドが正しく `Configuration` クラスを参照していることを確認する。`langgraph dev` で起動できることを検証する（FR-001, FR-002）
- [x] T009 [US1] `trend_researcher/src/trend_researcher/graph.py` の `trend_researcher` エントリポイントが `ainvoke({"messages": [...]}, config)` で呼び出せることを確認する
- [x] T010 [US1] Studio UI でリサーチ指示を送信した場合、7 ノードのパイプラインが正しく実行され、最終レポートが `messages` に含まれることを確認する（FR-003）

**Checkpoint**: ユーザーストーリー 1 は独立して機能・テスト可能

---

## Phase 4: User Story 2 - CLI と Web UI の両立 (Priority: P1)

**Goal**: CLI からも同一のグラフを使用してリサーチを実行できる

**Independent Test**: CLI で `python -m trend_researcher "テスト指示" --platform youtube` を実行し、従来と同等のレポートが出力されることを確認する

### Implementation for User Story 2

- [x] T011 [US2] `trend_researcher/src/trend_researcher/__main__.py` を `asyncio.run()` + `ainvoke()` ベースに変更する。既存の CLI 引数（`--platform`, `--format`, `--max-results` 等）はそのまま維持する（FR-007）
- [x] T012 [US2] CLI 実行時に `RunnableConfig` に `configurable` 辞書を渡し、`Configuration` クラス経由で設定値がグラフに反映されることを確認する
- [x] T013 [US2] CLI の `--since` オプションが正しく `published_after` フィールドに反映されることを確認する
- [x] T014 [US2] CLI の `--trends` / `--sort` オプションが正しく `use_trends` / `sort_by` フィールドに反映されることを確認する

**Checkpoint**: ユーザーストーリー 2 は独立して機能・テスト可能

---

## Phase 5: User Story 3 - Web UI での設定カスタマイズ (Priority: P2)

**Goal**: Studio UI の「Manage Assistants」タブでパラメータを変更できる

**Independent Test**: Studio UI の設定で `platform` を `youtube` に変更し、リサーチ指示を送信して YouTube の検索結果が返されることを確認する

### Implementation for User Story 3

- [x] T015 [P] [US3] `trend_researcher/src/trend_researcher/configuration.py` の `Configuration` クラスに `model_json_schema()` が正しく JSON スキーマを生成することを確認する。Studio UI でパラメータが表示されることを検証する
- [x] T016 [US3] Studio UI で `platform` を `youtube` に変更した場合、YouTube 検索が実行されることを確認する
- [x] T017 [US3] Studio UI で `output_format` を `json` に変更した場合、JSON 形式のレポートが出力されることを確認する
- [x] T018 [US3] Studio UI で `max_results` を変更した場合、指定件数分の候補が解析対象になることを確認する

**Checkpoint**: ユーザーストーリー 3 は独立して機能・テスト可能

---

## Phase 6: User Story 4 - 進捗のリアルタイム表示 (Priority: P2)

**Goal**: リサーチ実行中に各ノードの進捗が Studio UI でリアルタイムに表示される

**Independent Test**: リサーチを実行し、各ノードの開始・完了が Studio UI のストリーミング出力で確認できる

### Implementation for User Story 4

- [x] T019 [P] [US4] 各ノード（parse_instruction, plan_search, search, fetch, analyze_content, extract_common, compile_report）の開始時に `AIMessage` を `messages` に追加する
- [x] T020 [P] [US4] 各ノードの完了時に完了メッセージを `messages` に追加する
- [x] T021 [US4] search ノードで生成された検索クエリを `messages` に含めることで、ユーザーが使用されたクエリを確認できるようにする
- [x] T022 [US4] タイムアウト時に途中結果を含むメッセージを `messages` に追加し、ユーザーが途中経過を確認できるようにする（FR-009）

**Checkpoint**: ユーザーストーリー 4 は独立して機能・テスト可能

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 品質向上とドキュメント整備

- [x] T023 [P] `trend_researcher/tests/test_graph.py` を新規作成し、`trend_researcher` グラフの統合テストを追加する
- [x] T024 [P] `trend_researcher/tests/test_configuration.py` を新規作成し、`Configuration` クラスの単体テストを追加する
- [x] T025 [P] `trend_researcher/README.md` を更新し、LangGraph Studio の起動方法と CLI の使い方を記載する
- [x] T026 [P] `ruff check` と `mypy` を実行し、コード品質を確認する
- [x] T027 [P] quickstart.md の検証シナリオを実際に実行し、動作を確認する

---

## Dependencies

### Story Completion Order

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1) + Phase 4 (US2) 並行可能
                                                  ↓
                                             Phase 5 (US3) + Phase 6 (US4) 並行可能
                                                  ↓
                                             Phase 7 (Polish)
```

### Parallel Execution Opportunities

**Phase 1**: T001, T002, T003 は並行実行可能（異なるファイル）

**Phase 3 + Phase 4**: US1 と US2 は並行実行可能（同一のグラフを使用するが、変更対象が異なる）

**Phase 5 + Phase 6**: US3 と US4 は並行実行可能（設定変更と進捗表示は独立）

**Phase 7**: T023, T024, T025, T026, T027 は並行実行可能（異なるファイル）

---

## Implementation Strategy

### MVP Scope

**User Story 1 + User Story 2** が MVP。これにより：
- LangGraph Studio UI からブラウザでリサーチが実行可能
- CLI からも同一のグラフでリサーチが実行可能

### Incremental Delivery

1. **Phase 1-2**: ファンデーション（langgraph.json, Configuration, AgentState, グラフ変更）
2. **Phase 3**: Studio UI でのリサーチ実行（MVP）
3. **Phase 4**: CLI の一本化（MVP）
4. **Phase 5**: Studio UI での設定カスタマイズ
5. **Phase 6**: 進捗のリアルタイム表示
6. **Phase 7**: 品質向上とドキュメント
