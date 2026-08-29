# Implementation Plan: YouTube Trend Researcher

**Branch**: `002-youtube-trend-researcher` | **Date**: 2026-08-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-youtube-trend-researcher/spec.md`

## Summary

自然言語のリサーチ指示（ブログ記事の参考にしたいトピック）を受け取り、LangChain/LangGraph でオーケストレーションする「YouTube Trend Researcher」を BLOG-TOOLS 配下に構築する。v1 は**基本的な機能のみ**に絞り、以下の方針で実装する（spec 第3・第4ラウンド clarify に準拠）：

- **トレンド／伸びている判定は行わない**。yt-dlp の検索結果（関連度順）の上位 N 件（既定 **5 件**、指示で上書き可）を解析対象とする。
- **検索は単一クエリ**。指示文から LLM がトピック選定を含めて検索クエリを 1 つ生成し、yt-dlp（`ytsearchN:`）で 1 回検索する。複数角度からの自律探索（US2）は将来拡張。
- **字幕取得は yt-dlp のみ**。Whisper は利用しない。yt-dlp は自動翻訳字幕も取得できるため、字幕欠損は原則として起こらず、原則として必ず字幕テキストが取得できる。
- **要約はブログ執筆の参考向け**。各動画の内容を「ブログでどう扱えるか」の観点で要約し、動画間の共通ネタを抽出する。レポート構成は「選定動画リスト＋個別要約＋共通ネタ表」（執筆ヒントは含めない）。
- **インターフェースは CLI のみ**。プログラム API は将来拡張。
- **CLI 実行時は各ノードの進捗を表示（FR-013）**。どのノードにいるか／どの処理中かを stderr へ逐次出力し、最終レポート（stdout）と分離する。進捗と最終結果の間に「エラーまたは成功のみの空白状態」を作らない。

LLM は OpenDeepResearch の設定を流用し `openai:mimo-v2.5`（OpenAI 互換エンドポイント `https://opencode.ai/zen/go/v1`）を利用。データベースは使用せず、中間成果物はファイルキャッシュに JSON 永続化（FR-012）。

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- `langgraph`, `langchain`, `langchain-openai`（LLM オーケストレーション／ODR 互換）
- `yt-dlp`（検索・統計・字幕取得の主体。API キー/クォータ不要）
- `pydantic`（設定・データモデル）
- `python-dotenv`（`.env` 読み込み）

> **Scope note (2026-08-27 clarification / v1 簡素化)**:
> - Whisper（`openai-whisper`）・`ffmpeg` は **非利用**。yt-dlp のみで字幕取得（自動翻訳字幕含む）。
> - youtube-comment-downloader は **対象外**（v1 は動画本文のみ）。
> - YouTube Data API は **利用しない**。データ取得はすべて yt-dlp で行う（API キー・クォータ管理不要）。
> - 複数角度探索（plan_searches/reflect）は **将来拡張**。

**Storage**: なし（DB 非利用）。中間成果物・レポートはローカルファイルキャッシュ（`youtube_trend_researcher/cache/`）に JSON で永続化（FR-012）。

**Testing**: pytest（unit/integration）、ruff（lint）、mypy（型検査）。Constitution IV 準拠。

**Target Platform**: Linux（ヘッドレス CLI）。GUI なし。

**Project Type**: CLI ツール 兼 ライブラリモジュール（LangGraph エージェント）。

**Performance Goals**: 既定 5 件の動画リサーチを全体 100 分以内に完了。LLM 並列数は最大 2、API/ネットワークはリトライ・バックオフで長時間化を抑制。

**Constraints**:
- yt-dlp 検索はクエリあたりの結果件数に上限（数十〜百件程度）。上位 N 件（既定 5）を採用。
- LLM 並列実行数の上限は **2**（analyze_content 等の同時呼び出し）。
- 全体実行は **100 分**で上限。超過時は途中結果を返す。
- ネットワーク外部アクセス必須（YouTube、モデルエンドポイント）。
- 字幕は yt-dlp の自動翻訳字幕で原則として必ず取得できる。取得不能時のみ `notes` に記録。
- 最終レポートは stdout、進捗・ログは stderr へ分離（FR-013）。
- ToS 考慮: yt-dlp による検索・取得は非公式アクセス。個人利用・リサーチ目的に留め、過度な頻度は避ける。

**Scale/Scope**: 単一ユーザーのリサーチ用途。外部並行要求の要件はなし（内部で動画ごとの分析並列化は許容）。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 評価 | 根拠 |
|------|------|------|
| I. Purpose-Bound Tools | PASS | DMARU9.github.io のブログ記事リサーチ（関連動画の要約・共通ネタ抽出）に専用。Constitution の目的に合致。 |
| II. Centralized Tool Management | PASS | `BLOG-TOOLS/youtube_trend_researcher/` に集約。外部リポジトリ取り込みなし。 |
| III. Modular Architecture | PASS | 自己完結パッケージ。依存を `pyproject.toml` で明示、個別テスト可能。LangGraph グラフとして構造化。 |
| IV. Quality Standards | PASS | ruff/mypy/pytest を適用、README とテストを同梱（計画通り）。 |
| V. Simplicity & Pragmatism | PASS | DB 非利用、Whisper なし、単一検索、CLI のみ、YAGNI 準拠。過度な抽象化なし。 |

