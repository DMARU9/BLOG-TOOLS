"""tools/youtube_search.py の単体テスト（yt-dlp をモック）。"""

from datetime import UTC, datetime
from unittest import mock

from youtube_trend_researcher.tools.youtube_search import search_videos


def _fake_extract_info(url, download=False):
    # ytsearchN:query への呼び出しをシミュレーション
    return {
        "entries": [
            {
                "id": f"vid{i}",
                "title": f"動画 {i}",
                "url": f"https://www.youtube.com/watch?v=vid{i}",
                "channel": f"チャンネル{i}",
                "channel_id": f"ch{i}",
                "upload_date": "20260101",
                "view_count": 1000 * i,
                "like_count": 10 * i,
            }
            for i in range(1, 8)
        ]
    }


def test_search_videos_top_n():
    with mock.patch("yt_dlp.YoutubeDL") as ydl_mock:
        ydl_mock.return_value.__enter__.return_value.extract_info.side_effect = _fake_extract_info
        candidates = search_videos("テスト", max_results=5)

    assert len(candidates) == 5
    assert candidates[0].video_id == "vid1"
    assert candidates[0].relevance_rank == 1
    assert candidates[4].relevance_rank == 5
    assert candidates[0].view_count == 1000
    assert candidates[0].published_at == datetime(2026, 1, 1, tzinfo=UTC)
    assert candidates[0].url == "https://www.youtube.com/watch?v=vid1"


def test_search_videos_limits_to_max():
    with mock.patch("yt_dlp.YoutubeDL") as ydl_mock:
        ydl_mock.return_value.__enter__.return_value.extract_info.side_effect = _fake_extract_info
        candidates = search_videos("テスト", max_results=3)
    assert len(candidates) == 3
