# Feature Specification: ブログ作成エージェント

**Feature Branch**: `001-blog-writing-agent`

**Created**: 2026-08-06

**Status**: Draft

**Input**: User description: "ブログを作成するためのAIエージェント（オーケストレーター型、サブエージェント分離）。入力はトピック（必須）と、プロジェクト名・ディレクトリパス・詳細な内容指定（補足情報）。searchstack-aeo は記事生成後とデプロイ後の両方で実行。"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - トピックからブログ記事を自動生成 (Priority: P1)

ユーザーがトピック（必須）と、必要に応じてプロジェクト名・ディレクトリパス・詳細な内容指定（補足情報）を入力すると、リサーチから執筆、品質チェック、SEO最適化、自動修正まで一気通貫でブログ記事が完成し、`DMARU9.github.io/src/content/blog/` に配置される。

**入力ルール**: トピックは必ず必要。プロジェクト名・ディレクトリパス・詳細な内容指定は補足情報として扱い、トピックの深掘りや具体化に活用する。

**Why this priority**: ブログ作成の主要ユースケースであり、エージェントの核心機能。これを実現することで即座に価値を提供できる。

**Independent Test**: トピック「Obsidian でナレッジ管理」を入力し、完成した Markdown ファイルが出力されることを確認する。frontmatter が正しいこと、Mermaid ダイアグラムが含まれること、SEO チェックが通過することを検証する。

**Acceptance Scenarios**:

1. **Given** ユーザーが「Obsidian でナレッジ管理」と入力した, **When** エージェントを実行した, **Then** `src/content/blog/obsidian-knowledge-management.md` が生成される
2. **Given** ユーザーがトピックに加えてプロジェクト名やディレクトリパスを指定した, **When** エージェントを実行した, **Then** 補足情報として対象の情報を自動参照し、トピックの深掘りに活用して記事が生成される
3. **Given** トピック入力があった, **When** リサーチエージェントが実行された, **Then** 信頼できるソースから事実情報を収集する
4. **Given** リサーチ結果がある, **When** 執筆エージェントが実行された, **Then** スタイルガイドに準拠した Markdown が生成される
5. **Given** 記事が生成された, **When** 品質チェックが実行された, **Then** 事実誤り・フォーマット不備・SEO 問題が自動修正される

---

### User Story 2 - トピック + 詳細指定からの記事生成 (Priority: P2)

ユーザーがトピックに加えて、プロジェクト名、ディレクトリパス、または詳細な内容指定を与えると、リポジトリの README・ソースコード・ディレクトリ構成を自動参照して、トピックを深掘りした記事を生成する。

**Why this priority**: ユーザーは「DMARU9 保有プロジェクトの説明」だけでなく、既存コードベースの説明、技術的な深掘り、特定ディレクトリの解説など、トピックに補足情報を加えて記事を依頼する。この柔軟性が実用性を大きく左右する。

**Independent Test**: トピック「open_deep_research」+ 補足「LangGraph のアーキテクチャについて」を入力し、README やソースコードの情報が反映された記事が生成されることを確認する。

**Acceptance Scenarios**:

1. **Given** ユーザーがトピック「open_deep_research」+ 補足「LangGraph のアーキテクチャについて」を指定した, **When** リサーチエージェントが実行された, **Then** プロジェクトの README とソースコードから LangGraph 関連の情報が収集される
2. **Given** ユーザーがトピック + ディレクトリパスを指定した, **When** リサーチエージェントが実行された, **Then** そのディレクトリの構成・主要ファイルの内容が解析され、トピックの深掘りに活用される
3. **Given** ユーザーがトピック + 詳細な内容（「Inbox → Archive モデルについて深掘りして」など）を指定した, **When** 執筆エージェントが実行された, **Then** 指定された内容に焦点を当てた記事が生成される

---

### User Story 3 - 品質レポートの取得 (Priority: P2)

エージェント実行後に、リサーチ・執筆・品質チェック・SEO の各段階の結果レポートが取得できる。

