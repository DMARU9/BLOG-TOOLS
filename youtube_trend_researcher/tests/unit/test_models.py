"""models.py の単体テスト。"""


from youtube_trend_researcher.models import (
    AnalysisFinding,
    CommonTheme,
    OutputFormat,
    ResearchInstruction,
    ResearchReport,
    Transcript,
    TranscriptSource,
    VideoCandidate,
)


def test_research_instruction_defaults():
    inst = ResearchInstruction(raw_text="テスト指示")
    assert inst.max_results == 5
    assert inst.output.format == OutputFormat.MARKDOWN
    assert inst.topic == ""


def test_video_candidate_defaults():
    c = VideoCandidate(video_id="abc123")
    assert c.url == ""
    assert c.relevance_rank == 0
    assert c.view_count is None


def test_transcript_source_enum():
    t = Transcript(video_id="x", source=TranscriptSource.CAPTION)
    assert t.source == "caption"


def test_report_sources_invariant():
    cands = [
        VideoCandidate(video_id="a", url="https://www.youtube.com/watch?v=a"),
        VideoCandidate(video_id="b", url="https://www.youtube.com/watch?v=b"),
    ]
    report = ResearchReport(
        instruction=ResearchInstruction(raw_text="x"),
        candidates=cands,
        analyses=[AnalysisFinding(video_id="a")],
        common_themes=[CommonTheme(theme="t", supporting_video_ids=["a", "b"])],
        sources=[c.url for c in cands],
    )
    # sources は candidates の url を全件含む（report-schema.md 不変条件）
    assert set(report.sources) == {c.url for c in cands}
