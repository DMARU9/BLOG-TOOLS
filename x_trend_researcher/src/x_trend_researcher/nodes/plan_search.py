"""plan_search ノード（FR-003 対応、複数クエリ生成）。"""

from __future__ import annotations

import re

from x_trend_researcher.progress import NODE_PLAN_SEARCH, make_emitter
from x_trend_researcher.prompts import PLAN_SEARCH_PROMPT
from x_trend_researcher.state import State
from x_trend_researcher.tools.llm import build_model

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
    """指示から検索クエリを複数生成する（LLM に委ねる）。

    トピックを複数の側面に分解し、側面ごとに 1〜3 個のクエリを生成。
    1 行 1 クエリとして返し、ここでリスト化する。

    Args:
        state: `instruction` を含む State。

    Returns:
        更新された State（search_queries をセット）。
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
            "そのため、古い年号を付けずに最新の投稿も含めて広く検索してください。"
        )
    else:
        date_hint = ""

    model = build_model("research")
    prompt = PLAN_SEARCH_PROMPT.format(topic=search_topic, date_hint=date_hint)
    result = model.invoke(prompt)
    raw = result.content if hasattr(result, "content") else str(result)

    # LLM は 1 行 1 クエリで出力する。空行・番号・記号を除去して複数クエリ化。
    queries: list[str] = []
    for line in raw.splitlines():
        q = _clean_query(line)
        if q:
            queries.append(q)

    emitter.emit(2, NODE_PLAN_SEARCH, "完了", detail=f'クエリ {len(queries)} 件: {", ".join(queries)}')
    return {"search_queries": queries}
