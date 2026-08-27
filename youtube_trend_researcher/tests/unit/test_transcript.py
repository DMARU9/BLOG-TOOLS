"""tools/transcript.py の単体テスト（yt-dlp をモック）。"""

import os
import tempfile
from unittest import mock

from youtube_trend_researcher.models import TranscriptSource
from youtube_trend_researcher.tools.transcript import (
    _parse_vtt,
    fetch_transcript,
)


def _write_sub_file(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".vtt", prefix="ytr_t_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _fake_info_with_requested_subs(url, download=False):
    # 新実装は requested_subtitles の filepath からテキストを読む
    ja_path = _write_sub_file(
        "WEBVTT\nKind: captions\nLanguage: ja\n\n"
        "00:00:01.000 --> 00:00:02.000\n皆<00:00:01.500><c>さん</c>、こんにちは\n"
    )
    return {
        "subtitles": {"ja": [{"ext": "vtt", "url": "http://sub.example/ja"}]},
        "automatic_captions": {"en": [{"ext": "vtt", "url": "http://sub.example/en"}]},
        "requested_subtitles": {
            "ja": {"ext": "vtt", "filepath": ja_path},
        },
    }


def _fake_info_only_auto(url, download=False):
    en_path = _write_sub_file(
        "WEBVTT\nKind: captions\nLanguage: en\n\n"
        "00:00:01.000 --> 00:00:02.000\nHello world\n"
    )
    return {
        "subtitles": {},
        "automatic_captions": {"en": [{"ext": "vtt", "url": "http://sub.example/en"}]},
        "requested_subtitles": {
            "en": {"ext": "vtt", "filepath": en_path},
        },
    }


def _fake_info_no_subs(url, download=False):
    return {"subtitles": {}, "automatic_captions": {}, "requested_subtitles": {}}


def test_fetch_transcript_caption_preferred():
    with mock.patch("yt_dlp.YoutubeDL") as ydl_mock:
        ydl_mock.return_value.__enter__.return_value.extract_info.side_effect = _fake_info_with_requested_subs
        t = fetch_transcript("vid1", language="ja")
    assert t.source == TranscriptSource.CAPTION
    assert t.language == "ja"
    assert "皆さん、こんにちは" in t.text  # インラインタグが除去されている


def test_fetch_transcript_fallback_to_auto():
    with mock.patch("yt_dlp.YoutubeDL") as ydl_mock:
        ydl_mock.return_value.__enter__.return_value.extract_info.side_effect = _fake_info_only_auto
        t = fetch_transcript("vid1", language="ja")
    # 指定言語 ja がない場合、自動字幕の先頭言語（en）へフォールバック
    assert t.source == TranscriptSource.AUTOMATIC_CAPTION
    assert "Hello world" in t.text


def test_fetch_transcript_fallback_empty():
    with mock.patch("yt_dlp.YoutubeDL") as ydl_mock:
        ydl_mock.return_value.__enter__.return_value.extract_info.side_effect = _fake_info_no_subs
        t = fetch_transcript("vid1", language="ja")
    # 字幕なし → 空テキスト（呼び出し側で notes 記録の責務）
    assert t.text == ""
    assert t.source == TranscriptSource.AUTOMATIC_CAPTION


def test_parse_vtt_removes_inline_tags():
    raw = (
        "WEBVTT\nKind: captions\nLanguage: ja\n\n"
        "00:00:00.320 --> 00:00:02.149 align:start position:0%\n"
        "皆<00:00:00.520><c>さん</c>、エージェントは使っていますか\n"
    )
    assert _parse_vtt(raw) == "皆さん、エージェントは使っていますか"
