import os
import tempfile
import textwrap
import pytest
from blog_writer.trend_analyzer import analyze_trend
from blog_writer.project_analyzer import analyze_project
from blog_writer.seo_checker import check_seo
from blog_writer.markdown_validator import validate_markdown

@pytest.mark.integration
def test_basic_flow():
    """Test the basic flow: topic -> analysis -> check."""
    topic = "Python プログラミング"
    
    # 1. Trend Analysis (Mocked or slow)
    # For integration test, we'll skip actual API calls if possible,
    # but the tool is designed to be standalone.
    # In a real CI, we might mock this.
    # trend_result = analyze_trend(topic)
    # assert trend_result.trend_score > 0

    # 2. Project Analysis (with temp dir)
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "README.md"), "w") as f:
            f.write("# Test Project\nA test project.")
        project_result = analyze_project(tmpdir)
        assert project_result.name == os.path.basename(tmpdir)

    # 3. SEO & Validation Check (with generated file)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        content = textwrap.dedent("""\
            ---
            title: "Python プログラミング入門：基礎から実践まで学べる完全ガイド"
            description: "Python プログラミングの基本的な概念と使い方を初心者向けに解説します。変数、関数、クラスなどの基礎知識から、実践的なアプリケーション開発まで、具体的なコード例を交えて分かりやすく丁寧に説明します。初心者が挫折しないよう、ステップバイステップで学べる構成です。"
            pubDate: "2023-01-01"
            tags: ["python", "programming"]
            ---

            # Python プログラミング

            Python は人気のあるプログラミング言語です。

            ## 基本

            変数や関数の使い方を学びましょう。
        """)
        f.write(content)
        f.flush()
        
        seo_result = check_seo(f.name)
        assert seo_result.total_score == 100.0
        
        md_result = validate_markdown(f.name)
        assert md_result.is_valid is True
        
        os.unlink(f.name)
