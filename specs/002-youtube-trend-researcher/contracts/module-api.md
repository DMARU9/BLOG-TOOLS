# Contract: Python Module API

**Created**: 2026-08-26
**Feature**: [spec.md](../spec.md)
**Plan**: [plan.md](../plan.md)

他のコード（例：ブログ作成エージェント）からプログラムで呼び出すための API。

## Entry Point

```python
from youtube_trend_researcher import research, Config

config = Config()  # 環境変数 / .env から自動読込
report = await research(
    instruction="Claude Codeで会社を回す方法を解説している動画で伸びているものを10個ピックアップして",
    config=config,
)
print(report.candidates)        # list[VideoCandidate]
print(report.common_themes)    # list[CommonTheme]  (表の元)
```

## `research()`

| 引数 | 型 | 説明 |
|------|----|------|
| `instruction` | str | 自然言語指示 |
| `config` | Config | モデル/API/キャッシュ設定 |
| `instruction_obj` | ResearchInstruction \| None | 構造化指示を直接渡す場合（省略可） |

**Returns**: `ResearchReport`（[report-schema.md](./report-schema.md)）

**Raises**:
- `ConfigurationError`：環境変数/認証不足（CLI の exit 2 相当）
- `NoCandidatesError`：該当 0 件（CLI の exit 3 相当、部分的 report を返す実装も可）

## `Config`

| フィールド | 既定値 | 説明 |
|-----------|--------|------|
| youtube_api_key | `YOUTUBE_API_KEY` | YouTube Data API キー |
| openai_api_key | `OPENAI_API_KEY` | モデルキー |
| openai_base_url | `OPENAI_BASE_URL` or `https://opencode.ai/zen/go/v1` | エンドポイント |
| model | `YTR_MODEL` or `openai:mimo-v2.5` | モデル文字列 |
| cache_dir | `cache/` | 中間成果物ディレクトリ |
| transcript_language | `"ja"` | 優先字幕言語 |
| max_retries | 3 | API/LLM リトライ回数 |

## Notes

- すべての LLM 呼び出しは `tools/llm.py` の `build_model()` 経由で ODR 互換設定を使用。
- 非同期（`async`）で設計し、複数動画の分析を並列化（Performance Goals）。
