# Feature Specification: Trend Researcher Web UI

**Feature Branch**: `003-trend-researcher-web-ui`

**Created**: 2026-08-31

**Status**: Draft

**Input**: User description: "trend_researcher にブラウザ上で指示・回答を得られる GUI を追加する。open_deep_research と同様の仕組み（LangGraph Studio）で実現し、CLI は既存のまま維持する。"

## Purpose

`trend_researcher` は現在 CLI のみで利用可能である。本機能は、`open_deep_research` と同様に LangGraph Studio UI を利用してブラウザ上でリサーチ指示を入力し、進捗・結果をリアルタイムで確認できる Web UI を追加する。CLI 操作は既存のまま完全に維持する。

**背景**:
- `open_deep_research` は `langgraph.json` でグラフを定義し、`langgraph dev` で LangGraph Studio UI を提供
- `trend_researcher` は LangGraph を内部的に使用しているが、`langgraph.json` が存在しないため LangGraph Studio で起動できない
- ブログ運用において、ブラウザから直感的にリサーチ指示を入力・進捗を監視できる利便性が大きい

## User Scenarios & Testing *(mandatory)*

### User Story 1 - LangGraph Studio でブラウザからリサーチ実行 (Priority: P1)

ユーザーが `langgraph dev` を起動し、ブラウザの LangGraph Studio UI でリサーチ指示を入力して送信すると、各ノードの進捗がリアルタイムで表示され、最終レポートがブラウザ上で閲覧できる。

**Why this priority**: 本機能の核心価値。CLI と同等のリサーチ能力をブラウザ UI 経由で利用できること。

**Independent Test**: `langgraph dev` を起動し、Studio UI の `messages` フィールドにリサーチ指示を入力 → Submit することで、進捗表示とともに Markdown/JSON レポートが返されることを確認する。

**Acceptance Scenarios**:

1. **Given** ユーザーが `langgraph dev` を実行した, **When** ブラウザの Studio UI が開いた, **Then** API エンドポイント（localhost:2024）と Studio UI の URL が表示される
2. **Given** Studio UI が開いている, **When** ユーザーがリサーチ指示を `messages` フィールドに入力して Submit した, **Then** リサーチが開始され、各ノードの進捗がストリーミングで表示される
3. **Given** リサーチが完了した, **When** 結果を確認した, **Then** Markdown 形式のレポート（動画タイトル・URL・要約・共通ネタを含む）が表示される
4. **Given** リサーチ中にエラーが発生した, **When** エラーを確認した, **Then** エラーメッセージが Studio UI 上に表示され、ユーザーが再試行できる

---

### User Story 2 - CLI と Web UI の両立 (Priority: P1)

既存の CLI 操作（`python -m trend_researcher "指示" --platform x`）は新しい `MessagesState` ベースのグラフに一本化し、CLI と Web UI で同一のコードパスを使用する。CLI の引数・オプションはそのまま維持する。

**Why this priority**: 既存ユーザーのワークフローを壊さないことが必須。CLI と Web UI で同一のグラフを使うことでコードの保守性も向上する。

**Independent Test**: CLI で `python -m trend_researcher "テスト指示" --platform youtube` を実行し、従来と同等のレポートが出力されることを確認する。

**Acceptance Scenarios**:

1. **Given** グラフが `MessagesState` に一本化された, **When** CLI でリサーチを実行した, **Then** 従来と同等のレポートが出力される
2. **Given** Web UI が稼働中である, **When** 別のターミナルで CLI を実行した, **Then** 両方の実行が独立して動作する
3. **Given** CLI で使用可能なオプション（`--platform`, `--format`, `--max-results`, `--since` 等）がある, **When** Web UI で設定した, **Then** 同じパラメータがサポートされる

---

### User Story 3 - Web UI での設定カスタマイズ (Priority: P2)

ユーザーが Studio UI の「Manage Assistants」タブや設定フィールドから、プラットフォーム（X/YouTube）、出力形式、件数などのパラメータを変更できる。

**Why this priority**: CLI と同等の柔軟性を Web UI でも提供する。パラメータ変更は頻繁に行われる操作のため。

**Independent Test**: Studio UI の設定で `platform` を `youtube` に変更し、リサーチ指示を送信して YouTube の検索結果が返されることを確認する。

**Acceptance Scenarios**:

1. **Given** Studio UI が開いている, **When** `platform` 設定を `youtube` に変更した, **Then** YouTube 検索が実行される
2. **Given** Studio UI が開いている, **When** `output_format` を `json` に変更した, **Then** JSON 形式のレポートが出力される
3. **Given** Studio UI が開いている, **When** `max_results` を変更した, **Then** 指定件数分の候補が解析対象になる

---

### User Story 4 - 進捗のリアルタイム表示 (Priority: P2)

リサーチ実行中、LangGraph のノード遷移に応じて各フェーズ（指示解析→検索計画→検索→取得→分析→統合→レポート生成）の進捗が Studio UI 上でリアルタイムに表示される。

**Why this priority**: 長時間のリサーチにおいてユーザーに安心感と透明性を提供する。エラー発生時の早期検知にも有用。

**Independent Test**: リサーチを実行し、各ノードの開始・完了が Studio UI のストリーミング出力で確認できる。

**Acceptance Scenarios**:

1. **Given** リサーチが開始された, **When** 各ノードが実行された, **Then** ノード名とフェーズ（開始/完了）が Studio UI に表示される
2. **Given** 検索ノードが実行された, **When** 検索クエリが生成された, **Then** 使用されたクエリが Studio UI に表示される
3. **Given** リサーチがタイムアウトした, **When** 部分結果が返された, **Then** タイムアウトの旨と途中結果が Studio UI に表示される

