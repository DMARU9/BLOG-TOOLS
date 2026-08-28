"""plan_search ノードの単体テスト（LLM をモック）。"""

from x_trend_researcher.models import ResearchInstruction
from x_trend_researcher.nodes.plan_search import plan_search
from x_trend_researcher.state import State


class _FakeResult:
    def __init__(self, content):
        self.content = content


def _fake_model(prompt_text):
    """PLAN_SEARCH_PROMPT を受け取り、複数行クエリを返すモデルを作る。"""
    class _M:
        def invoke(self, prompt):
            return _FakeResult("オタク 困りごと\n推し活 大変\n同人 在庫")
    return _M()


def test_plan_search_returns_multiple_queries():
    instruction = ResearchInstruction(raw_text="オタクの活動における困りごとを調査したい", topic="オタクの活動における困りごと")
    with __import__("unittest").mock.patch(
        "x_trend_researcher.nodes.plan_search.build_model", return_value=_fake_model(None)
    ):
        state = plan_search({"instruction": instruction})
    queries = state["search_queries"]
    assert isinstance(queries, list)
    assert len(queries) == 3
    assert queries[0] == "オタク 困りごと"
    assert queries[1] == "推し活 大変"
    assert queries[2] == "同人 在庫"


def test_plan_search_cleans_year_and_period():
    """LLM が「2024 〜」等を含めても除去される。"""
    class _M:
        def invoke(self, prompt):
            return _FakeResult("2024 オタク 困りごと\n最近 AI ツール")
    instruction = ResearchInstruction(raw_text="test", topic="test")
    with __import__("unittest").mock.patch(
        "x_trend_researcher.nodes.plan_search.build_model", return_value=_M()
    ):
        state = plan_search({"instruction": instruction})
    queries = state["search_queries"]
    assert "オタク 困りごと" in queries
    assert all("2024" not in q for q in queries)
    assert all("最近" not in q for q in queries)
