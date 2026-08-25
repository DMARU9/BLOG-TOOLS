# Research: YouTube Trend Researcher

**Created**: 2026-08-26
**Feature**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

Phase 0 の調査成果。仕様の Technical Context にあった未確定事項を解決し、技術選定の根拠を記録する。

---

## R-1. データ取得 OSS の選定（yt-dlp 主体／YouTube Data API はオプション）

**背景（YouTube Data API の制限）**:
- 日次クォータ 10,000 ユニット。`search.list` は 100 ユニット/回のため 1 日 ~100 回検索が上限。
- 検索結果は関連度順で、**視聴回数・登録者数での並べ替え不可**。
- 登録者数取得には別途 `channels.list` が必要（追加コスト）。
- API キー申請とクォータ増額はレビュー必須で運用負荷大。

**Decision**: 検索・統計・チャンネル情報は **yt-dlp を主体**として取得し、YouTube Data API v3 は「高精度な登録者数が必要な場合のオプション」に降格する。
- **yt-dlp**（主体・API キー/クォータ不要）:
  - 検索: `ytsearchN:QUERY`（上位N件を取得）。**注: `ytsearchdateN:` は「直近N日」の窓フィルタではなく日付指定**。投稿日窓（直近半年等）は取得後の `upload_date` パースで絞り込む。
  - 統計: `view_count`（再生数）、`upload_date`（YYYYMMDD）、`like_count`
  - チャンネル: `channel_follower_count`（登録者数・非公開時は取得不可 → **その動画は候補除外**）
  - 字幕: `subtitles` / `automatic_captions`
- **youtube-comment-downloader**（コメント）: yt-dlp はコメントを安定取得できないため、別 OSS で取得。
- **Whisper**（`openai-whisper`） — 字幕が存在しない動画の音声文字起こし。yt-dlp で音声を取得し、ローカルで転写。
- **YouTube Data API v3**（オプション・非必須） — `channel_follower_count` が隠されている場合等の公式フォールバック。

**Rationale**:
- yt-dlp は API キー・クォータ不要で「検索＋統計＋登録者数＋字幕」を一貫取得でき、本ツールが求める「制限なし・複数角度探索」に最適。
- ユーザー例の「直近半年・低登録者・高再生」は取得したメタデータからフィルタ可能。`ytsearchdate` で投稿日窓も事前絞り込み可能。
- Whisper はローカルで動き、字幕不在動画でも「内容分析」の要件（FR-006/FR-007）を満たせる。

**Alternatives considered**:
- `youtube-transcript-api`：字幕取得に特化。取得範囲が狭いため yt-dlp に統合。
- 外部文字起こし API（AssemblyAI 等）：精度は高いがコスト・外部依存増。ローカル Whisper を優先。
- `youtube-search-python`：API キーなし検索ライブラリだが、yt-dlp の方が取得情報が豊富で保守も活発。
- スクレイピング（自前実装）：ToS 違反・不安定のため非採用。yt-dlp が事実上の標準。

---

## R-2. オーケストレーション設計（LangGraph + 複数角度探索）

**Decision**: OpenDeepResearch（ODR）を参考に、LangGraph の `StateGraph` でノードを繋ぎ、LLM 呼び出しを `init_chat_model` で行う。探索は「単一クエリ」ではなく、`plan_searches` ノードでトピックから複数の検索角度・クエリを生成し、反復（reflect）で追加探索を行う構成とする（FR-003 / US2）。

**Rationale**:
- ユーザーが「OpenDeepResearch のように自分で複数角度から検索」を明示的に要求。ODR の「supervisor が follow-up 検索を反復」パターンがそのまま適合。
- LangGraph の明示的グラフは、各ノード（解析・検索・文字起こし・分析・統合）を独立テスト可能にし、Constitution III（Modular Architecture）を満たす。

**Alternatives considered**:
- 単一スクリプトの手続き処理：テスト性・拡張性に劣るため非採用。
- 単一エージェントのツール呼び出しのみ：複数角度の「計画的」探索を制御しにくいため、plan/reflect ノードを分離。

