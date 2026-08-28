"""parse_instruction ノード（FR-001 対応）。"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from x_trend_researcher.models import OutputFormat, OutputSpec, ResearchInstruction
from x_trend_researcher.progress import NODE_PARSE_INSTRUCTION, make_emitter
from x_trend_researcher.prompts import PARSE_INSTRUCTION_PROMPT
from x_trend_researcher.state import State
from x_trend_researcher.tools.llm import build_model
from x_trend_researcher.tools.parse import extract_json_block

# 期間ラベル（数字+月以外）を投稿日下限の相対日数に変換するマッピング。
# 「最近」単体は 3 ヶ月程度とみなす。
_RELATIVE_PERIOD_DAYS = {
    "半年": 182,
    "1年": 365,
    "年": 365,
    "本年": 0,   # 当年 1/1 から（下で特別処理）
    "今年": 0,
    "最近": 92,
}


def _extract_published_after_from_text(text: str) -> datetime | None:
    """自然言語から投稿日下限（published_after）を抽出。

    対応: 「半年以内」「3ヶ月以内」「1年以内」「今年/本年」「最近N日」等。
    日付指定「2025-01-01以降」等は parse しない（明示 --since を利用）。
    """
    now = datetime.now(UTC)
    # 相対期間「X以内」（「半年」は年月パターンの一部として誤マッチしないよう先頭へ）
    m = re.search(r"(半年|三ヶ月|3ヶ月|三カ月|3カ月|[0-9０-９]+[ヶカ]?月|1年|年|本年|今年|最近)\s*以内", text)
    if m:
        label = m.group(1)
        return _period_to_date(label, now)
    # 「今年」「本年」は「以内」なしでも期間指定とみなす
    if re.search(r"(今年|本年)", text):
        return datetime(now.year, 1, 1, tzinfo=UTC)
    # 最近N日（「以内」なしでも）
    m = re.search(r"最近\s*([0-9０-９]+)\s*日", text)
    if m:
        return now - timedelta(days=int(m.group(1)))
    return None


def _period_to_date(label: str, now: datetime) -> datetime | None:
    """期間ラベルを投稿日下限の datetime に変換。"""
    # 数字+月 パターン（「3ヶ月」「一月」等）は個別に月数計算
    num_m = re.search(r"([0-9０-９]+)\s*[ヶカ]?\s*月", label)
    if num_m:
        months = int(num_m.group(1))
        # 正確な月数引き算（year/month 演算）
        total_months = now.year * 12 + (now.month - 1) - months
        y = total_months // 12
        mo = total_months % 12 + 1
        return datetime(y, mo, now.day, now.hour, now.minute, now.second, now.microsecond, tzinfo=UTC)
    # 固定ラベルはマッピング表から解決
    if label in _RELATIVE_PERIOD_DAYS:
        days = _RELATIVE_PERIOD_DAYS[label]
        return datetime(now.year, 1, 1, tzinfo=UTC) if days == 0 else now - timedelta(days=days)
    return None


def parse_instruction(state: State) -> State:
    """自然言語指示からトピック・件数・投稿日下限を抽出する。

    Args:
        state: `instruction_raw` を含む State。

    Returns:
        更新された State（instruction をセット）。
    """
    emitter = make_emitter()
    emitter.emit(1, NODE_PARSE_INSTRUCTION, "開始")

    raw = state.get("instruction_raw", "")
    model = build_model("research")
    prompt = PARSE_INSTRUCTION_PROMPT.format(instruction=raw)
    result = model.invoke(prompt)
    text = result.content if hasattr(result, "content") else str(result)
    parsed = extract_json_block(text) or {}

    topic = str(parsed.get("topic", "")).strip() or raw
    max_results = int(parsed.get("max_results", 5) or 5)
    output_format = OutputFormat.JSON if str(parsed.get("output_format", "markdown")).lower() == "json" else OutputFormat.MARKDOWN

    # 明示的な --max-results（state.max_results）があれば LLM の出力より優先
    if state.get("max_results") is not None:
        max_results = int(state["max_results"])

    published_after = _extract_published_after_from_text(raw)
    # 明示的な --since（state.published_after）があれば優先
    if state.get("published_after") is not None:
        published_after = state["published_after"]

    instruction = ResearchInstruction(
        raw_text=raw,
        topic=topic,
        max_results=max_results,
        output=OutputSpec(format=output_format),
        published_after=published_after,
        use_trends=bool(state.get("use_trends", False)),
    )

    emitter.emit(1, NODE_PARSE_INSTRUCTION, "完了", detail=f'トピック: "{topic}" / 件数: {max_results}')
    return {"instruction": instruction}
