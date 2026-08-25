# Contract: CLI Interface

**Created**: 2026-08-26
**Feature**: [spec.md](../spec.md)
**Plan**: [plan.md](../plan.md)

外部からの依頼を受け付けるコマンドライン・インターフェース（GUI なし）。

## Command

```bash
python -m youtube_trend_researcher "<INSTRUCTION>" \
  [--output PATH] \
  [--format markdown|json] \
  [--cache-dir PATH] \
  [--config PATH]
```

## Arguments

| 引数 | 必須 | 説明 |
|------|------|------|
| `INSTRUCTION` | 是 | 自然言語のリサーチ指示（例：「Claude Code で会社を回す方法を解説している動画で伸びているものを10個…」） |
| `--output PATH` | 否 | レポート出力先。省略時は標準出力へ出力 |
| `--format` | 否 | `markdown`（既定）または `json` |
| `--cache-dir PATH` | 否 | 中間成果物のキャッシュディレクトリ（既定：`cache/`） |
| `--config PATH` | 否 | `.env` ファイルのパス（既定：カレントの `.env`） |

## Environment Variables

| 変数 | 必須 | 説明 |
|------|------|------|
| `YOUTUBE_API_KEY` | 是 | YouTube Data API v3 キー |
| `OPENAI_API_KEY` | 是 | モデル API キー（ODR から流用：`https://opencode.ai/zen/go/v1` 用） |
| `OPENAI_BASE_URL` | 否 | モデルエンドポイント（既定：`https://opencode.ai/zen/go/v1`） |
| `YTR_MODEL` | 否 | モデル文字列（既定：`openai:mimo-v2.5`） |

## Exit Codes

| コード | 意味 |
|--------|------|
| 0 | 成功（レポート出力済み） |
| 1 | 汎用エラー（ネットワーク・API 等） |
| 2 | 設定/認証エラー（環境変数不足等） |
| 3 | 該当動画 0 件（条件緩和を要通知） |

## Behavior

- 人間の追加入力なしで最終レポートまで完了（FR-001）。
- 該当 0 件の場合でも `notes` に理由を記し、部分的結果を返す（Edge Cases）。
- 中間成果物を `--cache-dir` に JSON 出力（FR-012）。
