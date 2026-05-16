"""
Utility helpers for the YouTube Content Creator Agent.

Covers:
  - Output file saving (Markdown + JSON)
  - Rich console display helpers
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.content_generator import YouTubeContent

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def slugify(text: str, max_length: int = 60) -> str:
    """Convert *text* into a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = text.strip("-")
    return text[:max_length]


def save_content(content: "YouTubeContent", output_dir: Path = OUTPUT_DIR) -> dict[str, Path]:
    """Persist generated content to Markdown and JSON files.

    Args:
        content: The :class:`~src.content_generator.YouTubeContent` to save.
        output_dir: Directory where files are written (created if absent).

    Returns:
        A mapping of ``{"markdown": Path, "json": Path}``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(content.title or content.topic)
    base_name = f"{timestamp}_{slug}"

    md_path = output_dir / f"{base_name}.md"
    json_path = output_dir / f"{base_name}.json"

    md_path.write_text(content.to_markdown(), encoding="utf-8")
    logger.info("Markdown saved: %s", md_path)

    json_path.write_text(
        json.dumps(content.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("JSON saved: %s", json_path)

    return {"markdown": md_path, "json": json_path}


def display_topic_list(topics: list, console=None) -> None:
    """Print a numbered list of trending topics using Rich (or plain print)."""
    if console is None:
        try:
            from rich.console import Console  # type: ignore
            console = Console()
        except ImportError:
            console = None

    if console:
        from rich.table import Table  # type: ignore

        table = Table(title="🔥 Trending Topics", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Topic", min_width=30)
        table.add_column("Source", style="cyan")

        for t in topics:
            table.add_row(str(t.rank), t.title, t.source)

        console.print(table)
    else:
        print("\n🔥 Trending Topics:")
        for t in topics:
            print(f"  {t.rank:>2}. [{t.source}] {t.title}")
        print()


def display_content_summary(content: "YouTubeContent", paths: dict, console=None) -> None:
    """Print a summary of generated content and saved file paths."""
    if console is None:
        try:
            from rich.console import Console  # type: ignore
            console = Console()
        except ImportError:
            console = None

    md_path = paths.get("markdown", "")
    json_path = paths.get("json", "")

    if console:
        from rich.panel import Panel  # type: ignore
        from rich import box  # type: ignore

        summary = (
            f"[bold green]✅ Content Generated Successfully![/bold green]\n\n"
            f"[bold]Title:[/bold] {content.title}\n"
            f"[bold]Duration:[/bold] ~{content.estimated_duration_minutes} min\n"
            f"[bold]Tags:[/bold] {', '.join(content.tags[:5])}{'...' if len(content.tags) > 5 else ''}\n\n"
            f"[bold]Files saved:[/bold]\n"
            f"  📄 {md_path}\n"
            f"  📦 {json_path}"
        )
        console.print(Panel(summary, title="YouTube Content Creator", box=box.ROUNDED))
    else:
        print("\n✅ Content Generated Successfully!")
        print(f"  Title   : {content.title}")
        print(f"  Duration: ~{content.estimated_duration_minutes} min")
        print(f"  Tags    : {', '.join(content.tags[:5])}")
        print(f"  Markdown: {md_path}")
        print(f"  JSON    : {json_path}\n")
