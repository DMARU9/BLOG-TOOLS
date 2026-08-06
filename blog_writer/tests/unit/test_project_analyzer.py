import os
import tempfile
from blog_writer.project_analyzer import analyze_project, ProjectInfo

def test_analyze_project_returns_project_info():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple project structure
        with open(os.path.join(tmpdir, 'README.md'), 'w') as f:
            f.write("# Test Project\n\nThis is a test project description.")
        
        with open(os.path.join(tmpdir, 'main.py'), 'w') as f:
            f.write("print('hello')")
            
        result = analyze_project(tmpdir)
        
        assert isinstance(result, ProjectInfo)
        assert result.name == os.path.basename(tmpdir)
        assert 'Python' in result.tech_stack
        assert 'Test Project' in result.readme_summary
