"""compile_report ノード（FR-009/FR-010 対応、markdown/json 両対応）。"""

from __future__ import annotations

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
    return {"report": report}


def render_markdown(report: ResearchReport) -> str:
    """ResearchReport を Markdown 文字列に整形（FR-009 既定）。"""
    instruction = report.instruction
    lines: list[str] = []
    title = instruction.topic or instruction.raw_text[:40]
    lines.append(f"# リサーチレポート: {title}")
    lines.append("")

    # 選定動画リスト
    lines.append("## 選定動画リスト（関連度順上位 N 件）")
    lines.append("")
    lines.append("| # | タイトル | チャンネル | 再生数 | URL |")
    lines.append("|---|----------|------------|--------|-----|")
    for c in report.candidates:
        vc = f"{c.view_count:,}" if c.view_count is not None else "-"
        lines.append(f"| {c.relevance_rank} | {c.title} | {c.channel_title} | {vc} | {c.url} |")
    lines.append("")

    # 個別要約
    lines.append("## 各動画のブログ向け要約")
    lines.append("")
    analyses_by_id = {a.video_id: a for a in report.analyses}
    for c in report.candidates:
        a = analyses_by_id.get(c.video_id)
        lines.append(f"### {c.relevance_rank}. {c.title}")
        if a:
            lines.append(f"- 要約: {a.summary}")
            if a.key_points:
                lines.append("- ブログで取り上げられそうなポイント:")
                for kp in a.key_points:
                    lines.append(f"  - {kp}")
            if a.evidence:
                lines.append("- 根拠:")
                for ev in a.evidence:
                    lines.append(f"  - {ev}")
        else:
            lines.append("- 要約: （解析なし）")
        lines.append("")

    # 共通ネタ表
    lines.append("## 共通ネタ（表）")
    lines.append("")
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
