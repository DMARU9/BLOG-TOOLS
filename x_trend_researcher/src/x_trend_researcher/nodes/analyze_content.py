"""analyze_content ノード（FR-007 対応、並列上限 2）。"""

from __future__ import annotations

import asyncio
import re

from x_trend_researcher.models import AnalysisFinding, BlogAngle, TweetCandidate
from x_trend_researcher.progress import NODE_ANALYZE_CONTENT, make_emitter
from x_trend_researcher.prompts import ANALYZE_CONTENT_PROMPT
from x_trend_researcher.state import State
from x_trend_researcher.tools.llm import build_model
from x_trend_researcher.tools.parse import extract_list_items, extract_section


def _find_context(state: State, tweet_id: str) -> "object | None":
    for t in state.get("contexts", []):
        if t.tweet_id == tweet_id:
            return t
    return None


def _parse_angles_table(markdown_table: str) -> list[BlogAngle]:
    """「ブログの活用アイデア」表（| 切り口 | 読者への価値 | 拾えるキーフレーズ |）を解析。"""
    angles: list[BlogAngle] = []
    for line in markdown_table.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        # ヘッダー行・区切り行をスキップ
        if re.match(r"^\|[\s:|-]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0] in ("切り口", "角度"):
            continue
        angles.append(
            BlogAngle(
                angle=cells[0],
                value=cells[1],
                key_phrase=cells[2],
            )
        )
    return angles


def _build_source_text(candidate: TweetCandidate, context: "object | None") -> str:
    """ツイート本文＋スレッド＋リプライをブログ要約用のソーステキストに整形。"""
    parts: list[str] = []
    body = candidate.text
    thread = getattr(context, "thread_text", "") if context else ""
    replies = getattr(context, "replies", []) if context else []
    if thread:
        parts.append(f"[親ツイート（スレッド）]\n{thread}")
    parts.append(f"[ツイート本文]\n{body}")
    if replies:
        parts.append("[代表的なリプライ]\n" + "\n".join(f"- {r}" for r in replies))
    return "\n\n".join(parts)


async def _analyze_one(candidate: TweetCandidate, source_text: str) -> AnalysisFinding:
    model = build_model("research")
    prompt = ANALYZE_CONTENT_PROMPT.format(
        title=candidate.author_handle or candidate.url,
        transcript=source_text[:20000] or "（本文なし・メタデータのみ）",
    )
    # 非同期呼び出し（ainvoke）にすることで asyncio.Semaphore(2) の並列制御が有効になる
    result = await model.ainvoke(prompt)
    text = result.content if hasattr(result, "content") else str(result)

    summary = extract_section(text, "概要")
    angles = _parse_angles_table(extract_section(text, "ブログの活用アイデア"))
    evidence = extract_list_items(extract_section(text, "そのまま使える引用"))

    if not summary.strip():
        # フォールバック 1: 概要セクションが取れない場合は冒頭の段落を利用
        for para in text.split("\n\n"):
            para = para.strip()
            if para and not para.startswith("#"):
                summary = para
                break
    if not summary.strip() and angles:
        # フォールバック 2: それでも空なら、活用アイデアの切り口から簡易概要を合成
        summary = f"このツイートでは、{angles[0].angle}などについて語られています。" + (
            f"ほかにも{angles[1].angle}といった観点が扱われており、ブログのネタとして活用できます。"
            if len(angles) > 1 else ""
        )

    # 後方互換および共通ネタ抽出用に、切り口を key_points にも保持
    key_points = [a.angle for a in angles] if angles else []

    return AnalysisFinding(
        tweet_id=candidate.tweet_id,
        summary=summary,
        angles=angles,
        key_points=key_points,
        evidence=evidence,
    )


async def _analyze_all(candidates: list[TweetCandidate], contexts_by_id: dict[str, "object"]) -> list[AnalysisFinding]:
    # 並列実行数の上限は 2（analyze_content 等の同時 LLM 呼び出し）
    sem = asyncio.Semaphore(2)

    async def _bounded(cand: TweetCandidate) -> AnalysisFinding:
        source_text = _build_source_text(cand, contexts_by_id.get(cand.tweet_id))
        async with sem:
            return await _analyze_one(cand, source_text)

    return await asyncio.gather(*[_bounded(c) for c in candidates])


def analyze_content(state: State) -> State:
    """各ツイートを「ブログ執筆の参考」として要約する（並列上限 2）。

    Args:
        state: `candidates` と `contexts` を含む State。

    Returns:
        更新された State（analyses をセット）。
    """
    emitter = make_emitter()
    emitter.emit(5, NODE_ANALYZE_CONTENT, "開始", detail="並列上限 2")

    candidates = state.get("candidates", [])
    contexts_by_id = {t.tweet_id: t for t in state.get("contexts", [])}

    analyses = asyncio.run(_analyze_all(candidates, contexts_by_id))

    emitter.emit(5, NODE_ANALYZE_CONTENT, "完了", detail=f"{len(analyses)} 件を要約")
    return {"analyses": analyses}
