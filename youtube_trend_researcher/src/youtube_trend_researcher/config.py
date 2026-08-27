"""設定管理（OpenDeepResearch の設定を流用した形）。"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# パッケージルート（youtube_trend_researcher/）を解決
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_env_once() -> None:
    """プロジェクトの .env を一度だけ読み込む。"""
    env_path = _PACKAGE_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


class Config(BaseModel):
    """YouTube Trend Researcher の実行設定。"""

    openai_api_key: str = Field(default="")
    openai_base_url: str = Field(default="https://opencode.ai/zen/go/v1")
    model: str = Field(default="openai:mimo-v2.5")
    transcript_language: str = Field(default="ja")
    max_results: int = Field(default=5)
    cache_dir: Path = Field(default_factory=lambda: _PACKAGE_ROOT / "cache")
    max_retries: int = Field(default=3)

    @classmethod
    def load(cls, *, cache_dir: str | None = None, max_results: int | None = None) -> "Config":
        """環境変数／.env から設定を読み込む。

        Args:
            cache_dir: CLI 等からの上書き（任意）。
            max_results: CLI 等からの上書き（任意）。
        """
        _load_env_once()
        config = cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://opencode.ai/zen/go/v1"),
            model=os.getenv("YTR_MODEL", "openai:mimo-v2.5"),
            transcript_language=os.getenv("YTR_TRANSCRIPT_LANG", "ja"),
            max_results=int(os.getenv("YTR_MAX_RESULTS", "5")),
            cache_dir=Path(cache_dir) if cache_dir else Path(os.getenv("YTR_CACHE_DIR", str(_PACKAGE_ROOT / "cache"))),
            max_retries=int(os.getenv("YTR_MAX_RETRIES", "3")),
        )
        if max_results is not None:
            config.max_results = max_results
        return config


@lru_cache(maxsize=1)
def get_config() -> Config:
    """プロセス内で共有する Config を取得。"""
    return Config.load()
