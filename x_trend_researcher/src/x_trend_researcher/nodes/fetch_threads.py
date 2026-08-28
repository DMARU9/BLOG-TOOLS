"""fetch_threads ノード（FR-006 対応、字幕取得ノードの代わり）。"""

from __future__ import annotations

from x_trend_researcher.config import get_config
from x_trend_researcher.models import TweetContext
from x_trend_researcher.progress import NODE_FETCH_THREADS, make_emitter
from x_trend_researcher.state import State
from x_trend_researcher.tools.x_search import fetch_threads


def fetch_threads_node(state: State) -> State:
    """選定ツイートのスレッド展開＋リプライを取得する。取得不能時は notes に記録。

    Args:
        state: `candidates` を含む State。

    Returns:
        更新された State（contexts と notes をセット）。
    """
    emitter = make_emitter()
    emitter.emit(4, NODE_FETCH_THREADS, "開始")

    candidates = state.get("candidates", [])
    contexts: list[TweetContext] = []
    notes: list[str] = list(state.get("notes", []))

    if candidates:
        try:
            contexts = fetch_threads(candidates, accounts_db=str(get_config().accounts_db))
        except Exception as exc:  # noqa: BLE001 - コンテキスト取得失敗は本文のみで解析
            notes.append(f"スレッド取得に失敗しました（本文のみで解析）: {exc}")
            contexts = [TweetContext(tweet_id=c.tweet_id, text=c.text) for c in candidates]

    no_context = sum(1 for c in contexts if not (c.thread_text or c.replies))
    emitter.emit(
        4,
        NODE_FETCH_THREADS,
        "完了",
        detail=f"コンテキスト取得 {len(contexts)} 件（追加文脈なし {no_context} 件）",
    )
    return {"contexts": contexts, "notes": notes}
