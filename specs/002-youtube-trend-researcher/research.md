# Research: YouTube Trend Researcher

**Created**: 2026-08-26 (updated 2026-08-27)
**Feature**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

Phase 0 の調査成果。v1 簡素化（2026-08-27）= 「トレンド判定なし・単一検索・Whisper なし・CLI のみ・ブログ参考向け要約」に基づき再整理。

---

## R-1. データ取得 OSS の選定（yt-dlp 主体／YouTube Data API は利用しない）

**背景**:
- ユーザーが「YouTube Data API は利用しない」と指定（2026-08-27 第5ラウンド）。API キー・クォータ管理は一切不要。
- 検索結果は関連度順で返るため、トレンド判定・velocity 絞り込みは **行わない**（上位 N 件をそのまま採用）。

**Decision**: 検索・統計・字幕取得は **すべて yt-dlp で行う**。YouTube Data API v3 は **利用しない**。字幕は yt-dlp の自動翻訳字幕（自動生成キャプションの翻訳）も取得できるため、字幕欠損は原則として起こらない。

- **yt-dlp**（主体・API キー/クォータ不要）:
  - 検索: `ytsearchN:QUERY`（上位N件を取得、関連度順）。N = 指示の件数指定（既定 5）。
  - 統計: `view_count`（再生数）、`upload_date`（YYYYMMDD）、`like_count`
  - チャンネル: `channel` / `channel_id` / `channel_url`
  - 字幕: `subtitles` / `automatic_captions`（自動翻訳字幕含む。原則として必ず取得可能）
- **Whisper** は **非利用**（2026-08-27 確定）。

**Rationale**:
- yt-dlp は API キー・クォータ不要で「検索＋統計＋字幕」を一貫取得でき、本ツールが求める「制限なし・関連度順上位N件」に最適。
- v1 は「トレンドか」を判定せず、yt-dlp の関連度順検索結果をそのまま利用するため、velocity 等の複雑な絞り込みは不要。

**Alternatives considered**:
- `youtube-transcript-api`：字幕取得に特化。取得範囲が狭いため yt-dlp に統合。
- `google-api-python-client`（YouTube Data API）：利用しない（ユーザー指定）。
- `openai-whisper`：字幕不在時の音声文字起こし。v1 では利用せず、かつ字幕は自動翻訳で原則取得可能のため非利用。
- スクレイピング（自前実装）：ToS 違反・不安定のため非採用。yt-dlp が事実上の標準。

---

## R-2. オーケストレーション設計（LangGraph + 単一検索）

**Decision**: OpenDeepResearch（ODR）を参考に、LangGraph の `StateGraph` でノードを繋ぎ、LLM 呼び出しを `init_chat_model` で行う。v1 は**単一クエリ検索**（複数角度探索は将来拡張／US2）。検索クエリは `plan_search` ノードで LLM に生成させる（Q4: LLM に委ねる）。

**Rationale**:
- ユーザーが「今フェーズは複数角度探索は行わない。将来的に多角的な判定を検討」と指定（2026-08-27 確定）。v1 は単一検索で十分。
- LangGraph の明示的グラフは、各ノード（解析・検索・文字起こし・分析・統合）を独立テスト可能にし、Constitution III（Modular Architecture）を満たす。
- 各ノードの進捗を CLI へ表示する要件（FR-013）とも親和性が高い。

**提案するグラフ構造（v1）**:
```
parse_instruction → plan_search → search_videos → fetch_transcripts
                                                          │
                                                          ▼
                                                   analyze_content (並列, 上限2)
                                                          │
                                                          ▼
                                                   extract_common → compile_report → END
```
- `plan_search` で LLM がトピック選定を含めた検索クエリを 1 つ生成。
- `search_videos` は `ytsearchN:` で単一検索し、関連度順上位 N 件を採用（トレンド判定なし）。
- `analyze_content` は動画ごとに並列化（上限 2）し実用時間を短縮。

---

## R-3. LLM 設定の流用（OpenDeepResearch からコピー）

**Decision**: ODR の設定をそのまま流用する。