---

### Edge Cases

- LangGraph Studio が起動できない場合（ポート競合、依存関係不足）：エラーメッセージが表示され、CLI は引き続き利用可能
- 同時に複数のリサーチセッションが実行された場合：各セッションは独立して処理される
- ネットワーク障害で外部 API（X/YouTube）にアクセスできない場合：エラーメッセージが Studio UI に表示される
- 大量の検索結果がある場合：`max_results` で制限され、超過分はスキップされる

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST `langgraph.json` で Trend Researcher の LangGraph グラフを定義し、`langgraph dev` で起動可能にする（認証なし、ローカル開発向け）
- **FR-002**: System MUST `open_deep_research` と同等の方法で LangGraph Studio UI を提供する（API エンドポイント + ブラウザ UI）
- **FR-003**: System MUST リサーチ指示を自然言語で受け取り、7 ノードのパイプラインを自律的に実行する
- **FR-004**: System MUST 各ノードの進捗をストリーミングで Studio UI に返す
- **FR-005**: System MUST X（Twitter）と YouTube の両プラットフォームに対応する
- **FR-006**: System MUST プラットフォーム（`platform`）、出力形式（`output_format`）、件数（`max_results`）等のパラメータを設定可能にする
- **FR-007**: System MUST CLI と Web UI で同一のグラフを使用し、既存の `run()` / `build_graph()` は新しい `MessagesState` ベースの実装に一本化する
- **FR-008**: System MUST レポートを Markdown および JSON 形式で出力する
- **FR-009**: System MUST タイムアウト時に途中結果を返す
- **FR-010**: System MUST `.env` ファイルから環境変数（API キー等）を読み込む

### Key Entities

- **LangGraph Graph**: Trend Researcher の 7 ノードパイプライン（parse_instruction → plan_search → search → fetch → analyze_content → extract_common → compile_report）。`langgraph.json` で定義され、`langgraph dev` でサーバーとして公開される
- **Configuration**: リサーチ実行時のパラメータ（platform, output_format, max_results, sort_by 等）。LangGraph の `configurable_fields` で受け渡す
- **State**: `MessagesState`（LangGraph 標準）に統一。`messages` リストでユーザー入力を受け取り、内部状態（instruction, candidates, contexts, analyses, common_themes, report 等）は TypedDict のフィールドとして管理。CLI と Web UI で共通のグラフを使用
- **Progress Emitter**: 各ノードから Studio UI への進捗通知。既存の `ProgressEmitter` を改良し、LangGraph のストリーミングに対応させる

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ユーザーが `langgraph dev` を実行してからブラウザでリサーチ指示を入力できるまでに、セットアップ作業が 3 コマンド以内（起動コマンドのみ）で完了する
- **SC-002**: リサーチ指示の送信から最終レポートの表示まで、Studio UI 上で進捗がリアルタイムに確認できる
- **SC-003**: 既存の CLI コマンドが Web UI 追加後も従来と同等に動作し、後方互換性が維持される
- **SC-004**: 各ノードの進捗が Studio UI のストリーミング出力で確認でき、ユーザーはリサーチの進行状況を把握できる
- **SC-005**: X（Twitter）と YouTube の両プラットフォームで、Studio UI からリサーチが実行可能になる

## Assumptions

- ユーザーは `langgraph-cli` をインストールすることができる（`uvx --from "langgraph-cli[inmem]" langgraph dev`）
- 既存の `.env` ファイルの設定（API キー等）がそのまま Web UI でも利用される
- LangGraph Studio UI は `open_deep_research` と同等の操作感で提供される
- リサーチの実行時間は CLI と同等（最大 100 分のタイムアウト）
- ブラウザはスタンドアロンの Chrome/Firefox/Safari を想定し、モバイル対応は不要
- ローカル開発・個人利用が目的のため認証は不要（必要に応じて後から追加）
- `langgraph-cli[inmem]` は `pyproject.toml` の `[project.optional-dependencies].dev` に追加する

## Clarifications

### Session 2026-08-31

- Q: グラフの入力形式をどうするか（既存 State vs MessagesState） → A: `MessagesState` に統一。CLI 側も `ainvoke({"messages": [...]}, config)` で呼び出し、Web UI と同一のグラフを使用
- Q: 既存 `run()` 関数の扱い → A: 既存の `run()` / `build_graph()` は削除し、すべて新しい `MessagesState` ベースのグラフに一本化する。CLI と Web UI で同一のエントリポイントを使用
- Q: 非メッセージ状態フィールドの扱い → A: `MessagesState` にフィールドを追加した `AgentState` を定義し、内部状態（candidates, analyses 等）を分離管理（`open_deep_research` の `AgentState` パターンに準拠）
- Q: Configuration クラスの設計 → A: 既存 `Config` を `Configuration` クラスにリファクタリングし、`config_schema` としてグラフに渡す（Studio UI でパラメータ変更が可能に）
- Q: CLI の非同期実行パターン → A: `asyncio.run()` で `ainvoke()` を呼び出す（`open_deep_research` パターン）
- Q: LangGraph サーバーの認証 → A: 認証なし。ローカル開発・個人利用が目的。必要になったら後から追加
- Q: `langgraph.json` の `dependencies` 設定 → A: `open_deep_research` と同一パターン（`"dependencies": ["."]` + `langgraph-cli[inmem]` を dev 依存に追加）
