# Development Guide

This guide helps you maintain, improve, and add features to the Feynman Agent codebase.

## Table of Contents

- [Getting Started](#getting-started)
- [Code Style](#code-style)
- [Adding Features](#adding-features)
- [Common Tasks](#common-tasks)
- [Debugging](#debugging)
- [Testing](#testing)
- [Contributing](#contributing)

## Getting Started

### Development Environment Setup

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install development dependencies** (if needed):
   ```bash
   pip install pytest pytest-mock black flake8 mypy
   ```

3. **Verify configuration:**
   - Check `.env` file exists with all required keys
   - Verify `ActiveProblems.md` exists and has content
   - Test Readwise API connection

### Running in Development Mode

Add debug output:
```python
# In main(), add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Code Style

### Python Style Guide

Follow PEP 8 conventions:
- Use 4 spaces for indentation
- Maximum line length: 100 characters (current code uses ~120, consider refactoring)
- Use descriptive variable names
- Add docstrings to all functions

### Current Conventions

- **Function names**: `snake_case`
- **Class names**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **File organization**: Functions grouped by responsibility

### Example Function Structure

```python
def function_name(param1: str, param2: int = 0) -> dict:
    """
    Brief description of what the function does.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When something goes wrong
    """
    # Implementation
    pass
```

## Adding Features

### 1. Adding a New LLM Provider

**Step 1:** Create a new client class in `run_agent.py`:

```python
class OpenAIClient(LLMClient):
    def __init__(self, api_key):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4"
    
    def generate_response(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise e
```

**Step 2:** Update the factory function:

```python
def get_llm_client() -> LLMClient:
    if LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found")
        return OpenAIClient(OPENAI_API_KEY)
    elif LLM_PROVIDER == "gemini":
        # ... existing code
    else:
        # ... existing code
```

**Step 3:** Add environment variable to `.env.example`:
```env
OPENAI_API_KEY=your_key_here
```

### 2. Adding a New Data Source

**Example: Adding RSS feed support:**

```python
def get_rss_articles(feed_url: str, hours: int = 24):
    """Fetch articles from RSS feed updated in last N hours."""
    import feedparser
    from datetime import datetime, timedelta
    
    feed = feedparser.parse(feed_url)
    cutoff = datetime.now() - timedelta(hours=hours)
    
    articles = []
    for entry in feed.entries:
        pub_date = datetime(*entry.published_parsed[:6])
        if pub_date > cutoff:
            articles.append({
                'title': entry.title,
                'html_content': entry.summary,
                'source_url': entry.link
            })
    
    return articles
```

**Then integrate into `main()`:**
```python
# In main(), after get_recent_readwise_docs():
rss_articles = get_rss_articles("https://example.com/feed.xml", hours=24)
docs.extend(rss_articles)  # Combine with Readwise docs
```

### 3. Adding New Analysis Filters

**Modify the prompt in `analyze_document()`:**

```python
prompt = f"""
    ...
    Apply these filters:
    1. THE INVERSION: Does this contradict my current hypothesis?
    2. THE MECHANISM: Is there an abstract mechanism here I can steal?
    3. THE SOLUTION: Does this directly solve a bottleneck?
    4. THE ANALOGY: Can I map this to an unrelated domain?  # NEW
    ...
    "insight_type": "Mechanism" or "Contradiction" or "Solution" or "Analogy",  # UPDATE
    ...
"""
```

**Update JSON parsing if needed** (insight_type validation).

### 4. Adding Caching

**Add a simple file-based cache:**

```python
import hashlib
import json
from pathlib import Path

CACHE_FILE = Path("cache.json")

def get_doc_hash(doc):
    """Generate hash for document to use as cache key."""
    content = f"{doc.get('title', '')}{doc.get('source_url', '')}"
    return hashlib.md5(content.encode()).hexdigest()

def load_cache():
    """Load cache from file."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Save cache to file."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

# In analyze_document():
cache = load_cache()
doc_hash = get_doc_hash(doc)
if doc_hash in cache:
    return cache[doc_hash]  # Return cached result

# ... existing analysis ...

if insight:
    cache[doc_hash] = insight
    save_cache(cache)
```

### 5. Adding Parallel Processing

**Use `concurrent.futures` for parallel analysis:**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

# In main(), replace the for loop:
with ThreadPoolExecutor(max_workers=3) as executor:
    future_to_doc = {
        executor.submit(analyze_document, doc, context): doc 
        for doc in docs
    }
    
    for future in as_completed(future_to_doc):
        doc = future_to_doc[future]
        try:
            insight = future.result()
            if insight:
                insight['source_url'] = doc.get('source_url', '#')
                hits.append(insight)
        except Exception as e:
            sys.stderr.write(f"Error processing '{doc.get('title')}': {e}\n")
```

**Note:** Be careful with rate limits when parallelizing API calls.

## Common Tasks

### Updating the Prompt

**Location:** `analyze_document()` function, lines 138-168

**Tips:**
- Keep the three-filter structure (Inversion, Mechanism, Solution)
- Test with sample articles to ensure output format is consistent
- Consider adding examples in the prompt for few-shot learning

### Changing the Time Window

**Location:** `main()` function, line 234

```python
# Change from 24 hours to 48 hours:
docs = get_recent_readwise_docs(hours=48)
```

### Modifying Output Format

**Location:** `append_to_daily_note()` function, lines 210-217

**Example: Add priority field:**
```python
f.write(f"### Match: {hit['project_name']} (Priority: {hit.get('priority', 'medium')})\n")
```

### Adding Logging

**Replace `print()` and `sys.stderr.write()` with proper logging:**

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Replace print() with:
logger.info(f"📥 Fetching Readwise docs...")

# Replace sys.stderr.write() with:
logger.error(f"Error: {e}")
```

## Debugging

### Common Issues and Solutions

#### 1. API Timeout Errors

**Symptom:** `504 Deadline Exceeded` in error log

**Solutions:**
- Increase timeout in API client (if supported)
- Reduce content truncation limit (currently 15,000 chars)
- Add longer delays between requests
- Check network connectivity

#### 2. JSON Parsing Errors

**Symptom:** `analyze_document()` returns `None` even when LLM responds

**Debug:**
```python
# In analyze_document(), before JSON parsing:
print(f"Raw response: {result_text}")  # See what LLM actually returned
```

**Solutions:**
- Improve JSON extraction logic (handle markdown code blocks)
- Add prompt instruction: "Output ONLY valid JSON, no markdown"
- Use structured output if LLM supports it

#### 3. No Insights Found

**Debug:**
- Check that `ActiveProblems.md` has relevant content
- Verify Readwise has articles in "new" location
- Test prompt manually with a known-good article
- Check LLM response for "NO_HIT" vs actual JSON

#### 4. File Path Issues

**Symptom:** "Context file not found" or daily notes not created

**Debug:**
```python
# Add debug output:
print(f"Vault path: {OBSIDIAN_VAULT_PATH}")
print(f"Context file: {CONTEXT_FILE}")
print(f"Context exists: {CONTEXT_FILE.exists()}")
```

**Solutions:**
- Set `OBSIDIAN_VAULT_PATH` in `.env`
- Use absolute paths
- Check file permissions

### Debug Mode

Add a debug flag:
```python
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# In analyze_document():
if DEBUG:
    print(f"Analyzing: {title}")
    print(f"Content length: {len(content)}")
    print(f"Prompt length: {len(prompt)}")
```

## Testing

### Manual Testing

1. **Test with a single article:**
   ```python
   # Temporarily modify main():
   docs = [{
       'title': 'Test Article',
       'html_content': 'Your test content here...',
       'source_url': 'https://example.com'
   }]
   ```

2. **Test prompt directly:**
   - Copy prompt from `analyze_document()`
   - Paste into LLM playground
   - Verify output format

3. **Test file operations:**
   - Manually create test `ActiveProblems.md`
   - Run agent and verify daily note creation

### Unit Testing (Future)

Create `test_run_agent.py`:

```python
import pytest
from unittest.mock import Mock, patch
from run_agent import analyze_document, get_llm_client

def test_analyze_document_no_hit():
    doc = {'title': 'Test', 'html_content': 'Short content'}
    context = "Test context"
    
    with patch('run_agent.get_llm_client') as mock_client:
        mock_client.return_value.generate_response.return_value = "NO_HIT"
        result = analyze_document(doc, context)
        assert result is None

def test_analyze_document_with_hit():
    doc = {'title': 'Test', 'html_content': 'Long content ' * 100}
    context = "Test context"
    json_response = '{"project_name": "Test", "insight_type": "Mechanism", ...}'
    
    with patch('run_agent.get_llm_client') as mock_client:
        mock_client.return_value.generate_response.return_value = json_response
        result = analyze_document(doc, context)
        assert result is not None
        assert result['project_name'] == "Test"
```

## Code Quality Improvements

### Refactoring Opportunities

1. **Extract configuration to a class:**
   ```python
   class Config:
       def __init__(self):
           load_dotenv()
           self.llm_provider = os.getenv("LLM_PROVIDER", "claude")
           # ... etc
   ```

2. **Separate concerns into modules:**
   - `llm_clients.py`: All LLM client classes
   - `readwise.py`: Readwise integration
   - `analysis.py`: Analysis engine
   - `output.py`: Daily note writing

3. **Add type hints everywhere:**
   ```python
   from typing import Optional, List, Dict, Any
   
   def analyze_document(
       doc: Dict[str, Any], 
       context: str
   ) -> Optional[Dict[str, str]]:
       ...
   ```

4. **Add input validation:**
   ```python
   def analyze_document(doc, context):
       if not isinstance(doc, dict):
           raise TypeError("doc must be a dictionary")
       if 'title' not in doc:
           raise ValueError("doc must have 'title' key")
       # ... rest of function
   ```

### Performance Optimizations

1. **Add request batching** for Readwise API
2. **Implement caching** to avoid re-analyzing same articles
3. **Use async/await** for I/O operations
4. **Add progress bar** for long-running analyses

## Contributing

### Before Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Test your changes:**
   - Run the agent with test data
   - Verify output format
   - Check error handling

3. **Update documentation:**
   - Update README.md if adding features
   - Update ARCHITECTURE.md if changing structure
   - Update this file if adding new development patterns

### Code Review Checklist

- [ ] Code follows existing style conventions
- [ ] Functions have docstrings
- [ ] Error handling is appropriate
- [ ] No hardcoded values (use config/env vars)
- [ ] Documentation updated
- [ ] Tested manually

## Future Enhancements

### High Priority
- [ ] Add proper logging system
- [ ] Implement caching to avoid duplicate analysis
- [ ] Add unit tests
- [ ] Improve error messages

### Medium Priority
- [ ] Support for multiple data sources (RSS, Pocket, etc.)
- [ ] Parallel processing for faster analysis
- [ ] Configurable prompt templates
- [ ] Backlinks from daily notes to ActiveProblems.md

### Low Priority
- [ ] Web UI for configuration
- [ ] Scheduled runs (cron integration)
- [ ] Email notifications for high-value insights
- [ ] Export to other note systems (Notion, Roam, etc.)

