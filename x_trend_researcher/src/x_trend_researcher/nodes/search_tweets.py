"""search_tweets ノード（FR-003/FR-004/FR-005 対応）。"""

from __future__ import annotations

from x_trend_researcher.config import get_config
from x_trend_researcher.models import TweetCandidate
from x_trend_researcher.progress import NODE_SEARCH_TWEETS, make_emitter
from x_trend_researcher.state import State
from x_trend_researcher.tools.x_search import search_tweets


def _sort_by_likes(candidates: list[TweetCandidate]) -> list[TweetCandidate]:
    """いいね数の多い順に並べ替え、relevance_rank を振り直す。

    いいね数が None の場合は 0 として扱う。同順位は取得順（安定ソート）を維持。
    """
    ordered = sorted(candidates, key=lambda c: (c.like_count or 0), reverse=True)
    for rank, c in enumerate(ordered, start=1):
        c.relevance_rank = rank
    return ordered


def search_tweets_node(state: State) -> State:
    """単一検索でより多くの候補を取得し、いいね数順に並べ替えて上位 N 件を採用する。

    X の検索は関連度順に返してくるが、いいね数が分からないため、まずは
    `--max-results` より大きなプール（Config.search_pool_size と max_results の
    大きい方）で取得し、いいね数の多い順にソートしてから上位 N 件を採用する。

    Args:
        state: `instruction` と `search_query` を含む State。

    Returns:
        更新された State（candidates をセット）。
    """
    emitter = make_emitter()
    emitter.emit(3, NODE_SEARCH_TWEETS, "開始")

    instruction = state["instruction"]
    queries = state.get("search_queries") or []
    # 後方互換: 単一 search_query のみの場合
    if not queries and state.get("search_query"):
        queries = [state["search_query"]]
    max_results = instruction.max_results or 5
    sort_by = instruction.sort_by or "relevance"

    # X 検索は --since をネイティブサポートするため、各クエリに since: を付与する
    if instruction.published_after is not None:
        since = instruction.published_after.date().isoformat()
        queries = [f"{q} since:{since}" for q in queries]

    # 関連度順（既定）の場合は各クエリから max_results 件ずつ取得してマージし、
    # 重複を除いて上位 max_results 件を採用する（いいね数順にソートしない）。
    # いいね順（--sort likes）の場合は、より大きなプールからいいね順にソートして採用。
    config = get_config()

    if sort_by == "likes":
        pool_size = max(config.search_pool_size, max_results)
        emitter.emit(3, NODE_SEARCH_TWEETS, "取得中", detail=f"プール {pool_size} 件で検索（いいね順）")
        pool: list[TweetCandidate] = []
        for q in queries:
            pool.extend(search_tweets(q, max_results=pool_size, accounts_db=str(config.accounts_db)))
        ordered = _sort_by_likes(pool)
        candidates = ordered[:max_results]
        emitter.emit(3, NODE_SEARCH_TWEETS, "完了", detail=f"{len(pool)} 件取得 → いいね順上位 {len(candidates)} 件を選定")
    else:
        emitter.emit(3, NODE_SEARCH_TWEETS, "取得中", detail=f"クエリ {len(queries)} 件・関連度順で検索")
        pool = []
        for q in queries:
            pool.extend(search_tweets(q, max_results=max_results, accounts_db=str(config.accounts_db)))
        # 重複（tweet_id）を除去し、取得順（関連度順）を維持
        seen: set[str] = set()
        ordered = []
        for c in pool:
            if c.tweet_id not in seen:
                seen.add(c.tweet_id)
                ordered.append(c)
        candidates = ordered[:max_results]
        emitter.emit(3, NODE_SEARCH_TWEETS, "完了", detail=f"{len(pool)} 件取得（重複除 {len(ordered)} 件）→ 関連度順上位 {len(candidates)} 件を選定")

    return {"candidates": candidates, "published_after": instruction.published_after}
