"""yt-dlp を用いた検索（単一クエリ・関連度順上位 N 件）。FR-003/FR-004/FR-005 対応。"""

from __future__ import annotations

from datetime import UTC, datetime

import yt_dlp  # type: ignore[import-untyped]

from youtube_trend_researcher.models import VideoCandidate


def _parse_upload_date(raw: str | None) -> datetime | None:
    """yt-dlp の upload_date (YYYYMMDD) を UTC datetime に変換。"""
    if not raw or len(raw) != 8:
        return None
    try:
        return datetime.strptime(raw, "%Y%m%d").replace(tzinfo=UTC)
    except ValueError:
        return None


def search_videos(
    query: str, max_results: int = 5, published_after: datetime | None = None
) -> list[VideoCandidate]:
    """ytsearchN: で単一検索し、関連度順上位 N 件を VideoCandidate に変換する。

    Args:
        query: 検索クエリ（plan_search が生成）。
        max_results: 取得件数（既定 5）。
        published_after: 投稿日下限（任意）。指定時は期間内の動画のみを返す。

    Returns:
        関連度順の VideoCandidate リスト。
    """
    # 期間フィルタ指定時は過剰取得し、投稿日で絞り込む（yt-dlp に期間フィルタなし）
    fetch_count = max_results if published_after is None else max(max_results * 3, max_results + 10)

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        # extract_flat を False にして upload_date 等のメタデータを取得する。
        # flat のままだと upload_date が None になり、期間フィルタで全件除外される。
        "extract_flat": False,
        "skip_download": True,
        "default_search": f"ytsearch{fetch_count}",
        "dump_single_json": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[call-arg]
        info = ydl.extract_info(f"ytsearch{fetch_count}:{query}", download=False)

    entries = info.get("entries", []) if isinstance(info, dict) else []
    candidates: list[VideoCandidate] = []
    for rank, entry in enumerate(entries, start=1):
        if not entry:
            continue
        video_id = entry.get("id") or ""
        url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"
        published_at = _parse_upload_date(entry.get("upload_date"))
        # 期間フィルタ: published_after より古い動画は除外。
        # ただしメタデータ未取得（published_at が None）の場合は誤除外を防ぐため通す。
        if published_after is not None and published_at is not None and published_at < published_after:
            continue
        candidates.append(
            VideoCandidate(
                video_id=video_id or "",
                title=entry.get("title") or "",
                url=url,
                channel_id=entry.get("channel_id") or "",
                channel_title=entry.get("channel") or entry.get("uploader") or "",
                published_at=published_at,
                view_count=entry.get("view_count"),
                like_count=entry.get("like_count"),
                relevance_rank=len(candidates) + 1,
            )
        )
        if len(candidates) >= max_results:
            break

    return candidates
