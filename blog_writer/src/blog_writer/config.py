# Configuration for Blog Writer Tools
import os

# API Endpoints
OPEN_DEEP_RESEARCH_API = os.getenv("OPEN_DEEP_RESEARCH_API", "http://127.0.0.1:2024/runs/stream")

# SEO Constants
MIN_TITLE_LENGTH = 30
MAX_TITLE_LENGTH = 60
MIN_DESCRIPTION_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 160

# Rate Limiting
PYTRENDS_SLEEP_SECONDS = 5
