"""parse_instruction ノード（FR-001 対応）。X / YouTube 共通。"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from trend_researcher.models import OutputFormat, OutputSpec, ResearchInstruction
from trend_researcher.progress import NODE_PARSE_INSTRUCTION, make_emitter
from trend_researcher.state import State
from trend_researcher.tools.llm import build_model
from trend_researcher.tools.parse import extract_json_block

# 期間ラベル（数字+月以外）を投稿日下限の相対日数に変換するマッピング。
_RELATIVE_PERIOD_DAYS = {
    "半年": 182,
    "1年": 365,
    "年": 365,
    "本年": 0,
    "今年": 0,
    "最近": 92,
}


def _extract_published_after_from_text(text: str) -> datetime | None:
    """自然言語から投稿日下限（published_after）を抽出。"""
    now = datetime.now(UTC)
    m = re.search(r"(半年|三ヶ月|3ヶ月|三カ月|3カ月|[0-9０-９]+[ヶカ]?月|1年|年|本年|今年|最近)\s*以内", text)
    if m:
        return _period_to_date(m.group(1), now)
    if re.search(r"(今年|本年)", text):
        return datetime(now.year, 1, 1, tzinfo=UTC)
    m = re.search(r"最近\s*([0-9０-９]+)\s*日", text)
    if m:
        return now - timedelta(days=int(m.group(1)))
    return None


def _period_to_date(label: str, now: datetime) -> datetime | None:
    num_m = re.search(r"([0-9０-９]+)\s*[ヶカ]?\s*月", label)
    if num_m:
        months = int(num_m.group(1))
        total_months = now.year * 12 + (now.month - 1) - months
        y = total_months // 12
        mo = total_months % 12 + 1
        return datetime(y, mo, now.day, now.hour, now.minute, now.second, now.microsecond, tzinfo=UTC)
    if label in _RELATIVE_PERIOD_DAYS:
        days = _RELATIVE_PERIOD_DAYS[label]
        return datetime(now.year, 1, 1, tzinfo=UTC) if days == 0 else now - timedelta(days=days)
    return None


def _parse_date_from_text(text: str) -> datetime | None:
    """明示的な日付指定（YYYY-MM-DD 以降）を抽出。"""
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s*(?:以降|から|より|以後)", text)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def _extract_count_from_text(text: str) -> int | None:
    kanji = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    m = re.search(r"(\d+)\s*(?:個|件|本|つ|カ国|か国|社|人)?", text)
    if m:
        return int(m.group(1))
    for k, v in kanji.items():
        if re.search(rf"{k}\s*(?:個|件|本|つ|カ国|か国|社|人)", text):
            return v
    return None


def parse_instruction(state: State) -> State:
    """自然言語指示からトピック・件数・投稿日下限を抽出する。"""
    provider = state.get("provider")
    emitter = make_emitter()
    emitter.emit(1, NODE_PARSE_INSTRUCTION, "開始")

    raw = state.get("instruction_raw", "")
    model = build_model("research")
    prompt = provider.parse_instruction_prompt.format(instruction=raw)
    result = model.invoke(prompt)
    text = result.content if hasattr(result, "content") else str(result)
    parsed = extract_json_block(text) or {}

    topic = str(parsed.get("topic", "")).strip() or raw
    # 件数: CLI/run 上書き（state.max_results）＞自然言語＞LLM
    cli_max = state.get("max_results")
    if cli_max is not None:
        max_results = int(cli_max)
    else:
        nl = _extract_count_from_text(raw)
        max_results = nl if nl is not None else int(parsed.get("max_results", 5) or 5)
    # 出力形式: CLI/run（state.output_format）＞自然言語/LLM
    cli_fmt = state.get("output_format")
    if cli_fmt is not None:
        output_format = cli_fmt
    else:
        fmt = str(parsed.get("output_format", "markdown")).lower()
        output_format = OutputFormat.JSON if fmt == "json" else OutputFormat.MARKDOWN

    # 期間: CLI --since（state.published_after）＞自然言語
    cli_since = state.get("published_after")
    published_after = cli_since or _extract_published_after_from_text(raw) or _parse_date_from_text(raw)

    platform = provider.name
    instruction = ResearchInstruction(
        raw_text=raw,
        platform=platform,
        topic=topic,
        max_results=max_results,
        output=OutputSpec(format=output_format),
        published_after=published_after,
        use_trends=bool(state.get("use_trends", False)),
        sort_by=str(state.get("sort_by", "relevance")),
        transcript_language=str(state.get("transcript_language", "ja") or "ja"),
    )

    emitter.emit(1, NODE_PARSE_INSTRUCTION, "完了", detail=f'トピック: "{topic}" / 件数: {max_results}')
    return {"instruction": instruction}
