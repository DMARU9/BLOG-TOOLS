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


def _fake_extract_info_mixed_dates(url, download=False):
    # 新しい(2026-06)と古い(2024-01)が混在
    dates = ["20260601", "20240101", "20260615", "20240115", "20260701"]
    return {
        "entries": [
            {
                "id": f"vid{i}",
                "title": f"動画 {i}",
                "url": f"https://www.youtube.com/watch?v=vid{i}",
                "channel": f"チャンネル{i}",
                "channel_id": f"ch{i}",
                "upload_date": dates[i - 1],
                "view_count": 1000 * i,
                "like_count": 10 * i,
            }
            for i in range(1, 6)
        ]
    }


def test_search_videos_published_after_filter():
    with mock.patch("yt_dlp.YoutubeDL") as ydl_mock:
        ydl_mock.return_value.__enter__.return_value.extract_info.side_effect = _fake_extract_info_mixed_dates
        # 2025-01-01 以降のみ
        candidates = search_videos("テスト", max_results=10, published_after=datetime(2025, 1, 1, tzinfo=UTC))
    assert len(candidates) == 3  # 2026年の3件のみ
    assert all(c.published_at >= datetime(2025, 1, 1, tzinfo=UTC) for c in candidates)


def test_search_videos_published_after_overfetch():
    with mock.patch("yt_dlp.YoutubeDL") as ydl_mock:
        ydl_mock.return_value.__enter__.return_value.extract_info.side_effect = _fake_extract_info_mixed_dates
        # 件数指定より多く取得して絞り込む（過剰取得の確認）
        candidates = search_videos("テスト", max_results=2, published_after=datetime(2025, 1, 1, tzinfo=UTC))
    assert len(candidates) == 2
    # 外部呼び出しの fetch_count が max_results*3 以上になっているか確認
    call_arg = ydl_mock.return_value.__enter__.return_value.extract_info.call_args[0][0]
    assert "ytsearch" in call_arg
    # ytsearch6 以上（2*3）で検索しているはず
    n = int(call_arg.split("ytsearch")[1].split(":")[0])
    assert n >= 6
