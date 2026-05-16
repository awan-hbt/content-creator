"""Tests for src/utils.py"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.content_generator import YouTubeContent
from src.utils import save_content, slugify


def _make_content(**kwargs) -> YouTubeContent:
    defaults = dict(
        topic="viral topic",
        title="My Amazing YouTube Video",
        description="Full description here.",
        script_hook="Hook text",
        script_intro="Intro text",
        script_sections=[{"heading": "Section 1", "content": "Body text"}],
        script_cta="CTA text",
        tags=["youtube", "viral"],
        thumbnail_concept="Big bold text on colourful background",
        end_screen_suggestion="Show 2 video cards",
        estimated_duration_minutes=8,
    )
    defaults.update(kwargs)
    return YouTubeContent(**defaults)


class TestSlugify:
    def test_lowercases(self):
        assert slugify("Hello World") == "hello-world"

    def test_removes_special_chars(self):
        assert slugify("AI & ML: 2025!") == "ai-ml-2025"

    def test_replaces_spaces_with_hyphens(self):
        result = slugify("best tips ever")
        assert " " not in result
        assert "-" in result

    def test_max_length(self):
        long_text = "a" * 100
        result = slugify(long_text, max_length=20)
        assert len(result) <= 20


class TestSaveContent:
    def test_saves_markdown_and_json(self, tmp_path):
        content = _make_content()
        paths = save_content(content, output_dir=tmp_path)

        assert paths["markdown"].exists()
        assert paths["json"].exists()

    def test_markdown_contains_title(self, tmp_path):
        content = _make_content(title="Unique Title For Test")
        paths = save_content(content, output_dir=tmp_path)

        text = paths["markdown"].read_text()
        assert "Unique Title For Test" in text

    def test_json_is_valid(self, tmp_path):
        content = _make_content()
        paths = save_content(content, output_dir=tmp_path)

        data = json.loads(paths["json"].read_text())
        assert "title" in data
        assert "script" in data
        assert "tags" in data

    def test_creates_output_dir_if_absent(self, tmp_path):
        new_dir = tmp_path / "subdir" / "output"
        assert not new_dir.exists()

        content = _make_content()
        save_content(content, output_dir=new_dir)

        assert new_dir.exists()

    def test_filename_includes_slug(self, tmp_path):
        content = _make_content(title="Best Video Ever")
        paths = save_content(content, output_dir=tmp_path)

        assert "best-video-ever" in paths["markdown"].name
