"""yt-dlp による字幕取得（Whisper なし、自動翻訳字幕含む）。FR-006 対応。"""

from __future__ import annotations

from youtube_trend_researcher.models import Transcript, TranscriptSource


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
    import yt_dlp

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [language],
        "skip_download": True,
        "getcomments": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[call-arg]
            info = ydl.extract_info(url, download=False)
    except Exception:
        return Transcript(
            video_id=video_id,
            language=language,
            text="",
            source=TranscriptSource.AUTOMATIC_CAPTION,
        )

    if not isinstance(info, dict):
        return Transcript(video_id=video_id, language=language, text="", source=TranscriptSource.AUTOMATIC_CAPTION)

    # 手動字幕 → 自動字幕（自動翻訳含む）の順で探す
    text = ""
    source = TranscriptSource.AUTOMATIC_CAPTION
    subs = info.get("subtitles") or {}
    auto_subs = info.get("automatic_captions") or {}

    if language in subs:
        source = TranscriptSource.CAPTION
        text = _extract_text(url, subs[language])
    elif language in auto_subs:
        text = _extract_text(url, auto_subs[language])
    else:
        # 言語がなければ自動字幕の先頭を利用（自動翻訳フォールバック）
        if auto_subs:
            first_lang = next(iter(auto_subs))
            text = _extract_text(url, auto_subs[first_lang])

    return Transcript(video_id=video_id, language=language, text=text, source=source)


def _extract_text(url: str, formats: list[dict]) -> str:
    """字幕フォーマット一覧から JSON3 等のテキストを抽出する。"""
    import yt_dlp

    # json3 / srv3 / vtt 等から取得
    preferred = [f for f in formats if f.get("ext") in ("json3", "srv3", "vtt", "ttml")]
    target = preferred[0] if preferred else (formats[0] if formats else None)
    if not target:
        return ""

    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            sub_info = ydl.extract_info(target.get("url"), download=False)
        if isinstance(sub_info, dict) and sub_info.get("data"):
            # json3 の場合 events リストから text を結合
            events = sub_info.get("events", [])
            parts = [e.get("segs", [{}])[0].get("utf8", "") for e in events if e.get("segs")]
            return "".join(parts)
    except Exception:
        pass
    return ""