**コピー元**:
- `open_deep_research/src/open_deep_research/configuration.py`
  - `research_model = "openai:mimo-v2.5"`（max_tokens 10000）
  - `summarization_model = "openai:mimo-v2.5"`（max_tokens 8192）
  - `final_report_model = "openai:mimo-v2.5"`（max_tokens 10000）
  - `compression_model = "openai:mimo-v2.5"`（max_tokens 8192）
- `open_deep_research/.env`
  - `OPENAI_API_KEY=<OpenCode キー>`
  - `OPENAI_BASE_URL=https://opencode.ai/zen/go/v1`（OpenAI 互換エンドポイント）

**実装方針**（`tools/llm.py`）:
```python
from langchain.chat_models import init_chat_model

def build_model(role: str = "research"):
    model = os.getenv("YTR_MODEL", "openai:mimo-v2.5")
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://opencode.ai/zen/go/v1")
    max_tokens = 8192 if role == "summary" else 10000
    return init_chat_model(
        model, max_tokens=max_tokens, api_key=api_key, base_url=base_url,
        tags=["langsmith:nostream"],
    )
```
- モデル文字列・エンドポイント・キー解決を ODR と同一にし、設定の「コピー」要件を満たす。
- ODR 同様 `configurable_fields=("model","max_tokens","api_key")` で実行時上書きを許容。

**Alternatives considered**: 別プロバイダ（Anthropic/Google）への切り替え：ユーザーが「ODR に登録している mimo-v2.5 を使う」と指定したため非採用。

---

## R-4. 永続化（データベース非利用）

**Decision**: データベースは使用しない。中間成果物（検索候補・文字起こし・分析・レポート）はローカルファイルキャッシュ（`youtube_trend_researcher/cache/`）に JSON で永続化する（FR-012）。

**Rationale**: リサーチは実行ごとに完結し、後から参照・再現できれば十分。ファイル JSON で透明性と再現性を担保。

**Alternatives considered**: SQLite/Postgres：要件外の複雑さとなるため非採用。

---

## R-5. 外部インターフェース（CLI のみ）

**Decision**: CLI（`python -m youtube_trend_researcher "<指示>"`）のみを提供。プログラム API 経由の呼び出しは将来拡張（2026-08-27 確定／Q5: Option B）。GUI は v1 で非対象（FR-010 / US3）。最終レポートは stdout、進捗・ログは stderr へ分離（FR-013）。

**Rationale**: ユーザーが「CLI が前提」と指定。ブログ運用の自動化にも CLI がそのまま使える。

**Alternatives considered**: Python モジュール API / Web UI / Gradio：現時点で不要と明示されたため非採用（将来拡張は `contracts/` で想定のみ）。

---

## R-6. 要約の目的（ブログ執筆の参考）

**Decision**: v1 の要約・分析は「ブログ記事執筆の参考」に特化。各動画の内容を「ブログでどう扱えるか」の観点で要約し、動画間の共通ネタを抽出する（FR-007 / FR-008）。レポート構成は「選定動画リスト＋個別要約＋共通ネタ表」とし、執筆ヒント／アウトライン案は含めない（Q2: Option B）。

**LLM 出力形態（Clarification）**: 構造化出力の強制は行わず、プロンプトで指示しつつ、堅牢性のため軽いパース関数（`tools/parse.py`）で Markdown/JSON を抽出して後続ノードへ渡す。

**実行時間上限（Clarification）**: 全体実行を **100 分**で上限とし、超過時は途中結果をまとめた部分的 `ResearchReport` を返す。

## 解決済み事項サマリ

| 項目 | 決定 |
|------|------|
| 検索・統計・字幕 | yt-dlp（のみ。YouTube Data API は利用しない） |
| 文字起こし（字幕） | yt-dlp（自動翻訳字幕含む）。原則として必ず取得可能 |
| オーケストレーション | LangGraph StateGraph（単一検索、複数角度は将来拡張） |
| 検索クエリ生成 | LLM が指示文から 1 つ生成（plan_search） |
| LLM | `openai:mimo-v2.5` @ `https://opencode.ai/zen/go/v1`（ODR 設定をコピー） |
| 永続化 | DB なし、JSON ファイルキャッシュ |
| インターフェース | CLI のみ（プログラム API は将来拡張）、進捗は stderr |

すべての `NEEDS CLARIFICATION` は解決済み。
