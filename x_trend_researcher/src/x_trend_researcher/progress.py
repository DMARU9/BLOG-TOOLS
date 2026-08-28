"""ノード進捗エミッタ（FR-013 対応）。stderr へ逐次出力。"""

from __future__ import annotations

import sys
from typing import TextIO


class ProgressEmitter:
    """全ノードから呼び出される進捗表示ユーティリティ。

    進捗は常に「開始」または「完了」のいずれかで更新され、
    エラー／成功メッセージのみの空白状態を作らない（FR-013）。
    """

    TOTAL = 7

    def __init__(self, total: int = TOTAL, stream: TextIO | None = None) -> None:
        self.total = total
        self._stream = stream or sys.stderr

    def emit(self, node_index: int, node_name: str, phase: str, detail: str = "") -> None:
        """進捗を stderr へ出力。

        Args:
            node_index: ノード順序（1始まり）。
            node_name: ノード名。
            phase: "開始" | "完了"。
            detail: 任意の補足（クエリ内容等）。
        """
        suffix = f"（{detail}）" if detail else ""
        line = f"[{node_index}/{self.total}] {node_name} ... {phase}{suffix}"
        print(line, file=self._stream, flush=True)


# ノード名の固定定義（順序と一致させる）
NODE_PARSE_INSTRUCTION = "parse_instruction"
NODE_PLAN_SEARCH = "plan_search"
NODE_SEARCH_TWEETS = "search_tweets"
NODE_FETCH_THREADS = "fetch_threads"
NODE_ANALYZE_CONTENT = "analyze_content"
NODE_EXTRACT_COMMON = "extract_common"
NODE_COMPILE_REPORT = "compile_report"

NODE_ORDER = [
    NODE_PARSE_INSTRUCTION,
    NODE_PLAN_SEARCH,
    NODE_SEARCH_TWEETS,
    NODE_FETCH_THREADS,
    NODE_ANALYZE_CONTENT,
    NODE_EXTRACT_COMMON,
    NODE_COMPILE_REPORT,
]


def make_emitter() -> ProgressEmitter:
    """標準の ProgressEmitter を生成。"""
    return ProgressEmitter(total=len(NODE_ORDER))
