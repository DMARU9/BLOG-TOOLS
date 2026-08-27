"""analyze_content ノード（FR-007 対応、並列上限 2）。"""

from __future__ import annotations

import asyncio

from youtube_trend_researcher.models import AnalysisFinding, VideoCandidate
from youtube_trend_researcher.progress import NODE_ANALYZE_CONTENT, make_emitter
from youtube_trend_researcher.prompts import ANALYZE_CONTENT_PROMPT
from youtube_trend_researcher.state import State
from youtube_trend_researcher.tools.llm import build_model
from youtube_trend_researcher.tools.parse import extract_list_items, extract_section


def _find_transcript(state: State, video_id: str) -> str:
    for t in state.get("transcripts", []):
        if t.video_id == video_id:
            return t.text
    return ""


async def _analyze_one(candidate: VideoCandidate, transcript_text: str) -> AnalysisFinding:
    model = build_model("research")
    prompt = ANALYZE_CONTENT_PROMPT.format(
        title=candidate.title,
        transcript=transcript_text[:20000] or "（字幕なし・メタデータのみ）",
    )
    result = model.invoke(prompt)
    text = result.content if hasattr(result, "content") else str(result)

    summary = extract_section(text, "要約")
    if not summary.strip():
        # フォールバック: 要約セクションが取れない場合は冒頭の段落を利用
        for para in text.split("\n\n"):
            para = para.strip()
            if para and not para.startswith("#"):
                summary = para
                break
    key_points = extract_list_items(extract_section(text, "ブログで取り上げられそうなポイント"))
    evidence = extract_list_items(extract_section(text, "根拠"))

    return AnalysisFinding(
        video_id=candidate.video_id,
        summary=summary,
        key_points=key_points,
        evidence=evidence,
    )


async def _analyze_all(candidates: list[VideoCandidate], transcripts_by_id: dict[str, str]) -> list[AnalysisFinding]:
    # 並列実行数の上限は 2（analyze_content 等の同時 LLM 呼び出し）
    sem = asyncio.Semaphore(2)

    async def _bounded(cand: VideoCandidate) -> AnalysisFinding:
        async with sem:
            return await _analyze_one(cand, transcripts_by_id.get(cand.video_id, ""))

    return await asyncio.gather(*[_bounded(c) for c in candidates])


def analyze_content(state: State) -> State:
    """各動画を「ブログ執筆の参考」として要約する（並列上限 2）。

    Args:
        state: `candidates` と `transcripts` を含む State。

    Returns:
        更新された State（analyses をセット）。
    """
    emitter = make_emitter()
    emitter.emit(5, NODE_ANALYZE_CONTENT, "開始", detail="並列上限 2")

    candidates = state.get("candidates", [])
    transcripts_by_id = {t.video_id: t.text for t in state.get("transcripts", [])}

    analyses = asyncio.run(_analyze_all(candidates, transcripts_by_id))

    emitter.emit(5, NODE_ANALYZE_CONTENT, "完了", detail=f"{len(analyses)} 件を要約")
    return {"analyses": analyses}
