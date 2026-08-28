# Code Structure Insight — Report

対象: `youtube_trend_researcher` (commit 時点の `artifacts/` に基づく)
解析日: 2026-08-28

---

## 1. 全体像（関連図の解説）

依存図 (`pydeps_ytr.svg` / `packages_ytr.dot`) から読み取れる構造は、**「オーケストレーターが全ノードを束ね、共有ユーティリティに依存が集中する」** という単方向の階層です。循環依存は検出されませんでした。

```
                      __main__ (エントリーポイント)
                          │
                       graph  ← 全ノード (7) を編成するハブ
                          │
        ┌──────┬──────┬────┼─────┬──────┬──────┬──────────┐
        │      │      │    │     │      │      │          │
   parse_  plan_  search_ fetch_ analyze_ extract_ compile_  (nodes/)
   instruction search videos transcripts content  common   report
        │      │      │      │       │        │        │
        └──────┴──────┴──────┴───────┴────────┴────────┘
                 │            │            │
            tools.llm    tools.parse   tools.transcript / tools.youtube_search
                 └────────────┬────────────┘
                       models / state / progress / prompts (共有基盤)
```

- **中心的モジュール（多くから依存）**: `models` が最も広く依存されています（`graph`, 全 `nodes`, `state`, `tools.transcript`, `tools.youtube_search` から参照）。データの正体（DTO 定義）を一手に担っているため、変更時の影響範囲が最大です。`state` も同様に広く参照されています。
- **末端モジュール**: `tools.youtube_search`, `tools.transcript` は単一ノード（`search_videos` / `fetch_transcripts`）からのみ使われる「葉」です。`prompts` はプロンプト定数の提供のみ。
- **クラス構造**: このパッケージはクラスより *関数ベースのノード群*（`nodes/`, `tools/`）で構成されています。クラス図 (`classes_ytr.png`) は主に `models` の DTO 群を描きます。振る舞いのつながりは上記 pydeps 依存図の方が実態に即しています。

**注目点**: `graph` が 7 つのノードを直接 import して編成しており、ここが構成変更の際の唯一の変更点になっています（責務の集中度は適切）。一方 `compile_report` だけが `cache` に依存しており、キャッシュ永続化の責務は 1 箇所に閉じています。

---

## 2. 浮いているソース（孤立モジュール）

`isolated_modules.txt` の実データ:

```
youtube_trend_researcher.__main__
```

- `youtube_trend_researcher.__main__` —— **正常（エントリーポイント）**。誰からも import されるべきではない起動専用モジュールです。除外対象ではありません。
- それ以外のモジュールはすべて誰かから import されています。`cache` は `compile_report` から参照されているため、**未使用コード・配線漏れの疑いはありません**（※スキル説明の「cache が浮く」は仮の例であり、本リポジトリの実データでは該当しません）。

**結論**: 不要コード・未接続バグの疑いがある孤立モジュールは現在存在しません。

---

## 3. 設計の煩雑さ（複雑度ハイライト）

保守性指標 (`radon_mi.json`) は全モジュールで B 以上 = **低MI（保守性低下）のモジュールは 0 件**。モジュール単位の保守性は健全です。

循環複雑度ランク C（CC ≥ 11）の関数 7 件を抽出しました。複雑さの主因とリファクタ方向:

| CC | 関数 | ファイル | 複雑さの主因 | リファクタ方向 |
|----|------|----------|--------------|----------------|
| 17 | `search_videos` | `tools/youtube_search.py:22` | 取得件数の過剰取得判定、`continue` を伴うループ、期間フィルタ分岐、`max_results` 打切り | ①取得件数決定 ②`entry → VideoCandidate` 変換 ③フィルタ＋打切りループ、を別関数に分離 |
| 14 | `parse_instruction` | `nodes/parse_instruction.py:105` | CLI > 自然言語 > LLM の優先順位を if/else で縦に並べた `max_results` / `output_format` / `published_after` の解決 | `_resolve_max_results` / `_resolve_output_format` / `_resolve_published_after` のヘルパに抽出（優先順位ロジックの集約） |
| 12 | `run` | `graph.py:84` | SIGALRM タイムアウト設定、initial_state の組み立て | タイムアウト設定を `_install_timeout()` に、state 構築を `_build_initial_state()` に分離 |
| 12 | `main` | `__main__.py:39` | 引数パース、--since 検証、0件/不足時のエッジケース出力 | エントリーポイントとして許容範囲。検証のみ `_validate_args()` に抜く程度で十分 |
| 12 | `_analyze_one` | `nodes/analyze_content.py:48` | LLM 呼び出し + 概要のフォールバック 2 段（段落拾い / 切り口合成） | フォールバックを `_fallback_summary()` に抽出 |
| 12 | `_render_analysis_block` | `nodes/compile_report.py:75` | None ガード付きのメタ行組み立て、活用アイデア表・引用リストの文字列結合 | メタ行 builder と「表/リスト描画」ヘルパへの分割 |
| 12 | `fetch_transcript` | `tools/transcript.py:14` | yt-dlp オプション組み立て、DownloadError 時の空 Transcript 返却、subtitles/auto の選択 | オプション生成を `_build_ydl_opts()` に、subtitle 抽出を `_pick_subtitles()` に分離 |

補足（CC 10 の境界線）: `nodes/extract_common.py:_parse_themes` (10) も近いうちに注視。

---

## 4. 改善の優先順位（優先度付き TODO）

影響度 × 労力で順位付け。

| 優先度 | 項目 | 理由 | 次アクション |
|--------|------|------|--------------|
| 高 | `search_videos` の分割 (CC 17) | 最も複雑。取得・変換・フィルタが混在し、期間フィルタの挙動（メタデータ未取得時の通過）が読みにくい | 3 つの補助関数へ分離、単体テストで「期間内絞り込み」を固定 |
| 高 | `parse_instruction` の優先順位解決を抽出 (CC 14) | 3 つのフィールドで同じ「CLI > NL > LLM」パターンが重複。将来の項目追加でバグを生みやすい | 解決ヘルパを集約し、優先順位を 1 箇所で定義 |
| 中 | 報告系 2 関数の分割 (`_analyze_one`, `_render_analysis_block`) | フォールバック／描画の分岐が長いが、外部影響は局所的 | フォールバック・描画ヘルパへの抽出 |
| 中 | `run` / `fetch_transcript` の補助関数化 (CC 12) | タイムアウト・オプション生成が主因。テスタビリティ向上のため | `_install_timeout()` / `_build_ydl_opts()` 等へ分離 |
| 低 | `main` の検証分離 | エントリーポイントとして許容。副作用なし | 必要なら `_validate_args()` のみ |
| 監視 | 孤立モジュール | 現在は `__main__` のみで健全 | 新規モジュール追加時に `isolated_modules.txt` を確認し、意図しない浮きを検知 |

**現時点の総評**: 循環依存なし・保守性指標は全モジュール B 以上・孤立モジュールはエントリーポイントのみ。アーキテクチャ自体は健全で、**局所的な関数分割（上位 2 件）に集中すれば十分**です。モジュール解体や依存の再構成といった大掛かりな変更は不要です。
