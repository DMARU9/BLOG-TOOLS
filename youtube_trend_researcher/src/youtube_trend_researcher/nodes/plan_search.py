"""plan_search ノード（FR-003 対応、単一クエリ生成）。"""

from __future__ import annotations

from youtube_trend_researcher.progress import NODE_PLAN_SEARCH, make_emitter
from youtube_trend_researcher.prompts import PLAN_SEARCH_PROMPT
from youtube_trend_researcher.state import State
from youtube_trend_researcher.tools.llm import build_model


def plan_search(state: State) -> State:
    """指示から検索クエリを 1 つ生成する（LLM に委ねる）。

    Args:
        state: `instruction` を含む State。

    Returns:
        更新された State（search_query をセット）。
    """
    emitter = make_emitter()
    emitter.emit(2, NODE_PLAN_SEARCH, "開始", detail="LLM が検索クエリを生成中")

    instruction = state["instruction"]
    model = build_model("research")
    prompt = PLAN_SEARCH_PROMPT.format(topic=instruction.topic or instruction.raw_text)
    result = model.invoke(prompt)
    query = result.content if hasattr(result, "content") else str(result)
    query = query.strip().strip('"').strip("'")

    emitter.emit(2, NODE_PLAN_SEARCH, "完了", detail=f'クエリ: "{query}"')
    return {"search_query": query}
