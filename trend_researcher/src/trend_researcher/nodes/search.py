"""search ノード（FR-003/FR-004/FR-005 対応、X / YouTube 共通）。"""

from __future__ import annotations

from trend_researcher.progress import NODE_SEARCH, make_emitter
from trend_researcher.state import State


def search_node(state: State) -> State:
    """provider.search を呼び出し、上位 N 件の候補を選定する。"""
    emitter = make_emitter()
    emitter.emit(3, NODE_SEARCH, "開始")

    provider = state["provider"]
    instruction = state["instruction"]
    queries = state.get("search_queries") or []
    config = state.get("config")
    max_results = instruction.max_results or 5

    candidates = provider.search(
        queries=queries,
        max_results=max_results,
        published_after=instruction.published_after,
        sort_by=instruction.sort_by or "relevance",
        config=config,
    )

    emitter.emit(3, NODE_SEARCH, "完了", detail=f"{len(candidates)} 件を選定")
    return {"candidates": candidates, "published_after": instruction.published_after}
