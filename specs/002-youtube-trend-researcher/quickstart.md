# Quickstart: YouTube Trend Researcher

**Feature**: YouTube Trend Researcher (v1)
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

本手順は、v1 実装後に「指示→実行→レポート取得」が end-to-end で動くことを検証するためのもの。

## Prerequisites

- Python 3.11+
- `uv` インストール済み
- `yt-dlp` 利用可能（`uv run` で依存解決、またはシステムに導入）
- `.env` に `OPENAI_API_KEY` と `OPENAI_BASE_URL=https://opencode.ai/zen/go/v1` を設定（ODR 流用）
- ネットワークアクセス（YouTube、モデルエンドポイント）

## Setup

```bash
cd /home/takumi/github/BLOG-TOOLS
cp youtube_trend_researcher/.env.example youtube_trend_researcher/.env
# .env を編集し OPENAI_API_KEY 等を設定
```

## Validation Scenarios

### Scenario A: 既定 5 件・Markdown 出力

```bash
uv run python -m youtube_trend_researcher \
  "Claude Code で会社を回す方法を解説している動画を参考にブログを書きたい" \
  --format markdown
```

**期待結果**:
- stderr に各ノード進捗（[1/7]〜[7/7]）が順次表示される。
- stdout に選定動画リスト（関連度順上位 5 件）＋個別要約＋共通ネタ表を含む Markdown レポートが出力される。
- `cache/` に中間成果物（candidates/transcripts/analyses/report）が JSON で残る（FR-012）。

### Scenario B: 件数指定（10 件）・JSON 出力

```bash
uv run python -m youtube_trend_researcher \
  "機械学習チュートリアルを参考にブログを書きたい" \
  --max-results 10 --format json --output out.json
```

**期待結果**:
- 関連度順上位 10 件が解析対象となる（SC-003）。
- `out.json` に `ResearchReport` スキーマの JSON が書き出される。
- 進捗は stderr、レポートはファイル（または stdout）へ分離（FR-013）。

### Scenario C: 字幕取得の確認

- 任意の指示で実行し、各動画の字幕（自動翻訳字幕含む）が取得されていることを確認。
- 字幕は yt-dlp の自動翻訳で原則として必ず取得できる（FR-006）。

## Exit / Success Criteria Mapping

| SC | 検証 |
|----|------|
| SC-001 | 1 回の指示で追加入力なしにレポートが完成（A/B） |
| SC-002 | レポートに動画タイトル・URL・チャンネル・統計が明示（A/B） |
| SC-003 | 件数指定が反映（B: 10 件） |
| SC-004 | 共通ネタが表形式で出力（A: Markdown 表） |
| SC-005 | 全体 100 分以内に完了 |
| SC-006 | 単一クエリ検索で関連度上位 N 件を自動選定・要約・抽出まで完了 |

## Notes

- プログラム API は v1 未提供（CLI のみ）。
- 複数角度探索は将来拡張（US2）。