**提案するグラフ構造（改善点）**:
```
parse_instruction → plan_searches → search_videos → filter_candidates
                                              ↑            │
                                              │            ▼
                                       (reflect: 追加角度) fetch_transcripts
                                                                │
                                                                ▼
                                                         analyze_content (並列)
                                                                │
                                                                ▼
                                                         extract_common
                                                                │
                                                                ▼
                                                         compile_report → END
```
- `plan_searches` と `reflect`（再検索判定）で ODR 的「複数角度からの自律探索」を実現。
- `analyze_content` は動画ごとに並列化し実用時間を短縮（Performance Goals）。

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

**解決ルール**（ODR `utils.get_api_key_for_model` を踏襲）:
- `"openai:"` プレフィックスのモデルは `OPENAI_API_KEY` を使用。
- `base_url` は `OPENAI_BASE_URL` から解決（既定 `https://opencode.ai/zen/go/v1`）。

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

**Decision**: データベースは使用しない。中間成果物（検索候補・文字起こし・分析・レポート）はローカルファイルキャッシュ（`YouTube_Trend_Researcher/cache/`）に JSON で永続化する（FR-012）。

**Rationale**:
- ユーザーが「データベースは利用する想定はありません」と明示。
- リサーチは実行ごとに完結し、後から参照・再現できれば十分。ファイル JSON で透明性と再現性を担保。

**Alternatives considered**: SQLite/Postgres：要件外の複雑さとなるため非採用。

---

## R-5. 外部インターフェース（GUI なし）

**Decision**: CLI（`python -m youtube_trend_researcher "<指示>"`）と Python モジュール API（`research()`）の両方を提供。GUI は v1 で非対象（FR-010 / US3）。

**Rationale**: ユーザーが「OpenDeepResearch のように外部から依頼→実行→取得」を指定。ODR が LangGraph サーバ／API で外部から呼ばれる形と同義。

**Alternatives considered**: Web UI / Gradio：現時点で不要と明示されたため非採用（将来拡張は `contracts/` で想定のみ）。

---

## R-6. 「制限なし」で同じ目的を達成する OSS 構成まとめ

**Decision**: YouTube Data API のクォータ/検索制限を回避するため、データ取得を **yt-dlp 主体**に切り替える。これにより API キー申請・クォータ管理が不要になり、ユーザーが懸念した「制限」が解消される。

**利用 OSS**:
| 目的 | 採用 OSS | 備考 |
|------|----------|------|
| 検索・統計・登録者数 | **yt-dlp** | `ytsearch`/`ytsearchdate`、クォータなし |
| 字幕・動画情報 | **yt-dlp** | captions 取得 |
| コメント | **youtube-comment-downloader** | yt-dlp は非対応 |
| 文字起こし（字幕なし） | **Whisper** | ローカル転写 |
| 高精度登録者数 | YouTube Data API v3（任意） | 隠蔽時のみフォールバック |

**「伸びている」の定義**: YouTube 公式のトレンドフィードはニッチ検索に弱いため、本ツールでは**メタデータから視聴velocity（再生数 ÷ 登録者数、かつ直近投稿）**を指標とし、「条件に合う動画」を自前で特定する。これによりトレンドフィードへ依存しない。**既定閾値: velocity ≥ 10.0 かつ 直近半年（180日）以内。** 指示で上書き可。`subscriber_count` が取得できない（非公開）動画は FR-004 により対象外とする。

**LLM 出力形態（Clarification）**: 構造化出力の強制は行わず、プロンプトで指示しつつ、堅牢性のため軽いパース関数（`tools/parse.py`）で Markdown/JSON を抽出して後続ノードへ渡す。

**実行時間上限（Clarification）**: 全体実行を **10 分**で上限とし、超過時は途中結果をまとめた部分的 `ResearchReport` を返す。

## 解決済み事項サマリ

| 項目 | 決定 |
|------|------|
| 検索・統計・登録者数 | yt-dlp（主体）／YouTube Data API v3（任意フォールバック） |
| 字幕・情報・コメント | 字幕/情報: yt-dlp、コメント: youtube-comment-downloader |
| 文字起こし（字幕なし） | Whisper（ローカル） |
| オーケストレーション | LangGraph StateGraph（複数角度探索 + reflect） |
| LLM | `openai:mimo-v2.5` @ `https://opencode.ai/zen/go/v1`（ODR 設定をコピー） |
| 永続化 | DB なし、JSON ファイルキャッシュ |
| インターフェース | CLI + モジュール API、GUI なし |

すべての `NEEDS CLARIFICATION` は解決済み。
