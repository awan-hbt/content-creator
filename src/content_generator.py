"""
AI-powered YouTube content generator.

Uses OpenAI to produce a full YouTube content package for a given topic:
  - Engaging title
  - SEO-optimised description
  - Full video script (hook, body, CTA)
  - Tags / keywords
  - Thumbnail concept
  - Suggested end-screen / cards
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = """You are an expert YouTube content strategist and scriptwriter.
You create viral, engaging content optimised for YouTube's algorithm.
Your content is always:
- Attention-grabbing in the first 30 seconds
- Structured with clear hooks, value delivery, and strong CTAs
- Optimised with relevant SEO keywords
- Written in an authentic, conversational tone
- Tailored to maximise watch-time and audience retention
Always respond with valid JSON matching the requested schema."""

_CONTENT_PROMPT = """Create a complete YouTube content package for the following trending topic:

Topic: {topic}

Return a JSON object with EXACTLY these keys:
{{
  "title": "<catchy, SEO-optimised YouTube title (max 70 chars)>",
  "description": "<full YouTube description with keywords, timestamps placeholder, and links section (300-500 words)>",
  "script": {{
    "hook": "<opening 30-second hook script to grab attention>",
    "intro": "<30-second intro – channel intro + what viewer will learn>",
    "sections": [
      {{"heading": "<section heading>", "content": "<detailed script for this section>"}}
    ],
    "cta": "<60-second call-to-action – subscribe, like, comment prompt>"
  }},
  "tags": ["<tag1>", "<tag2>", "..."],
  "thumbnail_concept": "<detailed description of an eye-catching thumbnail>",
  "end_screen_suggestion": "<suggestion for end screen cards (30 seconds before video ends)>",
  "estimated_duration_minutes": <integer>
}}

Ensure the script is detailed enough to produce a {duration}-minute video.
Focus on making the content highly engaging and shareable."""


@dataclass
class YouTubeContent:
    """Holds all generated content for a single YouTube video."""

    topic: str
    title: str
    description: str
    script_hook: str
    script_intro: str
    script_sections: list[dict] = field(default_factory=list)
    script_cta: str = ""
    tags: list[str] = field(default_factory=list)
    thumbnail_concept: str = ""
    end_screen_suggestion: str = ""
    estimated_duration_minutes: int = 10

    def to_markdown(self) -> str:
        """Return the content as a formatted Markdown document."""
        lines: list[str] = [
            f"# {self.title}",
            "",
            "## 📋 Topic",
            self.topic,
            "",
            "## 📝 Description",
            self.description,
            "",
            "## 🎬 Script",
            "",
            "### Hook (0:00 – 0:30)",
            self.script_hook,
            "",
            "### Intro (0:30 – 1:00)",
            self.script_intro,
            "",
        ]

        for i, section in enumerate(self.script_sections, start=1):
            heading = section.get("heading", f"Section {i}")
            content = section.get("content", "")
            lines += [f"### {heading}", content, ""]

        lines += [
            "### Call to Action",
            self.script_cta,
            "",
            "## 🏷️ Tags",
            ", ".join(self.tags),
            "",
            "## 🖼️ Thumbnail Concept",
            self.thumbnail_concept,
            "",
            "## 📌 End Screen Suggestion",
            self.end_screen_suggestion,
            "",
            f"## ⏱️ Estimated Duration",
            f"{self.estimated_duration_minutes} minutes",
        ]

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "title": self.title,
            "description": self.description,
            "script": {
                "hook": self.script_hook,
                "intro": self.script_intro,
                "sections": self.script_sections,
                "cta": self.script_cta,
            },
            "tags": self.tags,
            "thumbnail_concept": self.thumbnail_concept,
            "end_screen_suggestion": self.end_screen_suggestion,
            "estimated_duration_minutes": self.estimated_duration_minutes,
        }


class ContentGenerator:
    """Generates complete YouTube content packages using OpenAI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", _DEFAULT_MODEL)

        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY in your environment "
                "or pass api_key to ContentGenerator."
            )

        if OpenAI is None:
            raise ImportError(
                "openai package is required. Install it with: pip install openai"
            )

        self._client = OpenAI(api_key=self.api_key)

    def generate(
        self,
        topic: str,
        duration_minutes: int = 10,
    ) -> YouTubeContent:
        """Generate a full YouTube content package for *topic*.

        Args:
            topic: The trending topic to create content about.
            duration_minutes: Target video length in minutes.

        Returns:
            A :class:`YouTubeContent` instance with all generated assets.
        """
        prompt = _CONTENT_PROMPT.format(topic=topic, duration=duration_minutes)

        logger.info("Generating content for topic: %s", topic)

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
        )

        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)

        script = data.get("script", {})
        sections = script.get("sections", [])
        if isinstance(sections, list):
            sections = [
                s if isinstance(s, dict) else {"heading": "", "content": str(s)}
                for s in sections
            ]

        return YouTubeContent(
            topic=topic,
            title=data.get("title", ""),
            description=data.get("description", ""),
            script_hook=script.get("hook", ""),
            script_intro=script.get("intro", ""),
            script_sections=sections,
            script_cta=script.get("cta", ""),
            tags=data.get("tags", []),
            thumbnail_concept=data.get("thumbnail_concept", ""),
            end_screen_suggestion=data.get("end_screen_suggestion", ""),
            estimated_duration_minutes=int(
                data.get("estimated_duration_minutes", duration_minutes)
            ),
        )
