"""search_tweets ノード（FR-003/FR-004/FR-005 対応）。"""

from __future__ import annotations

from x_trend_researcher.config import get_config
from x_trend_researcher.progress import NODE_SEARCH_TWEETS, make_emitter
from x_trend_researcher.state import State
from x_trend_researcher.tools.x_search import search_tweets


def search_tweets_node(state: State) -> State:
    """単一検索で関連度順上位 N 件を選定する。

    Args:
        state: `instruction` と `search_query` を含む State。

    Returns:
        更新された State（candidates をセット）。
    """
    emitter = make_emitter()
    emitter.emit(3, NODE_SEARCH_TWEETS, "開始")

    instruction = state["instruction"]
    query = state.get("search_query", "")
    max_results = instruction.max_results or 5

    # X 検索は --since をネイティブサポートするため、クエリに since: を付与する
    if instruction.published_after is not None:
        query = f'{query} since:{instruction.published_after.date().isoformat()}'

    candidates = search_tweets(query, max_results=max_results, accounts_db=str(get_config().accounts_db))

    emitter.emit(3, NODE_SEARCH_TWEETS, "完了", detail=f"{len(candidates)} 件を選定")
    return {"candidates": candidates, "published_after": instruction.published_after}
