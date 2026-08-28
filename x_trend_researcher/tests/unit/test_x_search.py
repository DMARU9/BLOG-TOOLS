"""tools/x_search.py の単体テスト（twscrape をモック）。"""

from datetime import datetime, timezone
from unittest import mock

from twscrape import Tweet, User

from x_trend_researcher.tools.x_search import _tweet_to_candidate, search_tweets


def _fake_tweet(tid: int) -> Tweet:
    user = User(
        id=tid * 10,
        username=f"user{tid}",
        displayname=f"User {tid}",
        followersCount=100 + tid,
        friendsCount=10,
        statusesCount=5,
        rawDescription="",
        id_str=str(tid * 10),
        url=f"https://x.com/user{tid}",
        favouritesCount=0,
        listedCount=0,
        mediaCount=0,
        location="",
        profileImageUrl="",
        profileBannerUrl="",
        verified=False,
        created=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    return Tweet(
        id=tid,
        id_str=str(tid),
        url=f"https://x.com/user{tid}/status/{tid}",
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        rawContent=f"ツイート本文 {tid}",
        lang="ja",
        conversationId=tid,
        conversationIdStr=str(tid),
        cashtags=[],
        likeCount=tid * 3,
        retweetCount=tid * 2,
        replyCount=tid,
        quoteCount=tid,
        isQuoteStatus=False,
        retweetedTweet=None,
        quotedTweet=None,
        mentionedUsers=[],
        hashtags=[],
        links=[],
        media=[],
        viewCount=None,
        bookmarkedCount=None,
        user=user,
        source=None,
        inReplyToTweetId=None,
    )


def test_tweet_to_candidate_mapping():
    t = _fake_tweet(42)
    c = _tweet_to_candidate(t, rank=1)
    assert c.tweet_id == "42"
    assert c.author_handle == "user42"
    assert c.like_count == 126
    assert c.retweet_count == 84
    assert c.relevance_rank == 1


def test_search_tweets_top_n():
    tweets = [_fake_tweet(i) for i in range(1, 8)]

    class _FakeAPI:
        def __init__(self, db):
            pass

        async def search(self, query, limit=5):
            for t in tweets[:limit]:
                yield t

    async def _fake_gather(gen):
        out = []
        async for x in gen:
            out.append(x)
        return out

    with mock.patch("x_trend_researcher.tools.x_search.API", _FakeAPI), \
         mock.patch("x_trend_researcher.tools.x_search.gather", _fake_gather):
        candidates = search_tweets("test", max_results=5)
    assert len(candidates) == 5


def test_sort_by_likes_orders_descending_and_renumbers():
    from x_trend_researcher.models import TweetCandidate
    from x_trend_researcher.nodes.search_tweets import _sort_by_likes

    cands = [
        TweetCandidate(tweet_id="a", like_count=10, relevance_rank=1),
        TweetCandidate(tweet_id="b", like_count=300, relevance_rank=2),
        TweetCandidate(tweet_id="c", like_count=50, relevance_rank=3),
        TweetCandidate(tweet_id="d", like_count=None, relevance_rank=4),
    ]
    ordered = _sort_by_likes(cands)
    assert [c.tweet_id for c in ordered] == ["b", "c", "a", "d"]
    assert [c.relevance_rank for c in ordered] == [1, 2, 3, 4]
    # None は 0 として扱われ、末尾に回る
    assert ordered[-1].like_count is None


def test_sort_by_likes_takes_top_n():
    from x_trend_researcher.models import TweetCandidate
    from x_trend_researcher.nodes.search_tweets import search_tweets_node
    from x_trend_researcher.models import ResearchInstruction

    pool = [
        TweetCandidate(tweet_id=f"t{i}", like_count=i * 5, relevance_rank=i)
        for i in range(1, 61)  # 60 件のプール
    ]

    def _fake_search(query, max_results=50, accounts_db="accounts.db"):
        return pool[:max_results]

    with mock.patch("x_trend_researcher.nodes.search_tweets.search_tweets", _fake_search), \
         mock.patch("x_trend_researcher.nodes.search_tweets.get_config") as cfg:
        cfg.return_value.search_pool_size = 50
        instruction = ResearchInstruction(raw_text="test", topic="test", max_results=10)
        state = search_tweets_node({"instruction": instruction, "search_query": "python"})

    cands = state["candidates"]
    assert len(cands) == 10
    likes = [c.like_count for c in cands]
    assert likes == sorted(likes, reverse=True)  # いいね順
    assert likes[0] == 250  # 取得プール最大の 50*5=250
    assert likes[-1] == 205  # 11 番目に大きい 41*5=205
