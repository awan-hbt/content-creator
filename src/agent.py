"""
YouTube Content Creator AI Agent.

Orchestrates the full pipeline:
  1. Fetch trending/viral topics
  2. Let the user (or auto-mode) pick a topic
  3. Generate complete YouTube content via OpenAI
  4. Save output to disk
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from src.trending import TrendingFetcher, TrendingTopic
from src.content_generator import ContentGenerator, YouTubeContent
from src.utils import save_content, display_topic_list, display_content_summary, OUTPUT_DIR

logger = logging.getLogger(__name__)


class YouTubeContentAgent:
    """End-to-end AI agent for YouTube content creation on viral topics.

    Usage::

        agent = YouTubeContentAgent()
        # Interactive mode – user picks a topic
        agent.run()

        # Auto mode – generate content for the top N trending topics
        agent.run(auto=True, auto_count=3)

        # Custom topic
        agent.run(custom_topic="Electric vehicles 2025")
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        youtube_api_key: Optional[str] = None,
        model: Optional[str] = None,
        country: str = "US",
        max_topics: int = 10,
        video_duration_minutes: int = 10,
        output_dir: Optional[Path] = None,
    ) -> None:
        self.video_duration_minutes = video_duration_minutes
        self.output_dir = output_dir or OUTPUT_DIR

        self.fetcher = TrendingFetcher(
            youtube_api_key=youtube_api_key,
            country=country,
            max_topics=max_topics,
        )
        self.generator = ContentGenerator(
            api_key=openai_api_key,
            model=model,
        )

        try:
            from rich.console import Console  # type: ignore
            self._console = Console()
        except ImportError:
            self._console = None  # type: ignore

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        auto: bool = False,
        auto_count: int = 1,
        custom_topic: Optional[str] = None,
    ) -> list[YouTubeContent]:
        """Run the agent and return generated content objects.

        Args:
            auto: If ``True``, automatically generate content for the
                  top *auto_count* trending topics without user input.
            auto_count: Number of topics to process in auto mode.
            custom_topic: Skip trend fetching and use this topic directly.

        Returns:
            List of :class:`~src.content_generator.YouTubeContent` objects.
        """
        results: list[YouTubeContent] = []

        if custom_topic:
            topics = [TrendingTopic(title=custom_topic, source="Custom", rank=1)]
        else:
            self._print("🔍 Fetching trending topics…")
            topics = self.fetcher.fetch()
            if not topics:
                self._print("⚠️  No trending topics found. Exiting.")
                return results
            display_topic_list(topics, console=self._console)

        if custom_topic or auto:
            selected = topics[:auto_count]
        else:
            selected = self._interactive_select(topics)

        for topic in selected:
            self._print(f"\n⚙️  Generating content for: [bold]{topic.title}[/bold]")
            content = self.generator.generate(
                topic=topic.title,
                duration_minutes=self.video_duration_minutes,
            )
            paths = save_content(content, output_dir=self.output_dir)
            display_content_summary(content, paths, console=self._console)
            results.append(content)

        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print(self, message: str) -> None:
        """Print using Rich if available, else plain print."""
        if self._console:
            self._console.print(message)
        else:
            # Strip simple rich markup for plain output
            import re
            plain = re.sub(r"\[/?[^\]]+\]", "", message)
            print(plain)

    def _interactive_select(
        self, topics: list[TrendingTopic]
    ) -> list[TrendingTopic]:
        """Prompt the user to pick one or more topics interactively."""
        print("\nEnter the number(s) of the topic(s) you want to create content for.")
        print("Separate multiple choices with commas (e.g. 1,3,5). Press Enter for topic #1.\n")

        raw = input("Your choice: ").strip()
        if not raw:
            return [topics[0]]

        selected: list[TrendingTopic] = []
        for part in raw.split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(topics):
                    selected.append(topics[idx])
                else:
                    print(f"  ⚠️  Ignoring out-of-range choice: {part}")
            else:
                print(f"  ⚠️  Ignoring invalid choice: {part}")

        return selected or [topics[0]]
