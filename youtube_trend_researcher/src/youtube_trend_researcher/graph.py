"""LangGraph グラフ構築と実行エントリ（FR-001/SC-005 対応）。"""

from __future__ import annotations

import asyncio
import signal
from datetime import datetime, timedelta
from typing import Any

from langgraph.graph import END, StateGraph

from youtube_trend_researcher.models import OutputFormat, ResearchInstruction, ResearchReport
from youtube_trend_researcher.nodes.compile_report import compile_report, render_json, render_markdown
from youtube_trend_researcher.nodes.analyze_content import analyze_content
from youtube_trend_researcher.nodes.extract_common import extract_common
from youtube_trend_researcher.nodes.fetch_transcripts import fetch_transcripts
from youtube_trend_researcher.nodes.parse_instruction import parse_instruction
from youtube_trend_researcher.nodes.plan_search import plan_search
from youtube_trend_researcher.nodes.search_videos import search_videos_node
from youtube_trend_researcher.state import State

# 全体実行時間上限（100 分、SC-005 / Clarification）
EXECUTION_TIMEOUT = timedelta(minutes=100)


def build_graph() -> Any:
    """単一検索の StateGraph を構築する。"""
    graph = StateGraph(State)
    graph.add_node("parse_instruction", parse_instruction)
    graph.add_node("plan_search", plan_search)
    graph.add_node("search_videos", search_videos_node)
    graph.add_node("fetch_transcripts", fetch_transcripts)
    graph.add_node("analyze_content", analyze_content)
    graph.add_node("extract_common", extract_common)
    graph.add_node("compile_report", compile_report)

    graph.set_entry_point("parse_instruction")
    graph.add_edge("parse_instruction", "plan_search")
    graph.add_edge("plan_search", "search_videos")
    graph.add_edge("search_videos", "fetch_transcripts")
    graph.add_edge("fetch_transcripts", "analyze_content")
    graph.add_edge("analyze_content", "extract_common")
    graph.add_edge("extract_common", "compile_report")
    graph.add_edge("compile_report", END)

    return graph.compile()


def _build_partial_report(instruction: ResearchInstruction, state: State) -> ResearchReport:
    """タイムアウト時などの途中結果から部分的なレポートを構築（SC-005）。"""
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
    max_results: int | None = None,
    transcript_language: str = "ja",
    output_format: OutputFormat = OutputFormat.MARKDOWN,
) -> ResearchReport:
    """自然言語指示から自律的にリサーチを実行し、ResearchReport を返す。

    Args:
        instruction_text: 自然言語のリサーチ指示。
        max_results: 件数上書き（任意）。
        transcript_language: 字幕優先言語。
        output_format: 出力形式（markdown/json）。

    Returns:
        完成（またはタイムアウト時は部分的な）ResearchReport。
    """
    compiled = build_graph()
    instruction = ResearchInstruction(raw_text=instruction_text)
    if max_results is not None:
        instruction.max_results = max_results
    instruction.output.format = output_format

    initial_state: State = {
        "instruction_raw": instruction_text,
        "instruction": instruction,
        "transcript_language": transcript_language,
    }

    # SIGALRM による全体時間監視（Linux のみ）
    timeouted = False
    old_handler = None
    try:
        if hasattr(signal, "SIGALRM"):
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(int(EXECUTION_TIMEOUT.total_seconds()))
        final = compiled.invoke(initial_state)
    except _TimeoutError:
        timeouted = True
        final = initial_state  # 最低限 instruction を保持
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
    return render_markdown(report)
