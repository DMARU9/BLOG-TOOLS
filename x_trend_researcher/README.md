# X Trend Researcher

自然言語のリサーチ指示（ブログ記事の参考にしたいトピック）を受け取り、LangGraph でオーケストレーションする CLI ツール。`youtube_trend_researcher` と同じアーキテクチャを X（Twitter）向けに置き換えたもの。

- **データソースは `twscrape`**（非公式だが事実上の標準）。自アカウントのクッキーで認証し、複数アカウントのレートリミットを自動ローテーション。
- **トレンド調査が目的**。YouTube 版と違い「伸びている判定」を行う（いいね/RT/引用数を取得）。
- **検索は単一クエリ**。指示文から LLM が検索クエリを 1 つ生成し、`twscrape.search` で 1 回検索。
- **コンテキスト取得**: 各ツイートについて親ツイート（スレッド）と代表リプライを追加取得し、文脈を補完（YouTube の「字幕取得」に相当）。
- **インターフェースは CLI のみ**。
- **CLI 実行時は各ノードの進捗を stderr へ出力**。最終レポート（stdout）と分離する。

## セットアップ

```bash
cd /home/takumi/github/BLOG-TOOLS
cp x_trend_researcher/.env.example x_trend_researcher/.env
# .env を編集し OPENAI_API_KEY 等を設定
uv pip install -e x_trend_researcher[dev]

# アカウントクッキーを登録（X の auth_token / ct0 を export）
# 推奨: ブラウザ拡張 unjar で x.com のクッキーを取り出してパイプ
unjar x.com -f header | uv run --project x_trend_researcher twscrape add_cookie my_account
```

> `twscrape` は認証済みアカウントが必要です。クッキーの取り出しには `unjar` 等を利用してください。

## 使い方

```bash
# 既定 5 件・Markdown 出力
uv run python -m x_trend_researcher \
  "Claude Code で会社を回す方法を解説しているポストを参考にブログを書きたい"

# 件数指定・JSON 出力
uv run python -m x_trend_researcher \
  "機械学習チュートリアルを参考にブログを書きたい" \
  --max-results 10 --format json --output out.json

# 投稿日で絞り込み（明示指定）
uv run python -m x_trend_researcher \
  "機械学習 入門" --since 2026-02-27 --output recent.md

# 投稿日で絞り込み（自然言語でも可: 「半年以内」「3ヶ月以内」「1年以内」「今年」等）
uv run python -m x_trend_researcher \
  "半年以内に公開された機械学習の基礎投稿" --max-results 3 --output recent.md
```

### オプション

| オプション | 既定値 | 説明 |
|-----------|--------|------|
| `INSTRUCTION`（位置引数） | 必須 | 自然言語のリサーチ指示 |
| `--format {markdown,json}` | `markdown` | 最終レポートの出力形式 |
| `--max-results N` | `5` | 解析対象の投稿件数（関連度順上位 N 件） |
| `--output PATH` | 標準出力 | レポート書き込み先ファイル |
| `--since YYYY-MM-DD` | なし | 投稿日下限（この日以降に公開された投稿のみ対象） |
| `--cache-dir PATH` | `cache/` | 中間成果物の永続化先 |
| `--trends` | なし | トレンドワード探索モード（予約） |

### 出力チャネル

- **stdout**: 最終レポートのみ（Markdown または JSON）
- **stderr**: 進捗・ログ・エラー（FR-013）

### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 成功 |
| 1 | 実行時エラー（ネットワーク障害・LLM エラー・認証エラー等） |
| 2 | 引数エラー |

## アーキテクチャ

```
parse_instruction → plan_search → search_tweets → fetch_threads
                                                        │
                                                        ▼
                                                   analyze_content (並列, 上限2)
                                                        │
                                                        ▼
                                                   extract_common → compile_report → END
```

中間成果物は `cache/` に JSON で永続化される（FR-012）。

## YouTube 版との主な違い

| 項目 | YouTube 版 | X 版 |
|------|-----------|------|
| データソース | `yt-dlp`（認証不要） | `twscrape`（アカウントクッキー要） |
| 取得単位 | 動画 + 字幕 | ツイート + スレッド + リプライ |
| エンゲージメント | 再生数/高評価 | いいね/RT/引用/リプライ |
| トレンド判定 | 行わない | 行う（指標を活用） |
| 期間フィルタ | yt-dlp にないため過剰取得→絞込 | X 検索の `since:` を直接使用 |
