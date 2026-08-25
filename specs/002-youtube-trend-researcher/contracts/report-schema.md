# Contract: Research Report Schema

**Created**: 2026-08-26
**Feature**: [spec.md](../spec.md)
**Plan**: [plan.md](../plan.md)

最終アウトプット `ResearchReport` の JSON スキーマ（`--format json` および `research()` の戻り値）。Markdown 出力はこの構造から生成される。

```json
{
  "instruction": {
    "raw_text": "string",
    "topic": "string",
    "filters": {
      "published_after": "2026-02-26 | null",
      "published_before": "null",
      "subscriber_max": 50000,
      "views_min": 10000,
      "velocity_ratio": 10.0,
      "max_results": 10,
      "relevance_keywords": ["Claude Code", "会社", "効率化"]
    },
    "output": {
      "format": "markdown | json",
      "table_for": ["common_points"]
    }
  },
  "generated_at": "2026-08-26T12:00:00Z",
  "candidates": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "string",
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "channel_id": "UCxxxx",
      "channel_title": "string",
      "published_at": "2026-07-01T00:00:00Z",
      "view_count": 123456,
      "like_count": 8900,
      "subscriber_count": 12000,
      "relevance_score": 0.92
    }
  ],
  "analyses": [
    {
      "video_id": "dQw4w9WgXcQ",
      "trending_reason": "実務での具体的な活用法を示しているため",
      "evidence": ["文字起こし抜粋1", "文字起こし抜粋2"]
    }
  ],
  "common_themes": [
    {
      "theme": "具体的なユースケース提示",
      "description": "多くの動画が実務事例を出している",
      "supporting_video_ids": ["dQw4w9WgXcQ", "..."],
      "example_quotes": ["抜粋", "..."]
    }
  ],
  "sources": [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  ],
  "notes": [
    "動画 X は字幕なしのため Whisper で文字起こし",
    "条件を満たす動画が 7 件のみ（10 件未満）"
  ]
}
```

## Markdown 出力フォーマット（既定）

1. **概要** — 指示の要約と前提
2. **選定動画リスト** — 表（タイトル・URL・チャンネル・再生・登録者・投稿日）
3. **動画ごとの伸び理由** — 各動画の `trending_reason` + 根拠抜粋
4. **共通点（表）** — `common_themes` を行とする表（指示で「表で」指定時）
5. **出典** — `sources`
6. **注記** — `notes`

## マッピング

- `candidates` → FR-004 / FR-010（動画リスト・出典）
- `analyses` → FR-007（伸び理由）
- `common_themes` → FR-008 / FR-009（共通点・表出力）
- `notes` → Edge Cases（字幕欠損・件数不足等の透明性）