全ゲート PASS。Complexity Tracking の記載不要。

## Project Structure

### Documentation (this feature)

```text
specs/002-youtube-trend-researcher/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cli.md
│   └── report-schema.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
youtube_trend_researcher/
├── pyproject.toml
├── README.md
├── .env.example
├── src/
│   └── youtube_trend_researcher/
│       ├── __init__.py
│       ├── __main__.py            # CLI エントリ (python -m ...)
│       ├── config.py             # Config (モデル/APIキー/パス) - ODR から流用
│       ├── state.py              # LangGraph State
│       ├── graph.py              # LangGraph 構築 (Research Engine)
│       ├── models.py             # Pydantic エンティティ
│       ├── prompts.py            # LLM プロンプト
│       ├── progress.py           # ノード進捗表示ユーティリティ (FR-013)
│       ├── nodes/
│       │   ├── __init__.py
│       │   ├── parse_instruction.py     # 指示→構造化 (LLM)
│       │   ├── plan_search.py           # LLM が検索クエリを1つ生成
│       │   ├── search_videos.py         # yt-dlp 単一検索・上位N件選定
│       │   ├── fetch_transcripts.py     # yt-dlp 字幕取得
│       │   ├── analyze_content.py       # ブログ向け要約 (LLM, 並列)
│       │   ├── extract_common.py        # 共通ネタ抽出 (LLM)
│       │   └── compile_report.py        # レポート整形 (Markdown/JSON)
│       └── tools/
│           ├── __init__.py
│           ├── youtube_search.py  # yt-dlp 主体の検索
│           ├── transcript.py      # yt-dlp 字幕取得
│           ├── llm.py             # init_chat_model ヘルパ (ODR 流用設定)
│           └── parse.py           # LLM 出力の軽いパース関数
├── tests/
│   ├── unit/
│   └── integration/
└── cache/                     # 中間成果物 (DB 代替)
```

**Structure Decision**: Constitution II に基づき BLOG-TOOLS 直下の独立モジュール `youtube_trend_researcher/` として配置。既存 `blog_writer` と同格の sibling パッケージ。`src/` レイアウトで `python -m youtube_trend_researcher` による CLI 実行と、後続の `tasks.md` で定義する（将来拡張の）プログラム API import を両立。

## Node Graph (v1)

```
parse_instruction → plan_search → search_videos → fetch_transcripts
                                                          │
                                                          ▼
                                                   analyze_content (並列, 上限2)
                                                          │
                                                          ▼
                                                   extract_common → compile_report → END
```

- `plan_search`: 指示文から LLM がトピック選定を含めて検索クエリを 1 つ生成（Q4: LLM に委ねる）。
- `search_videos`: `ytsearchN:`（N = 件数指定、既定 5）で単一検索。関連度順上位 N 件を採用。トレンド判定・velocity 絞り込みは行わない。
- `fetch_transcripts`: yt-dlp で字幕取得（自動翻訳字幕含む）。原則として必ず取得できる。
- `analyze_content`: 各動画を「ブログ執筆の参考」として要約（並列上限 2）。
- `extract_common`: 動画間の共通ネタを抽出し、表の元とする。
- `compile_report`: 選定動画リスト＋個別要約＋共通ネタ表を Markdown/JSON で整形。

## Progress Display Design (FR-013)

CLI 実行時、各ノードの開始・完了を stderr へ逐次出力する。最終レポートは stdout へ出力し、進捗と分離する。これにより「コマンド実行してから、次の表示がエラーまたは成功メッセージのみ」という空白状態を防ぐ。

- 進捗フォーマット（案）:
  - `[1/7] parse_instruction ... 開始`
  - `[1/7] parse_instruction ... 完了`
  - `[2/7] plan_search ... 開始（LLM が検索クエリを生成中）`
  - `[2/7] plan_search ... 完了（クエリ: "..."）`
  - `[3/7] search_videos ... 開始`
  - `[3/7] search_videos ... 完了（N 件を選定）`
  - `[4/7] fetch_transcripts ... 開始`
  - `[4/7] fetch_transcripts ... 完了（字幕 N 件取得）`
  - `[5/7] analyze_content ... 開始（並列上限 2）`
  - `[5/7] analyze_content ... 完了`
  - `[6/7] extract_common ... 開始`
  - `[6/7] extract_common ... 完了`
  - `[7/7] compile_report ... 開始`
  - `[7/7] compile_report ... 完了`

- 進捗は常に何らかのメッセージ（次ノードの開始、または完了）で更新され、エラーまたは成功メッセージのみが表示される空白状態を作らない。
- 実装は `progress.py` のユーティリティで集約し、各ノードから呼び出す。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

（本機能は Constitution に完全準拠しており、正当化が必要な違反は存在しない。）
