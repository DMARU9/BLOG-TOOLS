# Research: ブログ作成エージェント

**Feature**: 001-blog-writing-agent  
**Date**: 2026-08-06  
**Status**: Complete

## Research Items

### 1. open_deep_research API の利用方法

**Decision**: HTTP API 経由で呼び出し

**Rationale**: open_deep_research は LangGraph StateGraph として構築されており、`http://127.0.0.1:2024` で API を提供。既存の blog-reviewer エージェントがこの API を使用しており、互換性がある。

**Alternatives considered**:
- ライブラリとして直接インポート → 別プロセスでの実行が推奨されるため却下

**Implementation Details**:
```python
import httpx

async def call_research_api(query: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:2024/runs/stream",
            json={"input": {"query": query}}
        )
        return response.json()
```

---

### 2. pytrends のレートリミット対策

**Decision**: sleep + リトライ + キャッシュ

**Rationale**: pytrends は Google Trends の非公式 API を使用しており、短時間に大量のリクエストを送ると 429 エラーが発生。安全なレート制限が必要。

**Alternatives considered**:
- API キー不要の他のトレンドツール → 選択肢が限定的
- Selenium によるスクレイピング → 複雑すぎ

**Implementation Details**:
```python
from pytrends.request import TrendReq
import time

pytrends = TrendReq(hl='ja-JP', tz=540)

# レートリミット対策: 5 秒待機
time.sleep(5)

pytrends.build_payload(
    kw_list=[topic],
    cat=0,
    timeframe='today 12-m',
    geo='JP'
)
```

---

### 3. searchstack-aeo の無料コマンド仕様

**Decision**: CLI として subprocess で実行

**Rationale**: searchstack-aeo は `pip install searchstack` でインストール可能。無料コマンド（meta, schema, links, onpage）は API キー不要で使用可能。

**Alternatives considered**:
- ライブラリとしてインポート → CLI の方が柔軟性が高い

**Implementation Details**:
```python
import subprocess

def run_searchstack_meta(file_path: str) -> dict:
    result = subprocess.run(
        ["searchstack", "meta", file_path],
        capture_output=True,
        text=True
    )
    return parse_output(result.stdout)
```

---

### 4. markdownlint の Python からの呼び出し

**Decision**: subprocess で Node.js プロセスを呼び出し

**Rationale**: markdownlint は Node.js ツールであり、Python から直接インポートは不可。subprocess で CLI を呼び出すのが最もシンプル。

**Alternatives considered**:
- Python ラッパー（py-markdown-lint）→ 未検証
- 自作パーサー → 複雑すぎ

**Implementation Details**:
```python
import subprocess

def run_markdownlint(file_path: str) -> list:
    result = subprocess.run(
        ["npx", "markdownlint-cli", file_path],
        capture_output=True,
        text=True
    )
    return parse_markdownlint_output(result.stdout)
```

---

### 5. 既存ブログのスタイルガイド抽出

**Decision**: 既存記事の構造を解析してルールを抽出

**Rationale**: DMARU9.github.io には既存のブログ記事があり、その構造・トーン・フォーマットを分析してスタイルガイドを自動生成可能。

**Alternatives considered**:
- 手動でスタイルガイドを作成 → 時間がかかる
- LLM に既存記事を読んで理解させる → 可能だが不安定

**Implementation Details**:
- 既存の Markdown ファイルを解析
- frontmatter の構造を分析
- 見出しの使用パターンを抽出
- 比喩や表現の頻度を分析
- トーン（です・ます調）を確認

---

## Technology Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API 連携 | HTTP (httpx) | 既存の blog-reviewer と互換性 |
| トレンド分析 | pytrends | API キー不要、日本語対応 |
| SEO チェック | searchstack-aeo CLI | 無料コマンドが豊富 |
| Markdown 検証 | markdownlint CLI | 標準ツール、信頼性高い |
| スタイルガイド | 自動抽出 | 既存記事から学習可能 |
| エージェント構築 | VS Code Copilot Agent | 過度なフレームワーク導入を回避 |

## Open Questions

- searchstack-aeo の具体的なコマンドライン引数は要確認
- pytrends の exact レートリミットは未確定（要テスト）
- markdownlint のルールカスタマイズ方法は要調査
