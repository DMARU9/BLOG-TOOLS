"""extract_common ノード（FR-008 対応、ツイート本文のみ）。"""

from __future__ import annotations

import re

from x_trend_researcher.models import AnalysisFinding, CommonTheme
from x_trend_researcher.progress import NODE_EXTRACT_COMMON, make_emitter
from x_trend_researcher.prompts import EXTRACT_COMMON_PROMPT
from x_trend_researcher.state import State
from x_trend_researcher.tools.llm import build_model
from x_trend_researcher.tools.parse import extract_list_items, extract_section


def _format_analyses(analyses: list[AnalysisFinding]) -> str:
    lines = []
    for a in analyses:
        lines.append(f"### ツイート {a.tweet_id}")
        lines.append(f"要約: {a.summary}")
        lines.append("ポイント: " + " / ".join(a.key_points))
        lines.append("根拠: " + " / ".join(a.evidence))
        lines.append("")
    return "\n".join(lines)


def extract_common(state: State) -> State:
    """ツイート間の共通ネタを抽出する。

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

    themes = _parse_themes(text, [a.tweet_id for a in analyses])

    emitter.emit(6, NODE_EXTRACT_COMMON, "完了", detail=f"{len(themes)} 件の共通テーマ")
    return {"common_themes": themes}


def _split_sections(text: str) -> list[list[str]]:
    """Markdown を「### / #### 見出し」で区切ったセクション（行のリスト）に分割。"""
    heading_re = re.compile(r"^#{3,4}\s+(.*)$")
    sections: list[list[str]] = []
    current: list[str] = []
    for line in text.splitlines():
        if heading_re.match(line):
            if current:
                sections.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append(current)
    return sections


def _parse_themes(text: str, tweet_ids: list[str]) -> list[CommonTheme]:
    """Markdown の「### テーマ名」/「#### N. テーマ」セクションを CommonTheme に変換。

    LLM の出力スタイル（### または #### の見出し）の揺れを吸収する。
    """
    themes: list[CommonTheme] = []
    heading_re = re.compile(r"^#{3,4}\s+(.*)$")

    idx = 0
    for sec in _split_sections(text):
        hm = heading_re.match(sec[0])
        if not hm:
            continue
        theme_name = hm.group(1).strip()
        # テンプレートのプレースホルダや総括見出しはスキップ
        if theme_name in ("共通テーマ", "テーマ", "テーマ名") or "特筆" in theme_name:
            continue
        body = "\n".join(sec[1:]).strip()
        if not body and theme_name:
            # 見出しだけの場合はそのまま説明とする
            body = theme_name
        idx += 1
        desc = extract_section(body, "説明") or body
        # 簡易: 全ツイートを該当とみなす（詳細な紐付けは将来拡張）
        supporting = tweet_ids
        quotes = extract_list_items(extract_section(body, "代表抜粋")) or extract_list_items(body)
        themes.append(
            CommonTheme(
                theme=theme_name or f"共通テーマ{idx}",
                description=desc,
                supporting_tweet_ids=supporting,
                example_quotes=quotes,
            )
        )
    return themes