**Why this priority**: 透明性を担保し、ユーザーがエージェントの判断を理解・検証できるようにする。

**Independent Test**: エージェント実行後、各段階のレポートが標準出力またはファイルに出力されることを確認する。

**Acceptance Scenarios**:

1. **Given** エージェントが実行された, **When** 完了した, **Then** 各エージェントの実行結果サマリーが表示される
2. **Given** 品質チェックが実行された, **When** 問題が検出された, **Then** 修正内容と修正理由がレポートされる

---

### Edge Cases

- トピックが曖昧でリサーチの方向性が定まらない場合 → open_deep_research の clarification 機能でユーザーに確認
- 既存記事と内容が重複する場合 → 重複チェックを行い、差別化ポイントを提案
- 事実確認で信頼できるソースが見つからない場合 → 「要確認」としてマークし、修正せずに残す
- frontmatter の必須フィールドが不足している場合 → デフォルト値で補完
- Mermaid ダイアグラムが不要な記事の場合 → ダイアグラムを含めない
- 指定されたディレクトリやプロジェクトが存在しない場合 → ユーザーに正しいパスを尋ねる
- 複数の入力形式が混在する場合（トピック + プロジェクト名 + 詳細指定）→ 全ての入力を統合して処理する

---

## Requirements *(mandatory)*

### Functional Requirements

**オーケストレーター**

- **FR-001**: システムは VS Code Copilot エージェント（`.github/agents/`）として構築され、各サブエージェントを呼び出してフローを実行する
- **FR-002**: システムはトピック入力（必須）と補足情報（プロジェクト名、ディレクトリパス、詳細な内容指定）を受け取り、リサーチ→執筆→品質チェック→SEO→修正のフローを自動実行する
- **FR-003**: 各サブエージェントの実行結果は Copilot の会話コンテキストで管理され、次のフェーズに渡される

**リサーチエージェント**

- **FR-004**: エージェントは open_deep_research の API（`http://127.0.0.1:2024`）を活用してトピックリサーチを実行する
- **FR-004a**: エージェントは pytrends を使用してトピックの検索トレンド（Interest Over Time、Related Queries）を確認する。トレンドが低い場合でも記事生成は続行し、トレンドの高い関連トピックをユーザーに提案する
- **FR-005**: エージェントは収集した情報の出典（URL、タイトル）を記録する
- **FR-006**: プロジェクト名、ディレクトリパス、または詳細な内容指定が入力された場合、対象の README・ソースコード・ディレクトリ構成を自動参照して情報を収集する

**執筆エージェント**

- **FR-007**: エージェントは既存ブログのスタイルガイド（トーン、構成、比喩の使い方）に準拠して記事を執筆する
- **FR-008**: エージェントは記事の内容に応じて Mermaid ダイアグラムを自動生成する
- **FR-009**: エージェントは frontmatter（title, description, pubDate, tags, draft, enableComments）を正しく生成する
- **FR-010**: エージェントは「この記事を読んでほしい人」セクションと目次を含める

**品質チェックエージェント**

- **FR-011**: エージェントは blog-reviewer を活用して事実確認を実行する
- **FR-012**: エージェントは markdownlint を使用して Markdown フォーマットを検証する
- **FR-013**: エージェントはカスタム Python モジュール（`seo_checker.py`）で Markdown ベースの SEO メタ情報を検証する（title 長さ、description 長さ、見出し構造、alt テキスト）。frontmatter の正当性と Markdown 構造の基本チェックを担当
- **FR-013a**: エージェントは searchstack-aeo の無料コマンド（`meta`, `schema`, `links`, `onpage`）で技術 SEO 検証を実行する。OG タグ、構造化データ、内部リンク、オンページ SEO の包括チェックを担当
- **FR-013b**: デプロイ後（Astro ビルド後）にも searchstack-aeo を実行し、URL ベースで包括的な技術 SEO チェックを実行する
- **FR-014**: エージェントは website-seo-audit を使用してデプロイ後の包括的 SEO チェックを実行する

