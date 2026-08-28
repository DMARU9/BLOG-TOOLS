"""LangGraph State 定義（X / YouTube 共通グラフ遷移に対応）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from trend_researcher.models import (
    AnalysisFinding,
    Candidate,
    CommonTheme,
    Context,
    OutputFormat,
    ResearchInstruction,
    ResearchReport,
)
from trend_researcher.providers.base import Provider


class State(TypedDict, total=False):
    """リサーチ実行中の状態。

    parse_instruction → plan_search → search → fetch
    → analyze_content → extract_common → compile_report の各ノード間で受け渡す。
    """

    provider: Provider
    config: Any
    instruction: ResearchInstruction
    instruction_raw: str
    search_query: str
    search_queries: list[str]
    published_after: datetime | None
    max_results: int
    output_format: OutputFormat
    candidates: list[Candidate]
    contexts: list[Context]
    analyses: list[AnalysisFinding]
    common_themes: list[CommonTheme]
    report: ResearchReport
    notes: list[str]
    use_trends: bool
    sort_by: str
    transcript_language: str
    cache_dir: str | None
