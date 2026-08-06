import os
import tempfile
from blog_writer.seo_checker import check_seo, SeoReport

def test_check_seo_valid_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("---\ntitle: 'This is a valid blog post title for SEO'\ndescription: 'This is a valid description that meets the length requirements for search engines. It should be between 120 and 160 characters.'\n---\n\n# Heading\n\nContent")
        f.flush()
        result = check_seo(f.name)
        os.unlink(f.name)
        
        assert isinstance(result, SeoReport)
        assert result.total_score == 100.0
        assert len(result.issues) == 0

def test_check_seo_invalid_title():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("---\ntitle: 'Short'\ndescription: 'This is a valid description that meets the length requirements for search engines. It should be between 120 and 160 characters.'\n---\n\n# Heading\n\nContent")
        f.flush()
        result = check_seo(f.name)
        os.unlink(f.name)
        
        assert result.title_score < 100.0
        assert any("短すぎます" in issue for issue in result.issues)
