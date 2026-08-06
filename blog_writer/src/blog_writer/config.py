# Configuration for Blog Writer Tools
import os
from pathlib import Path

# API Endpoints
OPEN_DEEP_RESEARCH_API = os.getenv("OPEN_DEEP_RESEARCH_API", "http://127.0.0.1:2024/runs/stream")

# Blog Output Configuration
# ブログ記事の出力先ディレクトリ
BLOG_OUTPUT_DIR = os.getenv(
    "BLOG_OUTPUT_DIR",
    str(Path.home() / "github" / "DMARU9.github.io" / "src" / "content" / "blog")
)

# SEO Constants
MIN_TITLE_LENGTH = 30
MAX_TITLE_LENGTH = 60
MIN_DESCRIPTION_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 160

# Rate Limiting
PYTRENDS_SLEEP_SECONDS = 5
