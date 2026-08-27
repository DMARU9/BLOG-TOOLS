# Contract: Report Schema

**Feature**: YouTube Trend Researcher (v1)
**Spec**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md)

最終レポート `ResearchReport` の出力スキーマ。CLI の `--format` に応じ markdown または JSON で出力（FR-009）。構成は「選定動画リスト＋個別要約＋共通ネタ表」（執筆ヒントは含めない／Q2: Option B）。

## Markdown 出力構成

```markdown
# リサーチレポート: <指示の要約>

## 選定動画リスト（関連度順上位 N 件）
| # | タイトル | チャンネル | 再生数 | URL |
|---|----------|------------|--------|-----|
| 1 | ... | ... | ... | ... |

## 各動画のブログ向け要約
### 1. <タイトル>
- 要約: ...
- ブログで取り上げられそうなポイント:
  - ...
- 根拠: ...

## 共通ネタ（表）
| テーマ | 説明 | 該当動画 | 代表抜粋 |
|--------|------|----------|----------|
| ... | ... | ... | ... |

## 出典
- <URL> (×N)

## 備考
- 字幕なし動画はメタデータのみで解析（Whisper なし）
- ...
```

## JSON スキーマ（抜粋）

```json
{
  "instruction": {
    "raw_text": "string",
    "topic": "string",
    "max_results": 5,
    "output": { "format": "markdown", "table_for": ["common_points"] }
  },
  "generated_at": "2026-08-27T12:00:00Z",
  "candidates": [
    {
      "video_id": "string",
      "title": "string",
      "url": "https://www.youtube.com/watch?v=...",
      "channel_id": "string",
      "channel_title": "string",
      "published_at": "2026-01-01T00:00:00Z",
      "view_count": 12345,
      "like_count": 678,
      "relevance_rank": 1
    }
  ],
  "analyses": [
    {
      "video_id": "string",
      "summary": "string",
      "key_points": ["string"],
      "evidence": ["string"]
    }
  ],
  "common_themes": [
    {
      "theme": "string",
      "description": "string",
      "supporting_video_ids": ["string"],
      "example_quotes": ["string"]
    }
  ],
  "sources": ["https://www.youtube.com/watch?v=..."],
  "notes": ["string"]
}
```

## 不変条件

- `sources` は `candidates` の `url` を全件含む。
- `analyses` と `common_themes` は `candidates` に対応する（字幕欠損時は `notes` に記録）。
- 実行が 100 分を超過した場合は、到達済みの `candidates`/`analyses`/`common_themes` を含む部分的レポートを返す。
