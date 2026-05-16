#!/usr/bin/env python3
"""
YouTube AI Content Creator Agent – CLI entry point.

Usage examples:

    # Interactive mode (pick topic from trending list)
    python main.py

    # Auto mode – generate content for top 3 trending topics
    python main.py --auto --count 3

    # Custom topic
    python main.py --topic "Best AI tools 2025"

    # Set target video duration
    python main.py --topic "Morning routine tips" --duration 15

    # Use a specific OpenAI model
    python main.py --auto --model gpt-4o

    # Override country for trending topics
    python main.py --country GB
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv  # type: ignore

# Load .env file from project root
load_dotenv(Path(__file__).parent / ".env")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="content-creator",
        description="AI Agent that creates YouTube content for viral trending topics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--topic",
        "-t",
        metavar="TOPIC",
        help="Generate content for a specific topic (skips trending fetch).",
    )
    mode.add_argument(
        "--auto",
        "-a",
        action="store_true",
        help="Auto mode: fetch trending topics and generate content without user input.",
    )

    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=1,
        metavar="N",
        help="Number of topics to process in auto mode (default: 1).",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        default=10,
        metavar="MINUTES",
        help="Target video duration in minutes (default: 10).",
    )
    parser.add_argument(
        "--country",
        "-c",
        default="US",
        metavar="CODE",
        help="Country code for trending topics, e.g. US, GB, IN (default: US).",
    )
    parser.add_argument(
        "--max-topics",
        type=int,
        default=10,
        metavar="N",
        help="Maximum number of trending topics to fetch (default: 10).",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        metavar="MODEL",
        help="OpenAI model to use (default: gpt-4o-mini or $OPENAI_MODEL).",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=None,
        metavar="DIR",
        help="Directory to save generated content (default: ./output).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Lazy import after env is loaded
    from src.agent import YouTubeContentAgent

    output_dir = Path(args.output_dir) if args.output_dir else None

    try:
        agent = YouTubeContentAgent(
            model=args.model,
            country=args.country,
            max_topics=args.max_topics,
            video_duration_minutes=args.duration,
            output_dir=output_dir,
        )
    except ValueError as exc:
        print(f"❌ Configuration error: {exc}", file=sys.stderr)
        print(
            "   Set OPENAI_API_KEY in your environment or in a .env file.",
            file=sys.stderr,
        )
        return 1

    try:
        results = agent.run(
            auto=args.auto,
            auto_count=args.count,
            custom_topic=args.topic,
        )
    except KeyboardInterrupt:
        print("\n⏹  Interrupted by user.")
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Unexpected error: {exc}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    if not results:
        print("⚠️  No content was generated.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
