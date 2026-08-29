# Contract: CLI Interface

**Feature**: YouTube Trend Researcher (v1)
**Spec**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md)

## Command

```bash
python -m youtube_trend_researcher "<指示文>" [OPTIONS]
```

※ `uv run` 経由でも可: `uv run python -m youtube_trend_researcher "..."`

## Arguments

| 引数 | 必須 | 説明 |
|------|------|------|
| `INSTRUCTION` | はい | 自然言語のリサーチ指示（ブログで参考にしたいトピック等）。例：「Claude Code で会社を回す方法を解説している動画を参考にブログを書きたい」 |

## Options

| オプション | 既定値 | 説明 |
|-----------|--------|------|
| `--format {markdown,json}` | `markdown` | 最終レポートの出力形式 |
| `--max-results N` | `5` | 解析対象の動画件数（関連度順上位 N 件） |
| `--output PATH` | 標準出力 | レポート書き込み先ファイル（省略時は stdout） |
| `--lang CODE` | `ja` | 字幕取得の優先言語 |
| `--cache-dir PATH` | `cache/` | 中間成果物の永続化先 |

## Output Channels

- **stdout**: 最終レポートのみ（Markdown または JSON）。
- **stderr**: 進捗・ログ・エラー（FR-013）。進捗は各ノードの開始・完了ごとに出力。

### 進捗表示フォーマット（FR-013）

```
[1/7] parse_instruction ... 開始
[1/7] parse_instruction ... 完了
[2/7] plan_search ... 開始（LLM が検索クエリを生成中）
[2/7] plan_search ... 完了（クエリ: "..."）
[3/7] search_videos ... 開始
[3/7] search_videos ... 完了（N 件を選定）
[4/7] fetch_transcripts ... 開始
[4/7] fetch_transcripts ... 完了（字幕 M 件 / メタデータのみ K 件）
[5/7] analyze_content ... 開始（並列上限 2）
[5/7] analyze_content ... 完了
[6/7] extract_common ... 開始
[6/7] extract_common ... 完了
[7/7] compile_report ... 開始
[7/7] compile_report ... 完了
```

進捗は常に何らかのメッセージで更新され、エラーまたは成功メッセージのみが表示される空白状態を作らない。

## Exit Codes

| コード | 意味 |
|--------|------|
| 0 | 成功（レポートを stdout へ出力） |
| 1 | 実行時エラー（ネットワーク障害・LLM エラー等）。詳細は stderr |
| 2 | 引数エラー |

## Notes

- プログラム API（`research(instruction)` 等）は v1 では未提供（将来拡張）。
- YouTube Data API は利用しない。データ取得はすべて yt-dlp で行う（API キー不要）。
