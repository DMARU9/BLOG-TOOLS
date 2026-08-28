"""parse_instruction ノード（FR-001 対応）。"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from youtube_trend_researcher.models import OutputFormat, OutputSpec, ResearchInstruction
from youtube_trend_researcher.progress import NODE_PARSE_INSTRUCTION, make_emitter
from youtube_trend_researcher.prompts import PARSE_INSTRUCTION_PROMPT
from youtube_trend_researcher.state import State
from youtube_trend_researcher.tools.llm import build_model
from youtube_trend_researcher.tools.parse import extract_json_block

# 相対期間表現（「半年以内」「3ヶ月以内」「1年以内」等）を日数に変換
_RELATIVE_PERIOD_DAYS = {
    "半年": 182,
    "三ヶ月": 92,
    "3ヶ月": 92,
    "三カ月": 92,
    "3カ月": 92,
    "一月": 31,
    "1月": 31,
    "一年": 365,
    "1年": 365,
    "本年": 365,
    "今年": 0,  # 当年 1/1 から
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
    prompt = PARSE_INSTRUCTION_PROMPT.replace("{instruction}", raw_text)
    result = model.invoke(prompt)
    text = result.content if hasattr(result, "content") else str(result)

    parsed = extract_json_block(text) or {}
    topic = str(parsed.get("topic", "")) or raw_text
    # 件数: CLI/run の上書き（state.max_results）を最優先、次に自然言語、最後に LLM 出力
    cli_max = state.get("max_results")
    if cli_max is not None:
        max_results = int(cli_max)
    else:
        nl_count = _extract_count_from_text(raw_text)
        if nl_count is not None:
            max_results = nl_count
        else:
            max_results = int(parsed.get("max_results", 5) or 5)
    # 出力形式: CLI/run の指定（state.output_format）を最優先、なければ自然言語/LLM 出力
    cli_fmt = state.get("output_format")
    if cli_fmt is not None:
        output_format = cli_fmt
    else:
        fmt = str(parsed.get("output_format", "markdown")).lower()
        output_format = OutputFormat.JSON if fmt == "json" else OutputFormat.MARKDOWN
    # 期間: CLI --since（state.published_after）を優先、なければ自然言語から抽出
    cli_since = state.get("published_after")
    published_after = cli_since or _extract_published_after_from_text(raw_text) or _parse_date_from_text(raw_text)

    instruction = ResearchInstruction(
        raw_text=raw_text,
        topic=topic,
        max_results=max_results,
        output=OutputSpec(format=output_format),
        published_after=published_after,
    )

    emitter.emit(
        1,
        NODE_PARSE_INSTRUCTION,
        "完了",
        detail=f"topic: {topic}, max_results: {max_results}"
        + (f", since: {published_after.date()}" if published_after else ""),
    )
    return {"instruction": instruction}


def _parse_date_from_text(text: str) -> datetime | None:
    """明示的な日付指定（YYYY-MM-DD 以降）を抽出。"""
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s*(?:以降|から|より|以後)", text)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            return None
    return None
