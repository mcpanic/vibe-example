# Feynman Agent

An AI-powered research assistant that uses the Feynman Technique to analyze articles from Readwise and connect them to your active research problems. The agent automatically identifies high-value insights (mechanisms, contradictions, solutions) and appends them to your daily notes.

## Overview

The Feynman Agent implements a workflow inspired by Richard Feynman's learning technique:
1. **Fetches** recent articles from Readwise (last 24 hours)
2. **Analyzes** each article against your active problems using an LLM
3. **Filters** for three types of insights:
   - **The Inversion**: Contradictions to your current hypotheses
   - **The Mechanism**: Abstract mechanisms you can apply elsewhere
   - **The Solution**: Direct solutions to bottlenecks
4. **Appends** insights to your daily notes in Obsidian format

## Features

- **Multi-LLM Support**: Works with Claude (Anthropic) or Gemini (Google)
- **Readwise Integration**: Automatically fetches recent articles and highlights
- **Feynman Technique**: Applies structured analysis filters to find high-value connections
- **Daily Notes Integration**: Appends insights to date-stamped markdown files
- **Retry Logic**: Handles API failures gracefully with exponential backoff
- **Rate Limiting**: Built-in delays to avoid API rate limits

## Prerequisites

- Python 3.13+ (or compatible version)
- Readwise account with API access
- Anthropic API key (for Claude) or Google API key (for Gemini)
- Obsidian vault (or any markdown-based note system)

## Installation

1. **Clone or navigate to the repository:**
   ```bash
   cd feynman-agent
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install anthropic google-generativeai python-dotenv requests
   ```

4. **Create a `.env` file** in the project root:
   ```env
   # Required: Choose one LLM provider
   LLM_PROVIDER=claude  # or "gemini"
   
   # Required for Claude
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   
   # Required for Gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3-pro-preview  # Optional, defaults to gemini-3-pro-preview
   
   # Required: Readwise API token
   READWISE_TOKEN=your_readwise_token_here
   
   # Optional: Path to your Obsidian vault (defaults to current directory)
   OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
   ```

5. **Set up your context file:**
   - Create or update `ActiveProblems.md` in your vault root
   - List your active research problems (see `ActiveProblems.md` for format)

## Usage

Run the agent:
```bash
python run_agent.py
```

The agent will:
1. Read your `ActiveProblems.md` file
2. Fetch articles from Readwise updated in the last 24 hours
3. Analyze each article for connections to your problems
4. Append any insights found to today's daily note (e.g., `Daily Notes/2025-12-26.md`)

### Output Format

Insights are appended to your daily note in this format:
```markdown
## 🎯 Feynman Hits
### Match: Project Name
> **Mechanism**: Summary of the connection

👉 **Action:** Specific actionable advice
🔗 [Article Title](url)

---
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | No | `claude` | LLM provider: `claude` or `gemini` |
| `ANTHROPIC_API_KEY` | Yes* | - | API key for Claude |
| `GEMINI_API_KEY` | Yes* | - | API key for Gemini |
| `GEMINI_MODEL` | No | `gemini-3-pro-preview` | Gemini model name |
| `READWISE_TOKEN` | Yes | - | Readwise API token |
| `OBSIDIAN_VAULT_PATH` | No | `.` | Path to Obsidian vault |

*Required based on `LLM_PROVIDER` selection

### File Structure

```
feynman-agent/
├── run_agent.py          # Main script
├── ActiveProblems.md     # Your active research problems (context)
├── Daily Notes/          # Generated daily notes
│   └── YYYY-MM-DD.md
├── logs/                 # Error and output logs
├── .env                  # Environment variables (not in git)
└── venv/                 # Virtual environment
```

## Troubleshooting

### Common Issues

1. **"Configuration Error: API key not found"**
   - Ensure your `.env` file exists and contains the correct API keys
   - Check that `LLM_PROVIDER` matches the API key you've provided

2. **"Context file not found"**
   - Create `ActiveProblems.md` in your vault root
   - Or set `OBSIDIAN_VAULT_PATH` to point to the correct directory

3. **"504 Deadline Exceeded" errors**
   - The LLM API timed out. The agent includes retry logic, but persistent errors may indicate:
     - Network issues
     - API rate limits
     - Very long articles (content is truncated to 15,000 chars)

4. **No hits found**
   - This is normal! The agent only reports strong connections
   - Check that your `ActiveProblems.md` contains relevant problems
   - Verify that Readwise has recent articles in the "new" location

## How It Works

The agent uses a three-step filtering process inspired by the Feynman Technique:

1. **The Inversion**: Does this contradict my current hypothesis?
2. **The Mechanism**: Is there an abstract mechanism here I can steal?
3. **The Solution**: Does this directly solve a bottleneck?

Each article is analyzed against your active problems, and only articles with strong connections are saved to your daily notes.

## Next Steps

- See [ARCHITECTURE.md](ARCHITECTURE.md) for code structure and design patterns
- See [DEVELOPMENT.md](DEVELOPMENT.md) for how to maintain and extend the codebase

