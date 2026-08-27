"""search_videos ノード（FR-003/FR-004/FR-005 対応）。"""

from __future__ import annotations

from youtube_trend_researcher.progress import NODE_SEARCH_VIDEOS, make_emitter
from youtube_trend_researcher.state import State
from youtube_trend_researcher.tools.youtube_search import search_videos


def search_videos_node(state: State) -> State:
    """単一検索で関連度順上位 N 件を選定する。

    Args:
        state: `instruction` と `search_query` を含む State。

    Returns:
        更新された State（candidates をセット）。
    """
    emitter = make_emitter()
    emitter.emit(3, NODE_SEARCH_VIDEOS, "開始")

    instruction = state["instruction"]
    query = state.get("search_query", "")
    max_results = instruction.max_results or 5
    published_after = instruction.published_after

    candidates = search_videos(query, max_results=max_results, published_after=published_after)

    emitter.emit(3, NODE_SEARCH_VIDEOS, "完了", detail=f"{len(candidates)} 件を選定")
    return {"candidates": candidates, "published_after": published_after}
