"""fetch_transcripts ノード（FR-006 対応）。"""

from __future__ import annotations

from youtube_trend_researcher.models import Transcript
from youtube_trend_researcher.progress import NODE_FETCH_TRANSCRIPTS, make_emitter
from youtube_trend_researcher.state import State
from youtube_trend_researcher.tools.transcript import fetch_transcript


def fetch_transcripts(state: State) -> State:
    """選定動画の字幕を取得する。取得不能時は notes に記録。

    Args:
        state: `candidates` を含む State。

    Returns:
        更新された State（transcripts と notes をセット）。
    """
    emitter = make_emitter()
    emitter.emit(4, NODE_FETCH_TRANSCRIPTS, "開始")

    candidates = state.get("candidates", [])
    language = state.get("transcript_language", "ja")
    transcripts: list[Transcript] = []
    notes: list[str] = list(state.get("notes", []))

    for cand in candidates:
        transcript = fetch_transcript(cand.video_id, language=language)
        transcripts.append(transcript)
        if not transcript.text.strip():
            notes.append(f"字幕取得不可: {cand.title} ({cand.video_id}) - メタデータのみで解析")

    meta_only = sum(1 for t in transcripts if not t.text.strip())
    fetched = len(transcripts) - meta_only
    emitter.emit(
        4,
        NODE_FETCH_TRANSCRIPTS,
        "完了",
        detail=f"字幕 {fetched} 件 / メタデータのみ {meta_only} 件",
    )
    return {"transcripts": transcripts, "notes": notes}
