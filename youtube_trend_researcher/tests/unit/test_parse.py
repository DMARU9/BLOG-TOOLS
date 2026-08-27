"""tools/parse.py の単体テスト。"""

from youtube_trend_researcher.tools.parse import (
    extract_json_block,
    extract_list_items,
    extract_section,
)


def test_extract_json_block_fenced():
    text = '説明\n```json\n{"topic": "AI", "max_results": 10}\n```\n終わり'
    assert extract_json_block(text) == {"topic": "AI", "max_results": 10}


def test_extract_json_block_bare():
    text = '前置き {"a": 1} 後置き'
    assert extract_json_block(text) == {"a": 1}


def test_extract_json_block_none():
    assert extract_json_block("") is None


def test_extract_list_items_dash():
    text = "- ポイント1\n- ポイント2\n本文"
    assert extract_list_items(text) == ["ポイント1", "ポイント2"]


def test_extract_list_items_numbered():
    text = "1. 最初\n2. 次\n"
    assert extract_list_items(text) == ["最初", "次"]


def test_extract_section():
    text = "# タイトル\n本文\n## 要約\nここが要約\n## 他\n"
    assert extract_section(text, "要約") == "ここが要約"
