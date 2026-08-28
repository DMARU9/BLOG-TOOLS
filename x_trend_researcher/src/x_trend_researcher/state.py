"""LangGraph State 定義（X 版グラフ遷移に対応）。"""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from x_trend_researcher.models import (
    AnalysisFinding,
    CommonTheme,
    OutputFormat,
    ResearchInstruction,
    ResearchReport,
    TweetCandidate,
    TweetContext,
)


class State(TypedDict, total=False):
    """リサーチ実行中の状態。

    parse_instruction → plan_search → search_tweets → fetch_threads
    → analyze_content → extract_common → compile_report の各ノード間で受け渡す。
    """

    instruction: ResearchInstruction
    instruction_raw: str
    search_query: str
    published_after: datetime | None
    max_results: int
    output_format: OutputFormat
    candidates: list[TweetCandidate]
    contexts: list[TweetContext]
    analyses: list[AnalysisFinding]
    common_themes: list[CommonTheme]
    report: ResearchReport
    notes: list[str]
    use_trends: bool
    cache_dir: str | None
