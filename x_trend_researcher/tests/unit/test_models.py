"""models.py の単体テスト。"""

from x_trend_researcher.models import (
    AnalysisFinding,
    BlogAngle,
    CommonTheme,
    ResearchInstruction,
    TweetCandidate,
)


def test_tweet_candidate_defaults():
    c = TweetCandidate(tweet_id="1", text="hello")
    assert c.relevance_rank == 0
    assert c.like_count is None
    assert c.url == ""


def test_research_report_serializable():
    inst = ResearchInstruction(raw_text="AI エージェントについて調べたい")
    report = inst.model_copy(deep=True)
    dumped = report.model_dump(mode="json")
    assert dumped["raw_text"] == "AI エージェントについて調べたい"


def test_common_theme_fields():
    t = CommonTheme(theme="abc", supporting_tweet_ids=["1", "2"], example_quotes=["x"])
    assert t.theme == "abc"
    assert t.supporting_tweet_ids == ["1", "2"]
