# Quickstart & Validation

**Created**: 2026-08-26
**Feature**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

実装完了後に、本機能が End-to-End で動くことを検証するための手順。詳細コードは `tasks.md`（Phase 2）に譲る。

## Prerequisites

- Python 3.11+
- `uv`（または `pip` + `venv`）
- `yt-dlp` および `ffmpeg`（Whisper 用）が実行可能パスに存在
- （オプション）高精度登録者数が必要な場合のみ `YOUTUBE_API_KEY` を設定。なければ yt-dlp の `channel_follower_count` を利用
- 環境変数：`OPENAI_API_KEY`（ODR 流用キー）、`OPENAI_BASE_URL=https://opencode.ai/zen/go/v1`

## Setup

```bash
cd BLOG-TOOLS/YouTube_Trend_Researcher
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env   # OPENAI_API_KEY を編集（YOUTUBE_API_KEY は任意）
```

## Validation Scenarios

### V1. 単体（モック）— グラフ接続の確認
- **準備**: YouTube API / LLM / Whisper をモックに差し替え（DI 経由）。
- **実行**: `pytest tests/unit` — 各ノードが State を正しく更新し、グラフが END に到達することを確認。
- **期待**: 全ノードの単体テストが緑。フィルタ・解析ロジックが期待通り。

### V2. 小規模 End-to-End（実 API）
- **実行**:
  ```bash
  python -m youtube_trend_researcher "Python 自動化 の解説動画を3個" --output out.md
  ```
- **期待**: `out.md` に 3 件の候補・伸び理由・出典が含まれる。中間 JSON が `cache/` に出力される。

### V3. ユーザー例の条件付きリサーチ（FR-005/SC-003）
- **実行**:
  ```bash
  python -m youtube_trend_researcher "Claude Codeで会社を回す方法を解説している動画で伸びているものを10個ピックアップして。直近半年以内・登録者が少ないのに再生が伸びているものに絞って。共通点は表でまとめて" --format markdown --output report.md
  ```
- **期待**:
  - 投稿日が直近半年外の動画は除外される。
  - 低登録者／高再生の閾値が適用されている（`notes` に閾値根拠）。
  - 共通点が「表」として `report.md` に含まれる（SC-004）。
  - 使用動画の URL・チャンネル・統計が明示（SC-002）。

### V4. 出力形式の切り替え（FR-009）
- **実行**: 同指示で `--format json` を指定。
- **期待**: [report-schema.md](./contracts/report-schema.md) に合致する JSON が出力される。

### V5. 例外系（Edge Cases）
- `YOUTUBE_API_KEY` 未設定 → exit 2 / `ConfigurationError`。
- 条件を満たす動画 0 件 → exit 3 / `NoCandidatesError`、かつ `notes` に理由。
- 字幕なし動画混入 → Whisper で文字起こし、`notes` に「Whisper 使用」と記録。

## Success Criteria との対応

| SC | 検証シナリオ |
|----|--------------|
| SC-001 自律完了 | V2/V3（追加入力なし） |
| SC-002 動画明示 | V2/V3 |
| SC-003 フィルタ適用 | V3 |
| SC-004 出力形式 | V3/V4 |
| SC-005 実用時間 | V2/V3（数分以内） |
| SC-006 複数角度探索 | V3（plan_searches/reflect のログで確認） |
