"""compile_report ノード（FR-009/FR-010 対応、markdown/json 両対応）。"""

from __future__ import annotations

from pathlib import Path

from youtube_trend_researcher.cache import write_json
from youtube_trend_researcher.models import ResearchReport
from youtube_trend_researcher.progress import NODE_COMPILE_REPORT, make_emitter
from youtube_trend_researcher.state import State


def compile_report(state: State) -> State:
    """選定動画・要約・共通ネタをまとめた ResearchReport を組み立てる。

    Args:
        state: instruction / candidates / analyses / common_themes / notes を含む State。

    Returns:
        更新された State（report をセット）。
    """
    emitter = make_emitter()
    emitter.emit(7, NODE_COMPILE_REPORT, "開始")

    instruction = state["instruction"]
    candidates = state.get("candidates", [])
    analyses = state.get("analyses", [])
    common_themes = state.get("common_themes", [])
    notes = list(state.get("notes", []))

    # 期間フィルタ条件を notes に記録
    published_after = instruction.published_after
    if published_after is not None:
        notes.append(f"投稿日フィルタ: {published_after.date()} 以降に公開された動画を対象")

    # 候補 0 件時はその旨を記録（後続の字幕取得・要約はスキップ済み）
    if not candidates:
        notes.append("該当する動画が見つかりませんでした（検索クエリまたは期間フィルタの条件に一致する動画なし）。")

    sources = [c.url for c in candidates if c.url]

    report = ResearchReport(
        instruction=instruction,
        candidates=candidates,
        analyses=analyses,
        common_themes=common_themes,
        sources=sources,
        notes=notes,
    )

    emitter.emit(7, NODE_COMPILE_REPORT, "完了")

    # FR-012: 中間成果物（完成レポート）を cache_dir に永続化
    cache_dir = state.get("cache_dir")
    if cache_dir:
        try:
            write_json(Path(cache_dir), "report", report.model_dump(mode="json"))
        except Exception as exc:  # noqa: BLE001 - 永続化失敗は本体処理を止めない
            emitter.emit(7, NODE_COMPILE_REPORT, f"キャッシュ書き込み失敗: {exc}")

    return {"report": report}


def _render_candidates_table(report: ResearchReport) -> list[str]:
    lines = ["## 選定動画リスト（関連度順上位 N 件）", ""]
    lines.append("| # | タイトル | チャンネル | 再生数 | URL |")
    lines.append("|---|----------|------------|--------|-----|")
    for c in report.candidates:
        vc = f"{c.view_count:,}" if c.view_count is not None else "-"
        lines.append(f"| {c.relevance_rank} | {c.title} | {c.channel_title} | {vc} | {c.url} |")
    lines.append("")
    return lines


def _render_analysis_block(c: "object", a: "object | None") -> list[str]:
    """1 動画分の要約ブロック（メタデータ + 概要 + 活用アイデア + 引用）。"""
    lines: list[str] = [f"### {c.relevance_rank}. {c.title}"]
    meta_bits = [f"チャンネル: {c.channel_title}" if c.channel_title else None,
                 f"再生数: {c.view_count:,}" if c.view_count is not None else None,
                 f"公開日: {c.published_at.date()}" if c.published_at is not None else None]
    meta_line = " ｜ ".join(b for b in meta_bits if b)
    if meta_line:
        lines.append(f"> {meta_line}")
        lines.append("")
    if a is None:
        lines.append("- 要約: （解析なし）")
        lines.append("")
        return lines
    lines.append("**概要**")
    lines.append("")
    lines.append(a.summary)
    lines.append("")
    if a.angles:
        lines.append("**ブログの活用アイデア**")
        lines.append("")
        lines.append("| 切り口 | 読者への価値 | 拾えるキーフレーズ |")
        lines.append("|--------|--------------|---------------------|")
        for ang in a.angles:
            angle = ang.angle.replace("\n", " ")
            value = ang.value.replace("\n", " ")
            phrase = ang.key_phrase.replace("\n", " ")
            lines.append(f"| {angle} | {value} | {phrase} |")
        lines.append("")
    if a.evidence:
        lines.append("**そのまま使える引用**")
        lines.append("")
        for ev in a.evidence:
            lines.append(f"- {ev}")
        lines.append("")
    return lines


def _render_common_themes(report: ResearchReport) -> list[str]:
    lines = ["## 共通ネタ（表）", ""]
    if report.common_themes:
        lines.append("| テーマ | 説明 | 該当動画 | 代表抜粋 |")
        lines.append("|--------|------|----------|----------|")
        for t in report.common_themes:
            supporting = ", ".join(t.supporting_video_ids) or "-"
            quotes = " / ".join(t.example_quotes) or "-"
            lines.append(f"| {t.theme} | {t.description} | {supporting} | {quotes} |")
    else:
        lines.append("（特筆すべき共通点なし）")
    lines.append("")
    return lines


def render_markdown(report: ResearchReport) -> str:
    """ResearchReport を Markdown 文字列に整形（FR-009 既定）。"""
    instruction = report.instruction
    lines: list[str] = []
    title = instruction.topic or instruction.raw_text[:40]
    lines.append(f"# リサーチレポート: {title}")
    lines.append("")

    lines.extend(_render_candidates_table(report))

    # 個別要約
    lines.append("## 各動画のブログ向け要約")
    lines.append("")
    analyses_by_id = {a.video_id: a for a in report.analyses}
    for c in report.candidates:
        lines.extend(_render_analysis_block(c, analyses_by_id.get(c.video_id)))

    lines.extend(_render_common_themes(report))

    # 出典
    lines.append("## 出典")
    lines.append("")
    for s in report.sources:
        lines.append(f"- {s}")
    lines.append("")

    # 備考
    if report.notes:
        lines.append("## 備考")
        lines.append("")
        for n in report.notes:
            lines.append(f"- {n}")
        lines.append("")

    return "\n".join(lines)


def render_json(report: ResearchReport) -> str:
    """ResearchReport を JSON 文字列に整形（FR-009/SC-004）。"""
    return report.model_dump_json(indent=2, exclude_none=True)
