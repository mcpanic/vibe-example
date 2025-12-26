# Architecture Documentation

This document describes the code structure, design patterns, and key components of the Feynman Agent.

## Code Structure

```
run_agent.py
├── Configuration Section (lines 13-26)
│   ├── Environment variable loading
│   └── Path configuration
├── LLM Client Abstraction (lines 30-83)
│   ├── LLMClient (abstract base class)
│   ├── ClaudeClient (implementation)
│   ├── GeminiClient (implementation)
│   └── get_llm_client() (factory function)
├── Readwise Integration (lines 85-115)
│   └── get_recent_readwise_docs()
├── Context Management (lines 117-123)
│   └── read_context_file()
├── Analysis Engine (lines 125-195)
│   └── analyze_document()
└── Output Management (lines 197-219)
    └── append_to_daily_note()
```

## Design Patterns

### 1. Strategy Pattern: LLM Client Abstraction

The code uses an abstract base class (`LLMClient`) to support multiple LLM providers:

```python
class LLMClient(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass
```

**Benefits:**
- Easy to add new LLM providers (OpenAI, Cohere, etc.)
- Consistent interface across providers
- Testable with mock implementations

**Current Implementations:**
- `ClaudeClient`: Uses Anthropic API with retry logic
- `GeminiClient`: Uses Google Generative AI SDK

**Adding a New Provider:**
1. Create a new class inheriting from `LLMClient`
2. Implement `generate_response()` method
3. Update `get_llm_client()` factory function

### 2. Factory Pattern: LLM Client Selection

The `get_llm_client()` function acts as a factory, selecting the appropriate client based on configuration:

```python
def get_llm_client() -> LLMClient:
    if LLM_PROVIDER == "gemini":
        return GeminiClient(GEMINI_API_KEY)
    else:
        return ClaudeClient(ANTHROPIC_API_KEY)
```

**Benefits:**
- Centralized client creation
- Configuration-driven selection
- Early validation of API keys

### 3. Error Handling Strategy

**Retry Logic (ClaudeClient):**
- Exponential backoff: `2 ** attempt` seconds
- Maximum 3 retries
- Re-raises exception on final failure

**Graceful Degradation:**
- Missing context file: Exits early with error message
- API failures: Logs error, continues to next document
- Invalid JSON: Returns `None`, skips document

## Key Components

### 1. Configuration Management

**Location:** Lines 13-26

**Responsibilities:**
- Load environment variables from `.env` file
- Set default values
- Configure file paths

**Key Variables:**
- `LLM_PROVIDER`: Determines which LLM to use
- `OBSIDIAN_VAULT_PATH`: Base path for notes (defaults to current directory)
- `CONTEXT_FILE`: Path to `ActiveProblems.md`
- `DAILY_NOTE_FOLDER`: Path to daily notes directory

### 2. LLM Clients

#### ClaudeClient

**Features:**
- Model: `claude-opus-4-5` (hardcoded)
- Retry logic with exponential backoff
- Temperature: 0 (deterministic)
- Max tokens: 1000

**Error Handling:**
- Catches exceptions and retries up to 3 times
- Exponential backoff: 2s, 4s, 8s

#### GeminiClient

**Features:**
- Model: Configurable via `GEMINI_MODEL` env var (default: `gemini-3-pro-preview`)
- No retry logic (could be added)
- Simple error handling

**Improvement Opportunity:**
- Add retry logic similar to ClaudeClient
- Add timeout configuration

### 3. Readwise Integration

**Function:** `get_recent_readwise_docs(hours=24)`

**API Endpoint:** `https://readwise.io/api/v3/list/`

**Parameters:**
- `updatedAfter`: ISO timestamp (last N hours)
- `withHtmlContent`: `true` (needed for full text)
- `location`: `"new"` (only items in Inbox/Later)

**Error Handling:**
- Returns empty list on failure
- Logs errors to stderr
- 30-second timeout

**Improvement Opportunities:**
- Pagination support (currently only gets first page)
- Configurable time window
- Filter by tags or categories

### 4. Analysis Engine

**Function:** `analyze_document(doc, context)`

**Process:**
1. Extract title and content from document
2. Skip if content < 500 characters (likely just a link)
3. Truncate content to 15,000 characters (token cost control)
4. Build prompt with context and article
5. Call LLM with Feynman Technique prompt
6. Parse JSON response or return `None` if "NO_HIT"

