# Quick Reference Guide

A cheat sheet for common tasks and configurations in the Feynman Agent.

## Environment Variables

```env
# Required
LLM_PROVIDER=claude|gemini
ANTHROPIC_API_KEY=sk-...          # If using Claude
GEMINI_API_KEY=...                 # If using Gemini
READWISE_TOKEN=...                 # Your Readwise API token

# Optional
GEMINI_MODEL=gemini-3-pro-preview  # Gemini model name
OBSIDIAN_VAULT_PATH=/path/to/vault # Default: current directory
```

## File Locations

| File | Default Location | Purpose |
|------|-----------------|---------|
| `ActiveProblems.md` | `{VAULT}/ActiveProblems.md` | Your research problems (context) |
| Daily Notes | `{VAULT}/Daily Notes/YYYY-MM-DD.md` | Generated insights |
| `.env` | Project root | Configuration |
| Logs | `logs/error.log` | Error messages |

## Common Commands

```bash
# Run the agent
python run_agent.py

# Install dependencies
pip install -r requirements.txt

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

## Code Locations

| Task | File | Function/Line |
|------|------|---------------|
| Change time window | `run_agent.py` | `main()`, line 234 |
| Modify prompt | `run_agent.py` | `analyze_document()`, line 138 |
| Change output format | `run_agent.py` | `append_to_daily_note()`, line 210 |
| Add LLM provider | `run_agent.py` | `get_llm_client()`, line 75 |
| Adjust rate limiting | `run_agent.py` | `main()`, line 242 |

## Configuration Values

| Setting | Default | Location |
|---------|---------|----------|
| Time window | 24 hours | `get_recent_readwise_docs(hours=24)` |
| Content truncation | 15,000 chars | `analyze_document()`, line 146 |
| Min content length | 500 chars | `analyze_document()`, line 132 |
| Rate limit delay | 1.0 seconds | `main()`, line 242 |
| Max retries (Claude) | 3 | `ClaudeClient`, line 42 |
| Retry delay | 2 seconds | `ClaudeClient`, line 43 |

## Output Format

Insights are written to daily notes as:

```markdown
## 🎯 Feynman Hits
### Match: {project_name}
> **{insight_type}**: {summary}

👉 **Action:** {actionable_advice}
🔗 [{source_name}]({source_url})

---
```

## Insight Types

- **Mechanism**: Abstract pattern you can apply elsewhere
- **Contradiction**: Challenges your current hypothesis
- **Solution**: Directly solves a bottleneck

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key not found" | Check `.env` file exists and has correct keys |
| "Context file not found" | Create `ActiveProblems.md` or set `OBSIDIAN_VAULT_PATH` |
| "504 Deadline Exceeded" | Network/API issue, will retry automatically |
| No insights found | Normal if no strong connections exist |
| JSON parsing errors | Check LLM response format, improve extraction logic |

## Adding Features

### New LLM Provider
1. Create class inheriting from `LLMClient`
2. Implement `generate_response()` method
3. Update `get_llm_client()` factory

### New Data Source
1. Create fetch function (like `get_recent_readwise_docs()`)
2. Integrate into `main()` function
3. Ensure data format matches expected structure

### New Analysis Filter
1. Add filter to prompt in `analyze_document()`
2. Update `insight_type` in JSON schema
3. Update output formatting if needed

## Testing

```python
# Test with single article
docs = [{'title': 'Test', 'html_content': '...', 'source_url': '...'}]

# Debug mode (add to .env)
DEBUG=true

# Check logs
tail -f logs/error.log
```

## Project Structure

```
feynman-agent/
├── run_agent.py          # Main script
├── ActiveProblems.md     # Context file
├── Daily Notes/          # Output directory
├── logs/                 # Log files
├── .env                  # Configuration (gitignored)
├── requirements.txt      # Dependencies
└── docs/
    ├── README.md         # Overview and setup
    ├── ARCHITECTURE.md   # Code structure
    ├── DEVELOPMENT.md    # Development guide
    └── QUICK_REFERENCE.md # This file
```

## Links

- [Full README](README.md)
- [Architecture Details](ARCHITECTURE.md)
- [Development Guide](DEVELOPMENT.md)