> **Scope Note**: FR-013b と FR-014 はデプロイ後にのみ適用される要件。現在の実装スコープ（記事生成フロー）には含まれず、CI/CD パイプラインや手動ステップとして別途対応する。

**自動修正エージェント**

- **FR-015**: 品質チェックで検出された問題を自動修正する
- **FR-016**: 修正内容は元の記事のトーン・構成を維持する
- **FR-017**: 「要確認」と判定された項目は修正せず残す

**SEO サブシステム**

- **FR-018**: frontmatter の title は 30〜60 文字であることを保証する
- **FR-019**: frontmatter の description は 120〜160 文字であることを保証する
- **FR-020**: 記事には H1 が 1 つだけ存在し、H2→H3 の順序が正しいことを保証する
- **FR-021**: 画像には alt テキストが設定されていることを保証する
- **FR-022**: OG タグ（og:title, og:description, og:image）が正しく生成されることを検証する

**出力**

- **FR-023**: 完成した Markdown ファイルは `DMARU9.github.io/src/content/blog/` に配置される
- **FR-024**: ファイル名はスラッグ形式（`slug-title.md`）で生成される
- **FR-025**: 各段階の実行レポートが標準出力に出力される

### Key Entities

- **BlogPost**: ブログ記事の本文データ（Markdown + frontmatter）
- **ResearchResult**: リサーチ結果（出典、要約、信頼度、プロジェクト/ディレクトリ情報）
- **TrendResult**: トレンド分析結果（検索トレンド、関連クエリ、関連トピック提案）
- **QualityReport**: 品質チェック結果（問題リスト、修正内容、スコア）
- **SEOReport**: SEO チェック結果（各指標の値、推奨事項、修正内容）
- **StyleGuide**: ブログのスタイルガイド（トーン、構成ルール、フォーマット規則）

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: トピック入力から完成記事までが 10 分以内に完了する
- **SC-002**: 生成された記事の frontmatter スキーマ検証が 100% 通過する
- **SC-003**: Markdown フォーマットのエラーが 0 件である（警告は許容）
- **SC-004**: 事実確認で「誤り」と判定された項目が 0 件である（修正後）
- **SC-005**: SEO スコアが 80 点以上（100 点満点）である（Markdown ベース + URL ベースの両方で検証）
- **SC-006**: 生成された記事が Astro の `content.config.ts` スキーマに適合する
- **SC-007**: 記事には Mermaid ダイアグラムが最低 1 つ含まれる（可能な場合）

---

## Assumptions

- open_deep_research の LangGraph サーバーが `http://127.0.0.1:2024` で稼働している
- blog-reviewer エージェントが正常に動作する
- DMARU9.github.io の Astro ビルド環境が整っている
- markdownlint は npm でインストール可能
- website-seo-audit は pip でインストール可能（`pip install website-seo-audit`）
- pytrends は pip でインストール可能（`pip install pytrends`）、API キー不要
- searchstack-aeo は pip でインストール可能（`pip install searchstack`）、無料コマンドは API キー不要。記事生成後（Markdown ベース）とデプロイ後（URL ベース）の両方で実行する
- 記事のトーンは「です・ます」調、親しみやすい文体
- メンテナンス頻度は月 1 回程度（スタイルガイドの更新）

---

## Technology Constraints

- **Language**: Python 3.11+（BLOG-TOOLS Constitution 準拠）
- **Framework**: VS Code Copilot エージェント（`.github/agents/`）、Python ツールアプリ
- **Build Tool**: uv（BLOG-TOOLS Constitution 準拠）
- **Linting**: ruff, mypy（BLOG-TOOLS Constitution 準拠）
- **Testing**: pytest（BLOG-TOOLS Constitution 準拠）
- **External Tools**: open_deep_research, blog-reviewer, markdownlint, website-seo-audit, pytrends, searchstack-aeo
- **Target**: DMARU9.github.io (Astro ベース静的サイト)
