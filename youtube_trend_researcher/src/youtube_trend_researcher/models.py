"""Pydantic エンティティ定義（FR-005/FR-006/FR-007/FR-008/FR-009 等に対応）。"""

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


class VideoCandidate(BaseModel):
    """yt-dlp 検索から取得した動画（関連度順上位 N 件）。"""

    video_id: str
    title: str = ""
    url: str = ""
    channel_id: str = ""
    channel_title: str = ""
    published_at: datetime | None = None
    view_count: int | None = None
    like_count: int | None = None
    relevance_rank: int = 0


class TranscriptSource(str, Enum):
    CAPTION = "caption"
    AUTOMATIC_CAPTION = "automatic_caption"


class Transcript(BaseModel):
    """字幕（Whisper なし、yt-dlp のみ）。"""

    video_id: str
    language: str = "ja"
    text: str = ""
    source: TranscriptSource = TranscriptSource.AUTOMATIC_CAPTION


class AnalysisFinding(BaseModel):
    """個別動画のブログ執筆向け要約。"""

    video_id: str
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class CommonTheme(BaseModel):
    """複数動画間の共通ネタ。"""

    theme: str = ""
    description: str = ""
    supporting_video_ids: list[str] = Field(default_factory=list)
    example_quotes: list[str] = Field(default_factory=list)


class ResearchReport(BaseModel):
    """最終アウトプット。"""

    instruction: ResearchInstruction
    generated_at: datetime = Field(default_factory=datetime.now)
    candidates: list[VideoCandidate] = Field(default_factory=list)
    analyses: list[AnalysisFinding] = Field(default_factory=list)
    common_themes: list[CommonTheme] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
