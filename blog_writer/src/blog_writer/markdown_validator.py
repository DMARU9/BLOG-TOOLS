import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass


@dataclass
class ValidationResult:
    file_path: str
    is_valid: bool
    frontmatter_valid: bool
    markdownlint_valid: bool
    errors: list[str]


REQUIRED_FRONTMATTER = ['title', 'description', 'pubDate']


def validate_markdown(file_path: str) -> ValidationResult:
    """Validate a markdown file for frontmatter and markdownlint compliance."""
    errors = []
    frontmatter_valid = True
    markdownlint_valid = True

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return ValidationResult(file_path=file_path, is_valid=False, frontmatter_valid=False, markdownlint_valid=False, errors=["ファイルが見つかりません"])

    # 1. Frontmatter Validation
    fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not fm_match:
        frontmatter_valid = False
        errors.append("Frontmatterがありません")
    else:
        fm_content = fm_match.group(1)
        for field in REQUIRED_FRONTMATTER:
            if not re.search(rf'^{field}:', fm_content, re.MULTILINE):
                frontmatter_valid = False
                errors.append(f"Frontmatterに '{field}' がありません")

    # 2. Markdownlint Validation
    try:
        # Use npx to run the locally installed markdownlint-cli
        result = subprocess.run(
            ['npx', 'markdownlint', file_path],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            markdownlint_valid = False
            # Extract error messages
            for line in result.stdout.strip().split('\n'):
                if line:
                    errors.append(f"markdownlint: {line}")
    except FileNotFoundError:
        errors.append("markdownlintが見つかりません (npm install -D markdownlint-cli)")
    except Exception as e:  # noqa: BLE001
        errors.append(f"markdownlint実行エラー: {e!s}")

    return ValidationResult(
        file_path=file_path,
        is_valid=frontmatter_valid and markdownlint_valid,
        frontmatter_valid=frontmatter_valid,
        markdownlint_valid=markdownlint_valid,
        errors=errors
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m blog_writer.markdown_validator <file>")
        sys.exit(1)
    
    result = validate_markdown(sys.argv[1])
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
