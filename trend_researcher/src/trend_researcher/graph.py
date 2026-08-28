"""LangGraph グラフ構築と実行エントリ（FR-001/SC-005 対応、X / YouTube 共通）。"""

from __future__ import annotations

import signal
from datetime import datetime, timedelta
from typing import Any

from langgraph.graph import END, StateGraph

from trend_researcher.config import Config
from trend_researcher.models import OutputFormat, ResearchInstruction, ResearchReport
from trend_researcher.nodes.analyze_content import analyze_content
from trend_researcher.nodes.compile_report import (
    compile_report,
    render_json,
    render_markdown,
)
from trend_researcher.nodes.extract_common import extract_common
from trend_researcher.nodes.fetch import fetch_node
from trend_researcher.nodes.parse_instruction import parse_instruction
from trend_researcher.nodes.plan_search import plan_search
from trend_researcher.nodes.search import search_node
from trend_researcher.providers import get_provider
from trend_researcher.state import State

EXECUTION_TIMEOUT = timedelta(minutes=100)


def build_graph() -> Any:
    """単一検索の StateGraph を構築する（プラットフォーム共通）。"""
    graph = StateGraph(State)
    graph.add_node("parse_instruction", parse_instruction)
    graph.add_node("plan_search", plan_search)
    graph.add_node("search", search_node)
    graph.add_node("fetch", fetch_node)
    graph.add_node("analyze_content", analyze_content)
    graph.add_node("extract_common", extract_common)
    graph.add_node("compile_report", compile_report)

    graph.set_entry_point("parse_instruction")
    graph.add_edge("parse_instruction", "plan_search")
    graph.add_edge("plan_search", "search")
    graph.add_conditional_edges(
        "search",
        _route_after_search,
        {"skip": "compile_report", "continue": "fetch"},
    )
    graph.add_edge("fetch", "analyze_content")
    graph.add_edge("analyze_content", "extract_common")
    graph.add_edge("extract_common", "compile_report")
    graph.add_edge("compile_report", END)

    return graph.compile()


def _route_after_search(state: State) -> str:
    candidates = state.get("candidates", [])
    return "skip" if not candidates else "continue"


def _build_partial_report(instruction: ResearchInstruction, state: dict[str, Any]) -> ResearchReport:
    candidates = state.get("candidates", [])
    return ResearchReport(
        instruction=instruction,
        candidates=candidates,
        analyses=state.get("analyses", []),
        common_themes=state.get("common_themes", []),
        sources=[c.url for c in candidates if c.url],
        notes=list(state.get("notes", [])) + ["全体実行が時間上限に達したため、途中結果を返します。"],
    )


class _TimeoutError(Exception):
    pass


def _timeout_handler(_signum: int, _frame: Any) -> None:
    raise _TimeoutError("execution timeout")


def run(
    instruction_text: str,
    platform: str = "x",
    max_results: int | None = None,
    transcript_language: str = "ja",
    output_format: OutputFormat = OutputFormat.MARKDOWN,
    since: datetime | None = None,
    use_trends: bool = False,
    sort_by: str = "relevance",
    cache_dir: str | None = None,
) -> ResearchReport:
    """自然言語指示から自律的にリサーチを実行し、ResearchReport を返す。

    Args:
        instruction_text: 自然言語のリサーチ指示。
        platform: "x" | "youtube"。
        max_results: 件数上書き（任意）。
        transcript_language: 字幕優先言語（YouTube）。
        output_format: 出力形式（markdown/json）。
        since: 投稿日下限（任意、CLI --since 用）。
        use_trends: トレンドワード探索モード（X）。
        sort_by: 選定基準（X: "relevance"=関連度順 / "likes"=いいね順）。
        cache_dir: 中間成果物の永続化先（任意、FR-012）。

    Returns:
        完成（またはタイムアウト時は部分的な）ResearchReport。
    """
    compiled = build_graph()
    provider = get_provider(platform)
    config = Config.load(platform=platform, cache_dir=cache_dir, max_results=max_results)
    instruction = ResearchInstruction(raw_text=instruction_text, platform=platform)
    if max_results is not None:
        instruction.max_results = max_results
    instruction.output.format = output_format
    if since is not None:
        instruction.published_after = since

    initial_state: State = {
        "provider": provider,
        "config": config,
        "instruction_raw": instruction_text,
        "instruction": instruction,
        "published_after": instruction.published_after,
        "max_results": instruction.max_results,
        "output_format": instruction.output.format,
        "use_trends": use_trends,
        "sort_by": sort_by,
        "transcript_language": transcript_language,
        "cache_dir": cache_dir,
    }

    timeouted = False
    old_handler = None
    try:
        if hasattr(signal, "SIGALRM"):
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(int(EXECUTION_TIMEOUT.total_seconds()))
        final = compiled.invoke(initial_state)
    except _TimeoutError:
        timeouted = True
        final = initial_state
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
            if old_handler is not None:
                signal.signal(signal.SIGALRM, old_handler)

    if timeouted:
        return _build_partial_report(instruction, final if isinstance(final, dict) else dict(final))

    report = final.get("report") if isinstance(final, dict) else None
    if report is None:
        report = _build_partial_report(instruction, final if isinstance(final, dict) else {})
    return report


def render_report(report: ResearchReport) -> str:
    """レポートを指示された形式（既定 markdown）で描画。"""
    fmt = report.instruction.output.format
    if fmt == "json":
        return render_json(report)
    provider = get_provider(report.instruction.platform)
    return render_markdown(report, provider)
