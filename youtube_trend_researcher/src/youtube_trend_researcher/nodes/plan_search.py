"""plan_search ノード（FR-003 対応、単一クエリ生成）。"""

from __future__ import annotations

import re

from youtube_trend_researcher.progress import NODE_PLAN_SEARCH, make_emitter
from youtube_trend_researcher.prompts import PLAN_SEARCH_PROMPT
from youtube_trend_researcher.state import State
from youtube_trend_researcher.tools.llm import build_model

# クエリから除去する期間表現（「2024」等の西暦や「半年以内」等）
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_PERIOD_RE = re.compile(r"(半年|三?ヶ?月|1?年|本年|今年|最近|以内|以降|から|より)\s*")


def _clean_query(query: str) -> str:
    """生成クエリから年号・期間表現を除去し、広く検索できるようにする。"""
    q = _YEAR_RE.sub("", query)
    q = _PERIOD_RE.sub("", q)
    q = re.sub(r"\s{2,}", " ", q).strip().strip('"').strip("'")
    return q


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

    # 期間表現を topic から除去して検索主題のみを渡す（重複除去も兼ねる）
    search_topic = re.sub(r"[（(].*?[）)]", "", instruction.topic or instruction.raw_text)
    search_topic = _PERIOD_RE.sub("", search_topic).strip() or (instruction.topic or instruction.raw_text)

    # 日付フィルタがある場合は、LLM にその旨を伝えて広く検索させる
    published_after = instruction.published_after
    if published_after is not None:
        date_hint = (
            f"\n※投稿日フィルタ（{published_after.date()} 以降）が別途適用されます。"
            "そのため、古い年号を付けずに最新の動画も含めて広く検索してください。"
        )
    else:
        date_hint = ""

    model = build_model("research")
    prompt = PLAN_SEARCH_PROMPT.format(topic=search_topic, date_hint=date_hint)
    result = model.invoke(prompt)
    query = result.content if hasattr(result, "content") else str(result)
    query = _clean_query(query)

    emitter.emit(2, NODE_PLAN_SEARCH, "完了", detail=f'クエリ: "{query}"')
    return {"search_query": query}
