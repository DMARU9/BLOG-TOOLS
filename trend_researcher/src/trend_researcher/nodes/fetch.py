"""fetch ノード（FR-006 対応、X: スレッド/リプライ / YouTube: 字幕、共通）。"""

from __future__ import annotations

from trend_researcher.progress import NODE_FETCH, make_emitter
from trend_researcher.state import State


def fetch_node(state: State) -> State:
    """provider.fetch_contexts を呼び出し、要約用ソースを取得する。"""
    emitter = make_emitter()
    emitter.emit(4, NODE_FETCH, "開始")

    provider = state["provider"]
    config = state.get("config")
    candidates = state.get("candidates", [])
    contexts, notes = provider.fetch_contexts(candidates, config)

    notes = list(state.get("notes", [])) + notes
    no_context = sum(1 for c in contexts if not c.text.strip() and not c.thread_text and not c.replies)
    emitter.emit(
        4,
        NODE_FETCH,
        "完了",
        detail=f"コンテキスト取得 {len(contexts)} 件（追加文脈なし {no_context} 件）",
    )
    return {"contexts": contexts, "notes": notes}
