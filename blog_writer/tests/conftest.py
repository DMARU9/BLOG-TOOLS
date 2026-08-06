import pytest

@pytest.fixture
def sample_markdown():
    return """---
title: Sample Post
description: This is a sample blog post description.
---

# Hello World

This is the content.
"""
