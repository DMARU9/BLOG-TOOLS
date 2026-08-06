"""blog_writer CLI - ブログ記事作成支援ツール."""

import argparse
import sys


def main() -> None:
    """メインエントリーポイント."""
    parser = argparse.ArgumentParser(
        prog="blog_writer",
        description="ブログ記事作成支援ツール",
    )
    subparsers = parser.add_subparsers(dest="command", help="利用可能なコマンド")

    # trend コマンド
    trend_parser = subparsers.add_parser("trend", help="トレンド分析を実行")
    trend_parser.add_argument("topic", help="分析するトピック")

    # seo コマンド
    seo_parser = subparsers.add_parser("seo", help="SEO チェックを実行")
    seo_parser.add_argument("file", help="チェックする Markdown ファイル")

    # validate コマンド
    validate_parser = subparsers.add_parser("validate", help="Markdown バリデーションを実行")
    validate_parser.add_argument("file", help="バリデーションする Markdown ファイル")

    # analyze コマンド
    analyze_parser = subparsers.add_parser("analyze", help="プロジェクト分析を実行")
    analyze_parser.add_argument("path", help="分析するプロジェクトパス")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "trend":
        from blog_writer.trend_analyzer import analyze_trend

        result = analyze_trend(args.topic)
        print(f"トピック: {result.topic}")
        print(f"関連クエリ: {', '.join(result.related_queries)}")

    elif args.command == "seo":
        from blog_writer.seo_checker import check_seo

        report = check_seo(args.file)
        print(f"SEO スコア: {report.score}/100")
        if report.issues:
            print("問題:")
            for issue in report.issues:
                print(f"  - {issue}")

    elif args.command == "validate":
        from blog_writer.markdown_validator import validate_markdown

        result = validate_markdown(args.file)
        if result.is_valid:
            print("バリデーション通過")
        else:
            print("バリデーション失敗:")
            for error in result.errors:
                print(f"  - {error}")
            sys.exit(1)

    elif args.command == "analyze":
        from blog_writer.project_analyzer import analyze_project

        info = analyze_project(args.path)
        print(f"プロジェクト: {info.name}")
        print(f"技術スタック: {', '.join(info.tech_stack)}")


if __name__ == "__main__":
    main()
