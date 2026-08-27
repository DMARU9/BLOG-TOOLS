"""quickstart.md シナリオ A/B/C の統合テスト（ネットワーク・LLM はモック）。

実環境では yt-dlp / LLM へ接続するが、CI やオフライン検証のため
ツール層をモックし、グラフ全体の流れ（parse→plan→search→fetch→analyze→extract→compile）
が期待通りのレポートを产出することを確認する。
"""

from unittest import mock

import pytest

from youtube_trend_researcher.graph import render_report, run
from youtube_trend_researcher.models import (
    AnalysisFinding,
    OutputFormat,
    ResearchReport,
    Transcript,
    TranscriptSource,
    VideoCandidate,
)


def _fake_candidates(n: int) -> list[VideoCandidate]:
    return [
        VideoCandidate(
            video_id=f"v{i}",
            title=f"タイトル{i}",
            url=f"https://www.youtube.com/watch?v=v{i}",
            channel_title=f"チャンネル{i}",
            view_count=1000 * i,
            relevance_rank=i,
        )
        for i in range(1, n + 1)
    ]


def _fake_transcripts(cands: list[VideoCandidate]) -> list[Transcript]:
    return [
        Transcript(video_id=c.video_id, language="ja", text=f"{c.title} の字幕テキスト", source=TranscriptSource.CAPTION)
        for c in cands
    ]


def _fake_analysis(cands: list[VideoCandidate]) -> list[AnalysisFinding]:
    return [
        AnalysisFinding(
            video_id=c.video_id,
            summary=f"{c.title} の要約",
            key_points=["ポイントA", "ポイントB"],
            evidence=["根拠1"],
        )
        for c in cands
    ]


class _FakeModel:
    """LLM の呼び出しをシミュレーション。役割ごとに簡易レスポンスを返す。"""

    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, prompt: str):
        class _R:
            def __init__(self, content):
                self.content = content

        if "検索クエリ" in prompt:
            return _R("Claude Code 会社運用 解説")
        if "要約" in prompt or "ブログ" in prompt:
            return _R(
                "## 要約\n要約です\n\n## ブログで取り上げられそうなポイント\n- ポイントA\n- ポイントB\n\n## 根拠\n- 根拠1"
            )
        if "共通" in prompt:
            return _R(
                "## 共通テーマ\n### 自動化\n- 説明: 両方で語られている\n- 該当動画: 全動画\n- 代表抜粋: 抜粋"
            )
        return _R("{}")


@pytest.fixture
def patched_pipeline():
    with mock.patch(
        "youtube_trend_researcher.nodes.parse_instruction.build_model",
        side_effect=_FakeModel,
    ), mock.patch(
        "youtube_trend_researcher.nodes.plan_search.build_model",
        side_effect=_FakeModel,
    ), mock.patch(
        "youtube_trend_researcher.nodes.analyze_content.build_model",
        side_effect=_FakeModel,
    ), mock.patch(
        "youtube_trend_researcher.nodes.extract_common.build_model",
        side_effect=_FakeModel,
    ), mock.patch(
        "youtube_trend_researcher.nodes.search_videos.search_videos",
        side_effect=lambda q, max_results=5: _fake_candidates(max_results),
    ), mock.patch(
        "youtube_trend_researcher.nodes.fetch_transcripts.fetch_transcript",
        side_effect=lambda vid, language="ja": Transcript(
            video_id=vid, language=language, text="字幕テキスト", source=TranscriptSource.CAPTION
        ),
    ):
        yield


# --- Scenario A: 既定 5 件・Markdown ---
def test_scenario_a_default_markdown(patched_pipeline):
    report = run("Claude Code で会社を回す方法を解説している動画を参考にブログを書きたい")
    assert isinstance(report, ResearchReport)
    assert len(report.candidates) == 5  # SC-003 既定 5 件
    assert len(report.analyses) == 5
    assert report.candidates[0].relevance_rank == 1
    # SC-002: タイトル・URL・チャンネル・統計が明示
    assert report.candidates[0].title
    assert report.candidates[0].url
    assert report.candidates[0].channel_title
    assert report.candidates[0].view_count is not None
    # 既定は markdown
    assert report.instruction.output.format == OutputFormat.MARKDOWN
    md = render_report(report)
    assert "選定動画リスト" in md
    assert "共通ネタ" in md


# --- Scenario B: 件数指定 10 件・JSON ---
def test_scenario_b_max_results_json(patched_pipeline):
    report = run(
        "機械学習チュートリアルを参考にブログを書きたい",
        max_results=10,
        output_format=OutputFormat.JSON,
    )
    assert len(report.candidates) == 10  # SC-003 指定反映
    assert report.instruction.output.format == OutputFormat.JSON
    rendered = render_report(report)
    # JSON としてパース可能
    import json

    data = json.loads(rendered)
    assert data["candidates"][0]["video_id"] == "v1"
    assert len(data["candidates"]) == 10


# --- Scenario C: 字幕取得の確認 ---
def test_scenario_c_transcript_retrieval(patched_pipeline):
    report = run("字幕取得のテスト")
    # fetch_transcript が呼ばれ、Transcript が生成されていることの間接確認
    assert len(report.candidates) == 5
    # notes に字幕取得不可の記録がない（全件 caption 取得想定）
    assert not any("字幕取得不可" in n for n in report.notes)
