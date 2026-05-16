"""Tests for src/content_generator.py"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.content_generator import ContentGenerator, YouTubeContent


SAMPLE_RESPONSE = {
    "title": "10 AI Breakthroughs Changing the World in 2025",
    "description": "Discover the most mind-blowing AI breakthroughs of 2025...",
    "script": {
        "hook": "What if I told you AI can now...",
        "intro": "Welcome back to the channel...",
        "sections": [
            {"heading": "Breakthrough #1", "content": "The first breakthrough is..."},
            {"heading": "Breakthrough #2", "content": "Even more impressive..."},
        ],
        "cta": "If you found this valuable, smash the like button...",
    },
    "tags": ["AI", "2025", "technology", "artificial intelligence"],
    "thumbnail_concept": "Futuristic robot with glowing eyes, text overlay '2025'",
    "end_screen_suggestion": "Show two video cards with related AI content",
    "estimated_duration_minutes": 10,
}


def _make_mock_client(response_data: dict) -> MagicMock:
    """Return a mock OpenAI client that returns *response_data* as JSON."""
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = json.dumps(response_data)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


class TestYouTubeContent:
    def _make_content(self, **kwargs) -> YouTubeContent:
        defaults = dict(
            topic="AI breakthroughs",
            title="10 AI Breakthroughs",
            description="All about AI...",
            script_hook="What if...",
            script_intro="Welcome...",
            script_sections=[{"heading": "Part 1", "content": "..."}],
            script_cta="Like and subscribe!",
            tags=["AI", "tech"],
            thumbnail_concept="Robot image",
            end_screen_suggestion="Show more videos",
            estimated_duration_minutes=10,
        )
        defaults.update(kwargs)
        return YouTubeContent(**defaults)

    def test_to_markdown_contains_title(self):
        content = self._make_content()
        md = content.to_markdown()
        assert "# 10 AI Breakthroughs" in md

    def test_to_markdown_contains_hook(self):
        content = self._make_content(script_hook="Unique hook text")
        md = content.to_markdown()
        assert "Unique hook text" in md

    def test_to_markdown_contains_tags(self):
        content = self._make_content(tags=["foo", "bar", "baz"])
        md = content.to_markdown()
        assert "foo, bar, baz" in md

    def test_to_markdown_contains_sections(self):
        content = self._make_content(
            script_sections=[{"heading": "My Section", "content": "Section body text"}]
        )
        md = content.to_markdown()
        assert "My Section" in md
        assert "Section body text" in md

    def test_to_dict_structure(self):
        content = self._make_content()
        d = content.to_dict()
        assert "title" in d
        assert "description" in d
        assert "script" in d
        assert "hook" in d["script"]
        assert "sections" in d["script"]
        assert "tags" in d
        assert "thumbnail_concept" in d

    def test_to_dict_roundtrip(self):
        content = self._make_content()
        d = content.to_dict()
        assert d["topic"] == content.topic
        assert d["title"] == content.title
        assert d["tags"] == content.tags


class TestContentGenerator:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            ContentGenerator(api_key="")

    def test_generate_returns_youtube_content(self):
        mock_client = _make_mock_client(SAMPLE_RESPONSE)

        with patch("src.content_generator.OpenAI", return_value=mock_client):
            gen = ContentGenerator(api_key="test-key")
            result = gen.generate(topic="AI breakthroughs 2025")

        assert isinstance(result, YouTubeContent)
        assert result.title == SAMPLE_RESPONSE["title"]
        assert result.description == SAMPLE_RESPONSE["description"]

    def test_generate_parses_script(self):
        mock_client = _make_mock_client(SAMPLE_RESPONSE)

        with patch("src.content_generator.OpenAI", return_value=mock_client):
            gen = ContentGenerator(api_key="test-key")
            result = gen.generate(topic="AI breakthroughs 2025")

        assert result.script_hook == SAMPLE_RESPONSE["script"]["hook"]
        assert result.script_intro == SAMPLE_RESPONSE["script"]["intro"]
        assert len(result.script_sections) == 2
        assert result.script_cta == SAMPLE_RESPONSE["script"]["cta"]

    def test_generate_parses_tags(self):
        mock_client = _make_mock_client(SAMPLE_RESPONSE)

        with patch("src.content_generator.OpenAI", return_value=mock_client):
            gen = ContentGenerator(api_key="test-key")
            result = gen.generate(topic="AI breakthroughs 2025")

        assert result.tags == SAMPLE_RESPONSE["tags"]

    def test_generate_parses_duration(self):
        mock_client = _make_mock_client(SAMPLE_RESPONSE)

        with patch("src.content_generator.OpenAI", return_value=mock_client):
            gen = ContentGenerator(api_key="test-key")
            result = gen.generate(topic="AI breakthroughs 2025", duration_minutes=10)

        assert result.estimated_duration_minutes == 10

    def test_generate_handles_missing_keys_gracefully(self):
        sparse_response = {"title": "Sparse", "script": {}}
        mock_client = _make_mock_client(sparse_response)

        with patch("src.content_generator.OpenAI", return_value=mock_client):
            gen = ContentGenerator(api_key="test-key")
            result = gen.generate(topic="Test topic")

        assert result.title == "Sparse"
        assert result.description == ""
        assert result.script_hook == ""
        assert result.tags == []
