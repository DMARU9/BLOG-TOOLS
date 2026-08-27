# YouTube Trend Researcher

自然言語のリサーチ指示（ブログ記事の参考にしたいトピック）を受け取り、LangGraph でオーケストレーションする CLI ツール。v1 は基本機能に絞り、以下の方針で実装している。

- **トレンド／伸びている判定は行わない**。yt-dlp の関連度順検索結果の上位 N 件（既定 5 件）を解析対象とする。
- **検索は単一クエリ**。指示文から LLM がトピック選定を含めて検索クエリを 1 つ生成し、yt-dlp（`ytsearchN:`）で 1 回検索する。
- **字幕取得は yt-dlp のみ**。Whisper は利用しない（自動翻訳字幕を含む）。
- **要約はブログ執筆の参考向け**。各動画の内容を「ブログでどう扱えるか」の観点で要約し、動画間の共通ネタを抽出する。
- **インターフェースは CLI のみ**。
- **CLI 実行時は各ノードの進捗を stderr へ出力**。最終レポート（stdout）と分離する。

## セットアップ

```bash
cd /home/takumi/github/BLOG-TOOLS
cp youtube_trend_researcher/.env.example youtube_trend_researcher/.env
# .env を編集し OPENAI_API_KEY 等を設定
uv pip install -e youtube_trend_researcher[dev]
```

## 使い方

```bash
# 既定 5 件・Markdown 出力
uv run python -m youtube_trend_researcher \
  "Claude Code で会社を回す方法を解説している動画を参考にブログを書きたい"

# 件数指定・JSON 出力
uv run python -m youtube_trend_researcher \
  "機械学習チュートリアルを参考にブログを書きたい" \
  --max-results 10 --format json --output out.json
```

### オプション

| オプション | 既定値 | 説明 |
|-----------|--------|------|
| `INSTRUCTION`（位置引数） | 必須 | 自然言語のリサーチ指示 |
| `--format {markdown,json}` | `markdown` | 最終レポートの出力形式 |
| `--max-results N` | `5` | 解析対象の動画件数（関連度順上位 N 件） |
| `--output PATH` | 標準出力 | レポート書き込み先ファイル |
| `--lang CODE` | `ja` | 字幕取得の優先言語 |
| `--cache-dir PATH` | `cache/` | 中間成果物の永続化先 |

### 出力チャネル

- **stdout**: 最終レポートのみ（Markdown または JSON）
- **stderr**: 進捗・ログ・エラー（FR-013）

### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 成功 |
| 1 | 実行時エラー（ネットワーク障害・LLM エラー等） |
| 2 | 引数エラー |

詳細は `specs/002-youtube-trend-researcher/contracts/cli.md` を参照。

## 進捗表示（FR-013）

実行中は各ノードの開始・完了が stderr へ順次出力される（例：`[1/7] parse_instruction ... 完了`）。

## アーキテクチャ

```
parse_instruction → plan_search → search_videos → fetch_transcripts
                                                          │
                                                          ▼
                                                   analyze_content (並列, 上限2)
                                                          │
                                                          ▼
                                                   extract_common → compile_report → END
```

中間成果物は `cache/` に JSON で永続化される（FR-012）。
