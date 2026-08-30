"""nodes/plan_search.py の単体テスト（LLM をモック、X 用複数クエリ）。"""

from trend_researcher.models import ResearchInstruction
from trend_researcher.nodes.plan_search import plan_search
from trend_researcher.providers import get_provider
from trend_researcher.state import AgentState


class _FakeResult:
    def __init__(self, content):
        self.content = content


def _fake_model_multiple():
    class _M:
        def invoke(self, prompt):
            return _FakeResult("オタク 困りごと\n推し活 大変\n同人 在庫")
    return _M()


def _fake_model_with_year():
    class _M:
        def invoke(self, prompt):
            return _FakeResult("2024 オタク 困りごと\n最近 AI ツール")
    return _M()


def test_plan_search_x_returns_multiple_queries():
    provider = get_provider("x")
    instruction = ResearchInstruction(raw_text="オタクの活動における困りごとを調査したい", platform="x", topic="オタクの活動における困りごと")
    state: AgentState = {"provider": provider, "instruction": instruction}
    with __import__("unittest").mock.patch(
        "trend_researcher.nodes.plan_search.build_model", return_value=_fake_model_multiple()
    ):
        out = plan_search(state)
    queries = out["search_queries"]
    assert isinstance(queries, list)
    assert len(queries) == 3
    assert queries[0] == "オタク 困りごと"
    assert queries[1] == "推し活 大変"
    assert queries[2] == "同人 在庫"


def test_plan_search_cleans_year_and_period():
    provider = get_provider("x")
    instruction = ResearchInstruction(raw_text="test", platform="x", topic="test")
    state: AgentState = {"provider": provider, "instruction": instruction}
    with __import__("unittest").mock.patch(
        "trend_researcher.nodes.plan_search.build_model", return_value=_fake_model_with_year()
    ):
        out = plan_search(state)
    queries = out["search_queries"]
    assert "オタク 困りごと" in queries
    assert all("2024" not in q for q in queries)
    assert all("最近" not in q for q in queries)
