"""LLM 出力の軽いパース関数（構造化出力の強制はしない）。"""

from __future__ import annotations

import json
import re
from typing import Any


def extract_json_block(text: str) -> dict[str, Any] | None:
    """LLM 出力から最初の JSON オブジェクト（```json 含む）を抽出する。"""
    if not text:
        return None
    # ```json ... ``` を優先
    fenced = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    # 波括弧内を探す
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            return None
    return None


def extract_list_items(text: str, marker: str = "-") -> list[str]:
    """Markdown リスト（"- " または "1. "）から項目を抽出する。"""
    if not text:
        return []
    items: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(rf"^(?:\{marker}\s+|\d+\.\s+)(.*)$", line)
        if m:
            items.append(m.group(1).strip())
    return items


def extract_section(text: str, heading: str) -> str:
    """Markdown から指定見出し直下の本文を抽出する。"""
    if not text:
        return ""
    pattern = re.compile(rf"^#{1,6}\s*{re.escape(heading)}\s*$", re.MULTILINE)
    m = pattern.search(text)
    if not m:
        return ""
    start = m.end()
    # 次の見出しまで
    next_heading = re.compile(r"^#{1,6}\s+", re.MULTILINE).search(text, start)
    end = next_heading.start() if next_heading else len(text)
    return text[start:end].strip()
