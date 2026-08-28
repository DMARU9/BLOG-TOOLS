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
    assert candidates[0].tweet_id == "1"
    assert candidates[4].tweet_id == "5"
