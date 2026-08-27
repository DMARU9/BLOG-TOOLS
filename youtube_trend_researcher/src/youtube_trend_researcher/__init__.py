"""YouTube Trend Researcher - 自然言語指示から自律的にリサーチレポートを生成するツール."""

from youtube_trend_researcher.graph import render_report, run
from youtube_trend_researcher.models import (
    AnalysisFinding,
    BlogAngle,
    CommonTheme,
    OutputFormat,
    OutputSpec,
    ResearchInstruction,
    ResearchReport,
    Transcript,
    TranscriptSource,
    VideoCandidate,
)

__all__ = [
    "AnalysisFinding",
    "BlogAngle",
    "CommonTheme",
    "OutputFormat",
    "OutputSpec",
    "ResearchInstruction",
    "ResearchReport",
    "Transcript",
    "TranscriptSource",
    "VideoCandidate",
    "render_report",
    "run",
]


def research(
    instruction: str,
    max_results: int | None = None,
    lang: str = "ja",
    output_format: OutputFormat = OutputFormat.MARKDOWN,
) -> ResearchReport:
    """指示から自律リサーチを実行し、ResearchReport を返す（US1 MVP エントリ）。"""
    return run(
        instruction,
        max_results=max_results,
        transcript_language=lang,
        output_format=output_format,
    )
