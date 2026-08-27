"""parse_instruction ノード（FR-001 対応）。"""

from __future__ import annotations

from youtube_trend_researcher.models import OutputFormat, OutputSpec, ResearchInstruction
from youtube_trend_researcher.prompts import PARSE_INSTRUCTION_PROMPT
from youtube_trend_researcher.progress import NODE_PARSE_INSTRUCTION, make_emitter
from youtube_trend_researcher.state import State
from youtube_trend_researcher.tools.llm import build_model
from youtube_trend_researcher.tools.parse import extract_json_block


def parse_instruction(state: State) -> State:
    """自然言語指示から ResearchInstruction を抽出する。

    Args:
        state: 入力に `instruction` の raw_text を含む State（ここでは新規構築用に raw_text を受け取る）。

    Returns:
        更新された State（instruction をセット）。
    """
    emitter = make_emitter()
    emitter.emit(1, NODE_PARSE_INSTRUCTION, "開始")

    raw_text = state.get("instruction_raw", "") if "instruction_raw" in state else ""
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
