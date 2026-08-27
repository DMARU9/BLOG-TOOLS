"""parse_instruction ノード（FR-001 対応）。"""

from __future__ import annotations

import re

from youtube_trend_researcher.models import OutputFormat, OutputSpec, ResearchInstruction
from youtube_trend_researcher.progress import NODE_PARSE_INSTRUCTION, make_emitter
from youtube_trend_researcher.prompts import PARSE_INSTRUCTION_PROMPT
from youtube_trend_researcher.state import State
from youtube_trend_researcher.tools.llm import build_model
from youtube_trend_researcher.tools.parse import extract_json_block


def _extract_count_from_text(text: str) -> int | None:
    """自然言語から件数を抽出（「10個」「5件」「３つ」等）。

    Args:
        text: ユーザー指示。

    Returns:
        抽出した件数、または None（指定なし）。
    """
    # 全角数字・漢数字への対応（簡易）
    kanji = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    # まずアラビア数字 + 単位（個/件/本/つ/つ）を探す
    m = re.search(r"(\d+)\s*(?:個|件|本|つ|カ国|か国|社|人)?", text)
    if m:
        return int(m.group(1))
    # 漢数字（単一）
    for k, v in kanji.items():
        if re.search(rf"{k}\s*(?:個|件|本|つ|カ国|か国|社|人)", text):
            return v
    return None


def parse_instruction(state: State) -> State:
    """自然言語指示から ResearchInstruction を抽出する。

    Args:
        state: 入力に `instruction` の raw_text を含む State（ここでは新規構築用に raw_text を受け取る）。

    Returns:
        更新された State（instruction をセット）。
    """
    emitter = make_emitter()
    emitter.emit(1, NODE_PARSE_INSTRUCTION, "開始")

    raw_text = str(state.get("instruction_raw", "") or "")
    if isinstance(state.get("instruction"), ResearchInstruction):
        # すでに構造化済みならそのまま通す
        emitter.emit(1, NODE_PARSE_INSTRUCTION, "完了")
        return state

    model = build_model("research")
    prompt = PARSE_INSTRUCTION_PROMPT.format(instruction=raw_text)
    result = model.invoke(prompt)
    text = result.content if hasattr(result, "content") else str(result)

    parsed = extract_json_block(text) or {}
    topic = str(parsed.get("topic", "")) or raw_text
    # 自然言語の件数表記を優先（FR-005/SC-003）。LLM 出力は補助。
    nl_count = _extract_count_from_text(raw_text)
    if nl_count is not None:
        max_results = nl_count
    else:
        max_results = int(parsed.get("max_results", 5) or 5)
    fmt = str(parsed.get("output_format", "markdown")).lower()
    output_format = OutputFormat.JSON if fmt == "json" else OutputFormat.MARKDOWN

    instruction = ResearchInstruction(
        raw_text=raw_text,
        topic=topic,
        max_results=max_results,
        output=OutputSpec(format=output_format),
    )

    emitter.emit(1, NODE_PARSE_INSTRUCTION, "完了", detail=f"topic: {topic}, max_results: {max_results}")
    return {"instruction": instruction}