**Prompt Structure:**
- Context: Active problems from `ActiveProblems.md`
- Input: Article title and content
- Task: Apply three filters (Inversion, Mechanism, Solution)
- Output: JSON object or "NO_HIT"

**Response Format:**
```json
{
    "project_name": "Name of the relevant project",
    "insight_type": "Mechanism" | "Contradiction" | "Solution",
    "summary": "One sentence summary",
    "actionable_advice": "Specific thing to do",
    "source_name": "Name of the article"
}
```

**Improvement Opportunities:**
- Streaming responses for long articles
- Better JSON extraction (handle markdown code blocks)
- Confidence scoring
- Multi-pass analysis for complex articles

### 5. Output Management

**Function:** `append_to_daily_note(hits)`

**Process:**
1. Generate filename: `YYYY-MM-DD.md`
2. Create daily note folder if missing
3. Create daily note file if missing (with header)
4. Append "Feynman Hits" section with all insights

**Format:**
- Markdown with emoji indicators
- Links to source articles
- Separators between hits

**Improvement Opportunities:**
- Deduplication (check if insight already exists)
- Sorting by relevance or project
- Template customization
- Backlinks to ActiveProblems.md

## Data Flow

```
1. main()
   │
   ├─> get_llm_client() ──> Validates configuration
   │
   ├─> read_context_file() ──> Reads ActiveProblems.md
   │
   ├─> get_recent_readwise_docs() ──> Fetches articles from Readwise API
   │
   └─> For each document:
       │
       ├─> analyze_document()
       │   ├─> Extracts title/content
       │   ├─> Builds prompt
       │   ├─> Calls LLM client
       │   └─> Parses JSON response
       │
       └─> If insight found:
           └─> Adds to hits list
   
   └─> append_to_daily_note(hits) ──> Writes to daily note file
```

## Dependencies

### Core Libraries
- `anthropic`: Anthropic API client for Claude
- `google.generativeai`: Google Generative AI SDK for Gemini
- `python-dotenv`: Environment variable management
- `requests`: HTTP client for Readwise API

### Standard Library
- `os`, `sys`: System operations
- `datetime`: Date/time handling
- `json`: JSON parsing
- `time`: Sleep for rate limiting
- `pathlib`: Path manipulation
- `abc`: Abstract base classes

## Configuration Points

### Easy to Modify
- **Time window**: Change `hours=24` in `get_recent_readwise_docs()` call
- **Content truncation**: Change `15000` in `analyze_document()`
- **Min content length**: Change `500` in `analyze_document()`
- **Rate limiting delay**: Change `delay = 1.0` in `main()`
- **Model selection**: Change `self.model` in `ClaudeClient` or `GEMINI_MODEL` env var

### Requires Code Changes
- **Prompt structure**: Modify prompt string in `analyze_document()`
- **Output format**: Modify `append_to_daily_note()` formatting
- **New LLM provider**: Add new client class and update factory
- **New data source**: Add new fetch function and integrate into `main()`

## Testing Considerations

### Unit Test Targets
- `get_llm_client()`: Factory function with different configurations
- `read_context_file()`: File reading and error handling
- `analyze_document()`: Prompt building and JSON parsing
- `append_to_daily_note()`: File creation and formatting

### Integration Test Targets
- Readwise API integration (with mock responses)
- LLM client calls (with mock responses)
- End-to-end workflow (with test data)

### Mock Requirements
- Mock `requests.get()` for Readwise API
- Mock LLM client responses
- Mock file system operations

## Performance Characteristics

### Current Limitations
- **Sequential processing**: Documents analyzed one at a time
- **No caching**: Same article analyzed every run
- **No pagination**: Only first page of Readwise results
- **Synchronous**: No async/await for I/O operations

### Optimization Opportunities
- **Parallel processing**: Analyze multiple documents concurrently
- **Caching**: Store analyzed document IDs to skip repeats
- **Streaming**: Stream LLM responses for better UX
- **Async I/O**: Use `aiohttp` and async LLM clients

## Security Considerations

### Current State
- API keys stored in `.env` file (not in git)
- No encryption of stored data
- No authentication for file access

### Recommendations
- Add `.env` to `.gitignore` (if not already)
- Consider using secret management service for production
- Validate file paths to prevent directory traversal
- Add input sanitization for file content

