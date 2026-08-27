"""tools/transcript.py の単体テスト（yt-dlp をモック）。"""

from unittest import mock

from youtube_trend_researcher.models import TranscriptSource
from youtube_trend_researcher.tools.transcript import fetch_transcript


def _fake_info_with_subs(url, download=False):
    return {
        "subtitles": {"ja": [{"ext": "vtt", "url": "http://sub.example/ja"}]},
        "automatic_captions": {"en": [{"ext": "vtt", "url": "http://sub.example/en"}]},
    }


def _fake_info_no_subs(url, download=False):
    return {"subtitles": {}, "automatic_captions": {}}


def test_fetch_transcript_caption_preferred():
    with mock.patch("yt_dlp.YoutubeDL") as ydl_mock:
        ydl_mock.return_value.__enter__.return_value.extract_info.side_effect = _fake_info_with_subs
        t = fetch_transcript("vid1", language="ja")
    assert t.source == TranscriptSource.CAPTION
    assert t.language == "ja"


def test_fetch_transcript_fallback_empty():
    with mock.patch("yt_dlp.YoutubeDL") as ydl_mock:
        ydl_mock.return_value.__enter__.return_value.extract_info.side_effect = _fake_info_no_subs
        t = fetch_transcript("vid1", language="ja")
    # 字幕なし → 空テキスト（呼び出し側で notes 記録の責務）
    assert t.text == ""
    assert t.source == TranscriptSource.AUTOMATIC_CAPTION
