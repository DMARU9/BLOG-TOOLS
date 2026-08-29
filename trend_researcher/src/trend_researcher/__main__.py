"""CLI エントリ（python -m trend_researcher）。X / YouTube 共通。"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from trend_researcher.config import Config
from trend_researcher.graph import render_report, run
from trend_researcher.models import OutputFormat
from trend_researcher.providers import available_platforms


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="trend_researcher",
        description="自然言語指示から自律的にトレンドリサーチレポートを生成する CLI（X / YouTube 対応）。",
    )
    parser.add_argument("instruction", help="自然言語のリサーチ指示")
    parser.add_argument(
        "--platform",
        choices=available_platforms(),
        default="x",
        help="対象プラットフォーム（x=X/Twitter、youtube=YouTube）。既定: x",
    )
    parser.add_argument("--output", help="レポート書き込み先ファイル（省略時は stdout）")
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="最終レポートの出力形式（既定: markdown）",
    )
    parser.add_argument("--max-results", type=int, default=None, help="解析対象件数（既定 5）")
    parser.add_argument("--lang", default=None, help="字幕取得の優先言語（YouTube 用、既定: ja）")
    parser.add_argument(
        "--since",
        default=None,
        help="投稿日下限（YYYY-MM-DD）。この日以降に公開された投稿のみ対象",
    )
    parser.add_argument("--cache-dir", default=None, help="中間成果物の永続化先（既定: cache/）")
    parser.add_argument(
        "--trends",
        action="store_true",
        help="トレンドワード探索モード（X 用。予約。現在は通常検索と同じ）",
    )
    parser.add_argument(
        "--sort",
        choices=["relevance", "likes"],
        default="relevance",
        help="選定基準（X 用。relevance=関連度順／likes=いいね数順）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI メイン。戻り値は終了コード（0/1/2）。"""
    try:
        args = _parse_args(argv)
    except SystemExit as exc:
        if exc.code == 0:
            raise
        return 2

    platform = args.platform
    config = Config.load(platform=platform, cache_dir=args.cache_dir, max_results=args.max_results)
    lang = args.lang or config.transcript_language

    output_format = OutputFormat.JSON if args.format == "json" else OutputFormat.MARKDOWN

    since: datetime | None = None
    if args.since:
        try:
            since = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            print(f"[エラー] --since は YYYY-MM-DD 形式で指定してください: {args.since}", file=sys.stderr, flush=True)
            return 2

    try:
        report = run(
            args.instruction,
            platform=platform,
            max_results=args.max_results,
            transcript_language=lang,
            output_format=output_format,
            since=since,
            use_trends=args.trends,
            sort_by=args.sort,
            cache_dir=str(config.cache_dir),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[エラー] リサーチ実行中に問題が発生しました: {exc}", file=sys.stderr, flush=True)
        return 1

    if not report.candidates:
        subject = "ツイート" if platform == "x" else "動画"
        print(f"該当なし: 指定された指示に一致する{subject}が見つかりませんでした。", file=sys.stderr, flush=True)
        rendered = render_report(report)
    else:
        requested = report.instruction.max_results or config.max_results
        if len(report.candidates) < requested:
            print(
                f"[情報] 要求件数 {requested} 件に対し、実際に見つかったのは "
                f"{len(report.candidates)} 件です。",
                file=sys.stderr,
                flush=True,
            )
        rendered = render_report(report)

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"[完了] レポートを {args.output} に書き出しました。", file=sys.stderr, flush=True)
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    sys.exit(main())
