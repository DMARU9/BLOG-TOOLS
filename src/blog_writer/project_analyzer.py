import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional

from bs4 import BeautifulSoup


@dataclass
class ProjectInfo:
    name: str
    description: str
    tech_stack: List[str]
    readme_summary: str
    directory_structure: Optional[str] = None


def analyze_project(path: str) -> ProjectInfo:
    """Analyze a project directory and extract information."""
    if not os.path.exists(path):
        return ProjectInfo(
            name=os.path.basename(path),
            description="ディレクトリが見つかりません",
            tech_stack=[],
            readme_summary=""
        )

    # Project name
    name = os.path.basename(os.path.abspath(path))
    
    # Tech stack detection based on file extensions
    tech_stack = set()
    extensions_map = {
        '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
        '.astro': 'Astro', '.tsx': 'React', '.vue': 'Vue',
        '.go': 'Go', '.rs': 'Rust', '.java': 'Java'
    }
    
    # Check for package files
    if os.path.exists(os.path.join(path, 'package.json')):
        tech_stack.add('Node.js')
    if os.path.exists(os.path.join(path, 'pyproject.toml')) or os.path.exists(os.path.join(path, 'requirements.txt')):
        tech_stack.add('Python')
    if os.path.exists(os.path.join(path, 'Cargo.toml')):
        tech_stack.add('Rust')
        
    # Simple directory scan (limited depth)
    for root, dirs, files in os.walk(path):
        # Skip hidden dirs and node_modules
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'vendor', '__pycache__']]
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in extensions_map:
                tech_stack.add(extensions_map[ext])
        
        # Limit depth
        if root.count(os.sep) - path.count(os.sep) > 2:
            continue

    # README parsing
    readme_summary = ""
    readme_path = os.path.join(path, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Simple extraction: first 200 chars or first paragraph
            lines = content.split('\n')
            # Skip title and empty lines
            for line in lines[1:]:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith('#'):
                    readme_summary = clean_line[:200]
                    break
            if not readme_summary and lines:
                readme_summary = lines[0][:200]

    description = f"プロジェクト「{name}」の分析結果です。"
    
    return ProjectInfo(
        name=name,
        description=description,
        tech_stack=sorted(list(tech_stack)),
        readme_summary=readme_summary
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m blog_writer.project_analyzer <path>")
        sys.exit(1)
    
    path = sys.argv[1]
    result = analyze_project(path)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
