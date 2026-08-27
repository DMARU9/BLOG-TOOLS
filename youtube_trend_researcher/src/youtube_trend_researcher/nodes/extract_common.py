"""extract_common ノード（FR-008 対応、動画本文のみ）。"""

from __future__ import annotations

from youtube_trend_researcher.models import AnalysisFinding, CommonTheme
from youtube_trend_researcher.prompts import EXTRACT_COMMON_PROMPT
from youtube_trend_researcher.progress import NODE_EXTRACT_COMMON, make_emitter
from youtube_trend_researcher.state import State
from youtube_trend_researcher.tools.llm import build_model
from youtube_trend_researcher.tools.parse import extract_list_items, extract_section


def _format_analyses(analyses: list[AnalysisFinding]) -> str:
    lines = []
    for a in analyses:
        lines.append(f"### 動画 {a.video_id}")
        lines.append(f"要約: {a.summary}")
        lines.append("ポイント: " + " / ".join(a.key_points))
        lines.append("根拠: " + " / ".join(a.evidence))
        lines.append("")
    return "\n".join(lines)


def extract_common(state: State) -> State:
    """動画間の共通ネタを抽出する。

    Args:
        state: `analyses` を含む State。

    Returns:
        更新された State（common_themes をセット）。
    """
    emitter = make_emitter()
    emitter.emit(6, NODE_EXTRACT_COMMON, "開始")

    analyses = state.get("analyses", [])
    model = build_model("research")
    prompt = EXTRACT_COMMON_PROMPT.format(analyses=_format_analyses(analyses))
    result = model.invoke(prompt)
    text = result.content if hasattr(result, "content") else str(result)

    themes = _parse_themes(text, [a.video_id for a in analyses])

    emitter.emit(6, NODE_EXTRACT_COMMON, "完了", detail=f"{len(themes)} 件の共通テーマ")
    return {"common_themes": themes}


def _parse_themes(text: str, video_ids: list[str]) -> list[CommonTheme]:
    """Markdown の「### テーマ名」セクションを CommonTheme に変換。"""
    themes: list[CommonTheme] = []
    # テーマ区切り: ### で始まる行
    sections = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("### ") and current:
            sections.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current))

    for sec in sections:
        if "### " not in sec:
            continue
        # 最初の ### を行ごと抽出
        theme_name = ""
        body_lines: list[str] = []
        for line in sec.splitlines():
            if line.startswith("### ") and not theme_name:
                theme_name = line[4:].strip()
            else:
                body_lines.append(line)
        body = "\n".join(body_lines)
        if not theme_name or "特筆" in theme_name:
            continue
        desc = extract_section(body, "説明") or body
        supporting = video_ids  # 簡易: 全動画を該当とみなす（詳細な紐付けは将来拡張）
        quotes = extract_list_items(extract_section(body, "代表抜粋"))
        themes.append(
            CommonTheme(
                theme=theme_name,
                description=desc,
                supporting_video_ids=supporting,
                example_quotes=quotes,
            )
        )
    return themes
