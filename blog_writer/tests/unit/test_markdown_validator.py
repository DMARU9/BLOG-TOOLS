import os
import tempfile
from unittest.mock import patch
from blog_writer.markdown_validator import validate_markdown, ValidationResult

def test_validate_markdown_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("---\ntitle: 'Test Title'\ndescription: 'Test Description'\npubDate: '2023-01-01'\n---\n\n# Heading\n\nContent")
        f.flush()
        
        with patch('blog_writer.markdown_validator.subprocess') as mock_subprocess:
            mock_subprocess.run.return_value.returncode = 0
            result = validate_markdown(f.name)
            
            os.unlink(f.name)
            assert isinstance(result, ValidationResult)
            assert result.is_valid is True
            assert result.frontmatter_valid is True

def test_validate_markdown_missing_frontmatter():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Heading\n\nContent")
        f.flush()
        result = validate_markdown(f.name)
        os.unlink(f.name)
        
        assert result.is_valid is False
        assert result.frontmatter_valid is False
        assert any("Frontmatterがありません" in e for e in result.errors)
