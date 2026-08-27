"""yt-dlp による字幕取得（Whisper なし、自動翻訳字幕含む）。FR-006 対応。"""

from __future__ import annotations

import logging
import os
import tempfile

from youtube_trend_researcher.models import Transcript, TranscriptSource

logger = logging.getLogger(__name__)


def fetch_transcript(video_id: str, language: str = "ja") -> Transcript:
    """指定動画の字幕を取得する。

    yt-dlp の自動翻訳機能により、原則として必ず取得できる。
    取得できない場合は空文字を返し、呼び出し側で notes に記録する責務を持つ。

    Args:
        video_id: YouTube 動画ID。
        language: 優先言語コード（既定 ja）。

    Returns:
        Transcript（source は caption / automatic_caption）。
    """
    import yt_dlp  # type: ignore[import-untyped]

    url = f"https://www.youtube.com/watch?v={video_id}"
    tmp_dir = tempfile.mkdtemp(prefix="ytr_sub_")
    # 指定言語のみリクエストする（複数言語は YouTube 側のレート制限を誘発するため）
    ydl_opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [language],
        "outtmpl": os.path.join(tmp_dir, "%(id)s.%(ext)s"),
        "getcomments": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[call-arg]
            info = ydl.extract_info(url, download=True)
    except yt_dlp.DownloadError as exc:
        logger.warning("字幕取得に失敗しました（video_id=%s）: %s", video_id, exc)
        return Transcript(
            video_id=video_id,
            language=language,
            text="",
            source=TranscriptSource.AUTOMATIC_CAPTION,
        )

    if not isinstance(info, dict):
        return Transcript(video_id=video_id, language=language, text="", source=TranscriptSource.AUTOMATIC_CAPTION)

    subs = info.get("subtitles") or {}
    auto_subs = info.get("automatic_captions") or {}
    requested = info.get("requested_subtitles") or {}

    # 指定言語の手動/自動字幕を優先
    chosen_lang = language if language in requested else None
    # なければ自動字幕の先頭言語を自動翻訳フォールバックとして利用
    if chosen_lang is None and requested:
        chosen_lang = next(iter(requested))

    text = ""
    source = TranscriptSource.AUTOMATIC_CAPTION
    if chosen_lang:
        if chosen_lang in subs:
            source = TranscriptSource.CAPTION
        elif chosen_lang in auto_subs:
            source = TranscriptSource.AUTOMATIC_CAPTION
        sub = requested.get(chosen_lang, {})
        text = _read_subtitle_file(sub)

    return Transcript(video_id=video_id, language=language, text=text, source=source)


def _read_subtitle_file(sub: dict) -> str:
    """requested_subtitles エントリから字幕テキストを読み取る。"""
    # メモリ上の data があればそれをパース（json3 等）
    data = sub.get("data")
    if isinstance(data, dict) and data.get("events"):
        return _parse_json3(data)
    # それ以外はファイルから読む
    filepath = sub.get("filepath")
    if filepath and os.path.exists(filepath):
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        ext = os.path.splitext(filepath)[1].lstrip(".")
        if ext == "json3":
            return _parse_json3(_load_json(content))
        return _parse_vtt(content)
    return ""


def _load_json(content: str) -> dict:
    import json

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def _parse_vtt(content: str) -> str:
    """VTT/SRT 形式の字幕からタイムスタンプ等を除いたテキストを結合する。"""
    import re

    # srv3 由来のインラインタグ（<00:00:00.520>, <c>...</c>）を除去
    content = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", content)
    content = re.sub(r"</?c>", "", content)

    parts: list[str] = []
    for line in content.splitlines():
        s = line.strip()
        if not s:
            continue
        if s == "WEBVTT":
            continue
        if s.startswith("Kind:") or s.startswith("Language:"):
            continue
        if "-->" in s:  # タイムコード行
            continue
        parts.append(s)
    return "".join(parts)


def _parse_json3(data: dict) -> str:
    """json3 形式の字幕データからテキストを結合する。"""
    events = data.get("events", [])
    parts: list[str] = []
    for e in events:
        for seg in e.get("segs") or []:
            parts.append(seg.get("utf8", ""))
    return "".join(parts)
