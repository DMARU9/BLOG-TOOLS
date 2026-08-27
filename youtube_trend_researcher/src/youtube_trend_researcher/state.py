"""LangGraph State 定義（data-model.md のグラフ遷移に対応）。"""

from __future__ import annotations

from typing import TypedDict

from youtube_trend_researcher.models import (
    AnalysisFinding,
    CommonTheme,
    ResearchInstruction,
    ResearchReport,
    Transcript,
    VideoCandidate,
)


class State(TypedDict, total=False):
    """リサーチ実行中の状態。

    parse_instruction → plan_search → search_videos → fetch_transcripts
    → analyze_content → extract_common → compile_report の各ノード間で受け渡す。
    """

    instruction: ResearchInstruction
    search_query: str
    candidates: list[VideoCandidate]
    transcripts: list[Transcript]
    analyses: list[AnalysisFinding]
    common_themes: list[CommonTheme]
    report: ResearchReport
    notes: list[str]
