"""X（Twitter）用 provider。"""

from __future__ import annotations

from datetime import datetime

from trend_researcher.config import Config
from trend_researcher.models import Candidate, Context
from trend_researcher.prompts import (
    X_ANALYZE_CONTENT_PROMPT,
    X_EXTRACT_COMMON_PROMPT,
    X_PARSE_INSTRUCTION_PROMPT,
    X_PLAN_SEARCH_PROMPT,
)
from trend_researcher.tools.x_search import fetch_threads, search_tweets


def _sort_by_likes(candidates: list[Candidate]) -> list[Candidate]:
    """いいね数の多い順に並べ替え、relevance_rank を振り直す。"""
    ordered = sorted(candidates, key=lambda c: (c.like_count or 0), reverse=True)
    for rank, c in enumerate(ordered, start=1):
        c.relevance_rank = rank
    return ordered


class XProvider:
    name = "x"

    def search(
        self,
        queries: list[str],
        max_results: int,
        published_after: datetime | None,
        sort_by: str,
        config: Config,
    ) -> list[Candidate]:
        # X 検索は --since をネイティブサポートするため、各クエリに since: を付与する
        if published_after is not None:
            since = published_after.date().isoformat()
            queries = [f"{q} since:{since}" for q in queries]

        if sort_by == "likes":
            pool_size = max(config.search_pool_size, max_results)
            pool: list[Candidate] = []
            for q in queries:
                pool.extend(search_tweets(q, max_results=pool_size, accounts_db=str(config.accounts_db)))
            ordered = _sort_by_likes(pool)
            candidates = ordered[:max_results]
        else:
            pool: list[Candidate] = []
            for q in queries:
                pool.extend(search_tweets(q, max_results=max_results, accounts_db=str(config.accounts_db)))
            # 重複（id）を除去し、取得順（関連度順）を維持
            seen: set[str] = set()
            ordered = []
            for c in pool:
                if c.id not in seen:
                    seen.add(c.id)
                    ordered.append(c)
            candidates = ordered[:max_results]
        return candidates

    def fetch_contexts(self, candidates: list[Candidate], config: Config) -> tuple[list[Context], list[str]]:
        notes: list[str] = []
        if not candidates:
            return [], notes
        try:
            contexts = fetch_threads(candidates, accounts_db=str(config.accounts_db))
        except Exception as exc:  # noqa: BLE001 - コンテキスト取得失敗は本文のみで解析
            notes.append(f"スレッド取得に失敗しました（本文のみで解析）: {exc}")
            contexts = [Context(id=c.id, text=c.text) for c in candidates]
        return contexts, notes

    def candidate_table_header(self) -> tuple[str, str]:
        return (
            "| # | 本文抜粋 | 投稿者 | いいね | RT | 引用 | URL |",
            "|---|----------|--------|--------|----|------|-----|",
        )

    def render_candidate_row(self, c: Candidate) -> str:
        snippet = (c.text or "").replace("\n", " ")[:50]
        likes = f"{c.like_count:,}" if c.like_count is not None else "-"
        rts = f"{c.retweet_count:,}" if c.retweet_count is not None else "-"
        quotes = f"{c.quote_count:,}" if c.quote_count is not None else "-"
        author = f"@{c.author_handle}" if c.author_handle else c.author_name
        return f"| {c.relevance_rank} | {snippet} | {author} | {likes} | {rts} | {quotes} | {c.url} |"

    def render_block_title(self, c: Candidate) -> str:
        handle = c.author_handle or c.author_name
        return f"### {c.relevance_rank}. @{handle} のツイート"

    def render_block_meta(self, c: Candidate) -> list[str]:
        bits = [f"投稿者: {c.author_name}" if c.author_name else None,
                f"フォロワー: {c.author_followers:,}" if c.author_followers is not None else None,
                f"いいね: {c.like_count:,}" if c.like_count is not None else None,
                f"RT: {c.retweet_count:,}" if c.retweet_count is not None else None,
                f"公開日: {c.published_at.date()}" if c.published_at is not None else None]
        return [b for b in bits if b]

    @property
    def parse_instruction_prompt(self) -> str:
        return X_PARSE_INSTRUCTION_PROMPT

    @property
    def plan_search_prompt(self) -> str:
        return X_PLAN_SEARCH_PROMPT

    @property
    def analyze_content_prompt(self) -> str:
        return X_ANALYZE_CONTENT_PROMPT

    @property
    def extract_common_prompt(self) -> str:
        return X_EXTRACT_COMMON_PROMPT

    @property
    def common_theme_supporting_label(self) -> str:
        return "該当ツイート"
