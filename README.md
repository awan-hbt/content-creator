# 🎬 YouTube AI Content Creator Agent

An AI-powered agent that discovers current **viral/trending topics** and automatically generates complete **YouTube content packages** — including titles, descriptions, full video scripts, tags, and thumbnail concepts.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔥 **Viral Topic Discovery** | Fetches trending topics from **Google Trends** and the **YouTube Data API** in real time |
| 🤖 **AI Content Generation** | Uses **OpenAI GPT** to write engaging titles, descriptions, and full video scripts |
| 📝 **Complete YouTube Package** | Outputs title, SEO description, hook/intro/body/CTA script, tags, thumbnail concept, and end-screen suggestion |
| 💾 **Dual Output Formats** | Saves each content package as both **Markdown** (human-readable) and **JSON** (machine-readable) |
| 🖥️ **Flexible CLI** | Interactive, auto, and custom-topic modes — all via a single command |
| 🌍 **Multi-Country Trends** | Configure trending topics for any supported country (US, GB, IN, …) |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/awan-hbt/content-creator.git
cd content-creator
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env and add your API keys
```

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | Your OpenAI API key — get one at [platform.openai.com](https://platform.openai.com/api-keys) |
| `YOUTUBE_API_KEY` | ⬜ Optional | YouTube Data API key for YouTube trending — get one at [console.cloud.google.com](https://console.cloud.google.com/) |
| `OPENAI_MODEL` | ⬜ Optional | OpenAI model to use (default: `gpt-4o-mini`) |
| `TRENDING_COUNTRY` | ⬜ Optional | Country code for trends (default: `US`) |

### 3. Run the Agent

```bash
# Interactive mode — pick a topic from the trending list
python main.py

# Auto mode — generate content for the top trending topic
python main.py --auto

# Auto mode — generate content for top 3 trending topics
python main.py --auto --count 3

# Custom topic — skip trend fetching
python main.py --topic "Best AI tools 2025"

# 15-minute video, UK trends
python main.py --auto --duration 15 --country GB

# Use GPT-4o for higher quality
python main.py --topic "Morning routine tips" --model gpt-4o
```

---

## 📂 Project Structure

```
content-creator/
├── main.py                     # CLI entry point
├── requirements.txt
├── .env.example                # Environment variable template
├── src/
│   ├── agent.py                # Main AI agent orchestrator
│   ├── trending.py             # Trending topic fetcher (Google Trends + YouTube API)
│   ├── content_generator.py    # OpenAI-powered content generation
│   └── utils.py                # File saving & display helpers
├── output/                     # Generated content (Markdown + JSON)
└── tests/
    ├── test_trending.py
    ├── test_content_generator.py
    └── test_utils.py
```

---

## 📄 Sample Output

For each topic the agent generates a **Markdown** and **JSON** file in `output/`:

```markdown
# 10 Mind-Blowing AI Breakthroughs Changing the World in 2025

## 📋 Topic
Artificial Intelligence breakthroughs 2025

## 📝 Description
Discover the top AI breakthroughs shaping 2025...

## 🎬 Script

### Hook (0:00 – 0:30)
"What if I told you that in the last 6 months, AI has completely
changed how we work, create, and even think?..."

### Intro (0:30 – 1:00)
"Welcome back to the channel! Today we're diving into..."

### Breakthrough #1
...

### Call to Action
"If you found this valuable, hit that like button..."

## 🏷️ Tags
AI, artificial intelligence, 2025, technology, machine learning, ...

## 🖼️ Thumbnail Concept
Bold text "AI CHANGED EVERYTHING" over a split image...

## ⏱️ Estimated Duration
10 minutes
```

---

## 🧪 Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## 🏗️ Architecture

```
main.py (CLI)
    └── YouTubeContentAgent (src/agent.py)
            ├── TrendingFetcher (src/trending.py)
            │       ├── Google Trends  (pytrends)
            │       ├── YouTube Data API  (google-api-python-client)
            │       └── Fallback curated topics
            ├── ContentGenerator (src/content_generator.py)
            │       └── OpenAI Chat Completions API
            └── save_content / display helpers (src/utils.py)
```

### Topic Discovery Flow

1. **Google Trends** (`pytrends`) — fetches today's trending searches
2. **YouTube Trending** (optional) — fetches most popular videos via YouTube Data API
3. **Fallback** — if both APIs are unavailable, uses a curated list of evergreen viral categories
4. Topics are deduplicated and limited to `--max-topics`

### Content Generation Flow

1. The agent passes the topic to OpenAI with a detailed system prompt
2. OpenAI returns a structured JSON payload (enforced via `response_format`)
3. The payload is parsed into a `YouTubeContent` dataclass
4. Content is saved as `.md` and `.json` in `output/`

---

## ⚙️ CLI Reference

```
usage: content-creator [-h] [--topic TOPIC | --auto] [--count N]
                       [--duration MINUTES] [--country CODE]
                       [--max-topics N] [--model MODEL]
                       [--output-dir DIR] [--verbose]

options:
  --topic, -t TOPIC     Generate content for a specific topic
  --auto, -a            Auto mode (no user input required)
  --count, -n N         Topics to process in auto mode (default: 1)
  --duration, -d MIN    Target video duration in minutes (default: 10)
  --country, -c CODE    Country code for trends (default: US)
  --max-topics N        Max trending topics to fetch (default: 10)
  --model, -m MODEL     OpenAI model (default: gpt-4o-mini)
  --output-dir, -o DIR  Output directory (default: ./output)
  --verbose, -v         Enable debug logging
```

---

## 📋 Requirements

- Python 3.10+
- OpenAI API key
- (Optional) YouTube Data API key for YouTube trending data

---

## 📜 License

MIT
