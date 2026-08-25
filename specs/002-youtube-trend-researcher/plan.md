# Implementation Plan: YouTube Trend Researcher

**Branch**: `002-youtube-trend-researcher` | **Date**: 2026-08-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-youtube-trend-researcher/spec.md`

## Summary

自然言語のリサーチ指示を受け取り、yt-dlp を主体（検索・統計・チャンネル情報・字幕取得、API キー/クォータ不要）とし、コメント取得には youtube-comment-downloader、字幕不在動画の文字起こしには Whisper を用い、LangGraph で LLM 呼び出しをオーケストレーションする「YouTube Trend Researcher」を BLOG-TOOLS 配下に構築する。OpenDeepResearch のように、単一検索に依存せず複数角度から自律探索し、構造化されたレポート（動画リスト・伸び理由・共通点表・出典）を返す。データベースは使用せず、中間成果物はファイルキャッシュに永続化する。LLM は OpenDeepResearch の設定をそのまま流用し `openai:mimo-v2.5`（OpenAI 互換エンドポイント `https://opencode.ai/zen/go/v1`）を利用する。

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- `langgraph`, `langchain`, `langchain-openai`（LLM オーケストレーション／ODR 互換）
- `yt-dlp`（検索・統計・チャンネル情報・字幕取得の主体。API キー/クォータ不要）
- `openai-whisper`（字幕不在時の音声文字起こし；**GPU/CUDA 前提**）
- `pydantic`（設定・データモデル）
- `ffmpeg`（Whisper 用音声抽出、実行環境前提）
- `google-api-python-client`（オプション：高精度登録者数取得のフォールバックのみ。必須ではない）

> **Scope note (2026-08-26 clarification)**: v1 ではコメント取得（youtube-comment-downloader）は**対象外**。動画本文（字幕/Whisper）のみを分析に使用。将来拡張として予約。

**Storage**: なし（DB 非利用）。中間成果物・レポートはローカルファイルキャッシュ（`YouTube_Trend_Researcher/cache/`）に JSON で永続化（FR-012）。

**Testing**: pytest（unit/integration）、ruff（lint）、mypy（型検査）。Constitution IV 準拠。

**Target Platform**: Linux（ヘッドレス CLI／モジュール呼び出し）。GUI なし。

**Project Type**: CLI ツール 兼 ライブラリモジュール（LangGraph エージェント）。

**Performance Goals**: 10 件の動画リサーチを全体 100 分以内に完了。LLM 並列数は最大 2、API/ネットワークはリトライ・バックオフで長時間化を抑制。

**Constraints**:
- yt-dlp 検索はクエリあたりの結果件数に上限（数十〜百件程度）。複数角度探索でカバーし、不足時はクエリ分割。
- `channel_follower_count` は YouTube 側で非公開の場合取得不可。その際は YouTube Data API（オプション）または推定値でフォールバック。
- Whisper 実行に `ffmpeg` と **GPU（CUDA）リソース**が必要（Clarification: GPU 前提）
- LLM 並列実行数の上限は **2**（Clarification: analyze_content 等の同時呼び出し）
- 全体実行は **100 分**で上限。超過時は途中結果を返す（Clarification）
- 登録者数が非公開のチャンネル動画は候補から除外（FR-004: 補完・推定しない）
- ネットワーク外部アクセス必須（YouTube、モデルエンドポイント）
- 文字起こし欠損時はメタデータのみ分析へフォールバック
- ToS 考慮: yt-dlp による検索・取得は非公式アクセス。個人利用・リサーチ目的に留め、過度な頻度は避ける

**Scale/Scope**: 単一ユーザーのリサーチ用途。外部並行要求の要件はなし（内部で動画ごとの分析並列化は許容）。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 評価 | 根拠 |
|------|------|------|
| I. Purpose-Bound Tools | PASS | DMARU9.github.io のブログ記事リサーチ（トレンド動画の分析）に専用。Constitution の目的に合致。 |
| II. Centralized Tool Management | PASS | `BLOG-TOOLS/YouTube_Trend_Researcher/` に集約。外部リポジトリ取り込みなし。 |
| III. Modular Architecture | PASS | 自己完結パッケージ。依存を `pyproject.toml` で明示、個別テスト可能。 |
| IV. Quality Standards | PASS | ruff/mypy/pytest を適用、README とテストを同梱（計画通り）。 |
| V. Simplicity & Pragmatism | PASS | DB 非利用、CLI のみ、YAGNI 準拠。過度な抽象化なし。 |

全ゲート PASS。Complexity Tracking の記載不要。

## Project Structure

### Documentation (this feature)

```text
specs/002-youtube-trend-researcher/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── cli.md
│   ├── module-api.md
│   └── report-schema.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
YouTube_Trend_Researcher/
├── pyproject.toml
├── README.md
├── .env.example
├── src/
│   └── youtube_trend_researcher/
│       ├── __init__.py
│       ├── __main__.py            # CLI エントリ (python -m ...)
│       ├── config.py             # Config (モデル/APIキー/パス) - ODR から流用
│       ├── state.py              # LangGraph State
│       ├── graph.py              # LangGraph 構築 (Trend Engine)
│       ├── models.py             # Pydantic エンティティ
│       ├── prompts.py            # LLM プロンプト
│       ├── nodes/
│       │   ├── __init__.py
│       │   ├── parse_instruction.py     # 指示→構造化 (LLM)
│       │   ├── plan_searches.py         # 複数角度検索の立案 (LLM+反復)
│       │   ├── search_videos.py         # yt-dlp 主体の検索
│       │   ├── filter_candidates.py     # フィルタ適用
│       │   ├── fetch_transcripts.py     # yt-dlp + Whisper
│       │   ├── analyze_content.py       # 伸び理由分析 (LLM)
│       │   ├── extract_common.py        # 共通点抽出 (LLM)
│       │   └── compile_report.py        # レポート整形 (LLM/テンプレート)
│       └── tools/
│           ├── __init__.py
│           ├── youtube_search.py  # yt-dlp 主体の検索・統計・チャンネル情報
│           ├── transcript.py      # yt-dlp + whisper (GPU前提)
│           ├── youtube_api.py     # (オプション) 高精度登録者数フォールバック
│           ├── llm.py             # init_chat_model ヘルパ (ODR 流用設定)
│           └── parse.py           # LLM 出力の軽いパース関数 (Markdown/JSON抽出)
├── tests/
│   ├── unit/
│   └── integration/
└── cache/                     # 中間成果物 (DB 代替)
```

**Structure Decision**: Option 1（単一プロジェクト）を採用し、Constitution II に基づき BLOG-TOOLS 直下の独立モジュール `YouTube_Trend_Researcher/` として配置。既存 `blog_writer` と同格の sibling パッケージ。`src/` レイアウトで `python -m youtube_trend_researcher` による CLI 実行と、他コードからの import を両立。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

（本機能は Constitution に完全準拠しており、正当化が必要な違反は存在しない。）
