# ブログリサーチプロンプト

このプロンプトは、ブログ記事のリサーチを行う際のガイドラインを定義します。

## リサーチ手順

### 1. トレンド分析

以下のコマンドを実行して、トピックのトレンド情報を収集します：

```bash
python -m blog_writer.trend_analyzer "<topic>"
```

**注意点**:
- pytrends は Google Trends の非公式 API を使用しているため、短時間に大量のリクエストを送ると 429 エラーが発生
- リクエスト間は **5 秒以上** 待機すること
- エラーが発生した場合はリトライすること

### 2. Open Deep Research による深掘りリサーチ

以下のコマンドで Open Deep Research API を呼び出します：

```bash
curl -X POST http://127.0.0.1:2024/runs/stream \
  -H "Content-Type: application/json" \
  -d '{"input": {"query": "<topic>の詳細なリサーチ"}}'
```

**リサーチクエリの作成ガイドライン**:
- トピックを具体的に記述する
- 「とは」「仕組み」「使い方」などの補足を加える
- 日本語で検索する場合は適切なキーワードを選ぶ

### 3. プロジェクト解析 (任意)

ディレクトリパスが指定されている場合は、以下のコマンドでプロジェクト情報を収集します：

```bash
python -m blog_writer.project_analyzer "<path>"
```

## 出力形式

リサーチ結果は以下の JSON 形式で出力します：

```json
{
  "topic": "トピック",
  "trend_analysis": {
    "trend_score": 75.0,
    "related_queries": ["関連クエリ1", "関連クエリ2"],
    "recommendation": "このトピックは関心が高めです。"
  },
  "deep_research": {
    "summary": "リサーチの要約",
    "key_findings": ["発見事項1", "発見事項2"],
    "sources": [
      {
        "url": "https://example.com",
        "title": "ソースタイトル",
        "reliability": 0.9
      }
    ]
  },
  "project_info": {
    "name": "プロジェクト名",
    "tech_stack": ["Python", "TypeScript"],
    "description": "プロジェクトの説明"
  }
}
```

## 品質基準

### リサーチの品質
- [ ] 複数のソースから情報を収集している
- [ ] 情報の信頼性を確認している
- [ ] 最新の情報を使用している
- [ ] 日本語の情報を優先している

### 出力の品質
- [ ] JSON 形式で正しい
- [ ] 必須フィールドがすべて含まれている
- [ ] エスケープ処理が正しい
