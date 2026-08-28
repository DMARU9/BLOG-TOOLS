"""CLI エントリ（python -m x_trend_researcher）。FR-001/FR-010/FR-011/FR-013 対応。"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from x_trend_researcher.config import Config
from x_trend_researcher.graph import render_report, run
from x_trend_researcher.models import OutputFormat


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="x_trend_researcher",
        description="自然言語指示から自律的に X（Twitter）トレンドリサーチレポートを生成する CLI。",
    )
    parser.add_argument("instruction", help="自然言語のリサーチ指示")
    parser.add_argument("--output", help="レポート書き込み先ファイル（省略時は stdout）")
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="最終レポートの出力形式（既定: markdown）",
    )
    parser.add_argument("--max-results", type=int, default=None, help="解析対象件数（既定 5）")
    parser.add_argument(
        "--since",
        default=None,
        help="投稿日下限（YYYY-MM-DD）。この日以降に公開された投稿のみ対象（自然言語の「半年以内」等も可）",
    )
    parser.add_argument("--cache-dir", default=None, help="中間成果物の永続化先（既定: cache/）")
    parser.add_argument(
        "--trends",
        action="store_true",
        help="トレンドワード探索モード（予約。現在は通常検索と同じ）",
    )
    parser.add_argument(
        "--sort",
        choices=["relevance", "likes"],
        default="relevance",
        help="選定基準（既定: relevance＝検索の関連度順。likes＝いいね数順）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI メイン。戻り値は終了コード（0/1/2）。"""
    try:
        args = _parse_args(argv)
    except SystemExit as exc:
        if exc.code == 0:
            raise  # --help 等: そのまま終了コード 0 で通す（T033）
        return 2  # 引数エラー（code != 0）

    config = Config.load(cache_dir=args.cache_dir)

    # 出力形式を instruction.output に反映（render_report で使用）
    output_format = OutputFormat.JSON if args.format == "json" else OutputFormat.MARKDOWN

    # 投稿日下限（--since YYYY-MM-DD）
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
            max_results=args.max_results,
            output_format=output_format,
            since=since,
            use_trends=args.trends,
            cache_dir=str(config.cache_dir),
            sort_by=args.sort,
        )
    except Exception as exc:  # noqa: BLE001 - FR-011: すべての実行時エラーをユーザーに通知
        print(f"[エラー] リサーチ実行中に問題が発生しました: {exc}", file=sys.stderr, flush=True)
        return 1

    # 該当 0 件（FR-011 Edge Case）
    if not report.candidates:
        print("該当なし: 指定された指示に一致するツイートが見つかりませんでした。", file=sys.stderr, flush=True)
        rendered = render_report(report)
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered)
        return 0

    rendered = render_report(report)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"[完了] レポートを書き出しました: {args.output}", file=sys.stderr, flush=True)
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
