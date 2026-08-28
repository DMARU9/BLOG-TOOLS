"""twscrape を用いた検索・コンテキスト取得（単一クエリ・関連度順上位 N 件）。

twscrape は非同期 API のため、本モジュールは asyncio でラップする。
アカウント DB（クッキー保存先）は Config.accounts_db を使用。
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from twscrape import API, gather, Tweet

from x_trend_researcher.models import TweetCandidate, TweetContext


def _to_datetime(value: "datetime | None") -> datetime | None:
    """twscrape の datetime を UTC に正規化（naive なら UTC 付与）。"""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _tweet_to_candidate(tweet: Tweet, rank: int) -> TweetCandidate:
    """twscrape の Tweet を TweetCandidate に変換。"""
    url = f"https://x.com/{tweet.user.username}/status/{tweet.id}" if tweet.user else f"https://x.com/i/web/status/{tweet.id}"
    return TweetCandidate(
        tweet_id=str(tweet.id),
        text=(tweet.rawContent or "").strip(),
        url=url,
        author_handle=tweet.user.username if tweet.user else "",
        author_name=tweet.user.displayname if tweet.user else "",
        author_followers=int(tweet.user.followersCount) if tweet.user else None,
        published_at=_to_datetime(tweet.date),
        like_count=int(tweet.likeCount) if tweet.likeCount is not None else None,
        retweet_count=int(tweet.retweetCount) if tweet.retweetCount is not None else None,
        reply_count=int(tweet.replyCount) if tweet.replyCount is not None else None,
        quote_count=int(tweet.quoteCount) if tweet.quoteCount is not None else None,
        relevance_rank=rank,
    )


async def _search_async(query: str, max_results: int, accounts_db: str) -> list[TweetCandidate]:
    """単一検索し、関連度順上位 N 件を TweetCandidate に変換する。"""
    api = API(accounts_db)
    tweets = await gather(api.search(query, limit=max_results))
    candidates: list[TweetCandidate] = []
    for rank, tweet in enumerate(tweets, start=1):
        candidates.append(_tweet_to_candidate(tweet, rank))
        if len(candidates) >= max_results:
            break
    return candidates


def search_tweets(query: str, max_results: int = 5, accounts_db: str = "accounts.db") -> list[TweetCandidate]:
    """同期ラッパ: 単一検索で関連度順上位 N 件を選定する。

    Args:
        query: 検索クエリ（plan_search が生成。X 検索演算子も利用可）。
        max_results: 取得件数（既定 5）。
        accounts_db: twscrape のアカウント DB パス。

    Returns:
        関連度順の TweetCandidate リスト。
    """
    return asyncio.run(_search_async(query, max_results, accounts_db))


async def _fetch_context_async(tweet_id: str, accounts_db: str, max_replies: int = 3) -> TweetContext:
    """指定ツイートのスレッド（親遡り）＋代表リプライを取得する。"""
    api = API(accounts_db)
    ctx = TweetContext(tweet_id=tweet_id)

    # 元ツイートの本文
    try:
        main = await api.tweet_details(int(tweet_id))
        if main is not None:
            ctx.text = (main.rawContent or "").strip()
            # 親ツイート（会話ルート）があればスレッド本文として取り込む
            if getattr(main, "inReplyToTweetId", None):
                try:
                    parent = await api.tweet_details(int(main.inReplyToTweetId))
                    if parent is not None:
                        ctx.thread_text = (parent.rawContent or "").strip()
                except Exception:
                    pass
    except Exception:
        pass

    # 代表リプライ（上位 max_replies 件）
    try:
        replies = await gather(api.tweet_replies(int(tweet_id), limit=max_replies))
        ctx.replies = [(r.rawContent or "").strip() for r in replies if r.rawContent]
    except Exception:
        pass

    return ctx


def fetch_thread(tweet_id: str, accounts_db: str = "accounts.db", max_replies: int = 3) -> TweetContext:
    """同期ラッパ: ツイートのスレッド展開＋リプライを取得する。"""
    return asyncio.run(_fetch_context_async(tweet_id, accounts_db, max_replies))


async def _fetch_threads_async(candidates: list[TweetCandidate], accounts_db: str) -> list[TweetContext]:
    return await asyncio.gather(*[_fetch_context_async(c.tweet_id, accounts_db) for c in candidates])


def fetch_threads(candidates: list[TweetCandidate], accounts_db: str = "accounts.db") -> list[TweetContext]:
    """複数ツイートのスレッド＋リプライを一括取得する。"""
    if not candidates:
        return []
    return asyncio.run(_fetch_threads_async(candidates, accounts_db))
