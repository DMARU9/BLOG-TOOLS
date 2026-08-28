"""Pydantic エンティティ定義（X 版）。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


class OutputSpec(BaseModel):
    """出力指定。"""

    format: OutputFormat = OutputFormat.MARKDOWN
    table_for: list[str] = Field(default_factory=lambda: ["common_points"])


class ResearchInstruction(BaseModel):
    """ユーザー指示を構造化したもの（parse_instruction で抽出）。"""

    raw_text: str
    topic: str = ""
    max_results: int = 5
    output: OutputSpec = Field(default_factory=OutputSpec)
    published_after: datetime | None = None
    # X 特有: トレンドワード探索モード（--trends で有効化）
    use_trends: bool = False


class TweetCandidate(BaseModel):
    """twscrape 検索から取得したツイート（関連度順上位 N 件）。"""

    tweet_id: str
    text: str = ""
    url: str = ""
    author_handle: str = ""
    author_name: str = ""
    author_followers: int | None = None
    published_at: datetime | None = None
    like_count: int | None = None
    retweet_count: int | None = None
    reply_count: int | None = None
    quote_count: int | None = None
    relevance_rank: int = 0


class TweetContext(BaseModel):
    """ツイート本文＋スレッド展開＋リプライ（字幕取得ノードの代わり）。"""

    tweet_id: str
    text: str = ""
    thread_text: str = ""  # 親ツイートを遡ったスレッド本文（あれば）
    replies: list[str] = Field(default_factory=list)  # 代表リプライ（上位数件）


class BlogAngle(BaseModel):
    """ブログの活用アイデア（切り口 × 読者への価値 × 拾えるキーフレーズ）。"""

    angle: str = ""           # 切り口（記事で扱う角度）
    value: str = ""           # 読者への価値（なぜ書く価値があるか）
    key_phrase: str = ""      # ツイート内の代表的なキーフレーズ（引用）


class AnalysisFinding(BaseModel):
    """個別ツイートのブログ執筆向け要約。"""

    tweet_id: str
    summary: str = ""
    angles: list[BlogAngle] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class CommonTheme(BaseModel):
    """複数ツイート間の共通ネタ。"""

    theme: str = ""
    description: str = ""
    supporting_tweet_ids: list[str] = Field(default_factory=list)
    example_quotes: list[str] = Field(default_factory=list)


class ResearchReport(BaseModel):
    """最終アウトプット。"""

    instruction: ResearchInstruction
    generated_at: datetime = Field(default_factory=datetime.now)
    candidates: list[TweetCandidate] = Field(default_factory=list)
    analyses: list[AnalysisFinding] = Field(default_factory=list)
    common_themes: list[CommonTheme] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
