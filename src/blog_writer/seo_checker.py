import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import List

from bs4 import BeautifulSoup

from .config import MIN_TITLE_LENGTH, MAX_TITLE_LENGTH, MIN_DESCRIPTION_LENGTH, MAX_DESCRIPTION_LENGTH


@dataclass
class SeoReport:
    file_path: str
    title_score: float
    description_score: float
    heading_score: float
    alt_text_score: float
    total_score: float
    issues: List[str]


def check_seo(file_path: str) -> SeoReport:
    """Perform SEO checks on a markdown/HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return SeoReport(file_path=file_path, title_score=0, description_score=0, heading_score=0, alt_text_score=0, total_score=0, issues=["ファイルが見つかりません"])

    issues = []
    title_score = 100.0
    description_score = 100.0
    heading_score = 100.0
    alt_text_score = 100.0

    # Parse frontmatter (simple regex)
    fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    fm_content = fm_match.group(1) if fm_match else ""
    
    title = ""
    description = ""
    for line in fm_content.split('\n'):
        if line.startswith('title:'):
            title = line.split(':', 1)[1].strip().strip('"').strip("'")
        elif line.startswith('description:'):
            description = line.split(':', 1)[1].strip().strip('"').strip("'")

    # Title check
    if not title:
        title_score = 0
        issues.append("タイトルがありません")
    elif len(title) < MIN_TITLE_LENGTH:
        title_score = 50
        issues.append(f"タイトルが短すぎます ({len(title)}文字 / {MIN_TITLE_LENGTH}-{MAX_TITLE_LENGTH}文字)")
    elif len(title) > MAX_TITLE_LENGTH:
        title_score = 50
        issues.append(f"タイトルが長すぎます ({len(title)}文字 / {MIN_TITLE_LENGTH}-{MAX_TITLE_LENGTH}文字)")

    # Description check
    if not description:
        description_score = 0
        issues.append("ディスクリプションがありません")
    elif len(description) < MIN_DESCRIPTION_LENGTH:
        description_score = 50
        issues.append(f"ディスクリプションが短すぎます ({len(description)}文字)")
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        description_score = 50
        issues.append(f"ディスクリプションが長すぎます ({len(description)}文字)")

    # Heading structure check
    # Remove frontmatter for HTML parsing
    body = content[fm_match.end():] if fm_match else content
    # Convert simple markdown headings to HTML for parsing
    html_body = re.sub(r'^# (.*)', r'<h1>\1</h1>', body, flags=re.MULTILINE)
    html_body = re.sub(r'^## (.*)', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^### (.*)', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
    
    soup = BeautifulSoup(html_body, 'html.parser')
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    h1_count = len(soup.find_all('h1'))
    if h1_count == 0:
        heading_score -= 50
        issues.append("H1見出しがありません")
    elif h1_count > 1:
        heading_score -= 20
        issues.append(f"H1見出しが複数あります ({h1_count}個)")
    
    # Check order
    prev_level = 0
    for h in headings:
        level = int(h.name[1])
        if level > prev_level + 1 and prev_level != 0:
            heading_score -= 10
            issues.append(f"見出しのレベルが飛んでいます ({h.name})")
        prev_level = level

    # Alt text check
    images = soup.find_all('img')
    missing_alt = 0
    for img in images:
        if not img.get('alt'):
            missing_alt += 1
    
    if images:
        alt_text_score = ((len(images) - missing_alt) / len(images)) * 100
        if missing_alt > 0:
            issues.append(f"画像のalt属性が {missing_alt} 個不足しています")

    total_score = (title_score + description_score + heading_score + alt_text_score) / 4

    return SeoReport(
        file_path=file_path,
        title_score=title_score,
        description_score=description_score,
        heading_score=heading_score,
        alt_text_score=alt_text_score,
        total_score=total_score,
        issues=issues
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m blog_writer.seo_checker <file>")
        sys.exit(1)
    
    result = check_seo(sys.argv[1])
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
