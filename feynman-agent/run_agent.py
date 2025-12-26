import os
import sys
import datetime
import requests
import json
import time
from pathlib import Path
from abc import ABC, abstractmethod
from anthropic import Anthropic
import google.generativeai as genai
from dotenv import load_dotenv

# --- CONFIGURATION ---
# Load API keys from a .env file or environment variables
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Add Gemini Key
READWISE_TOKEN = os.getenv("READWISE_TOKEN")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower() # Default to claude

# PATHS (Update these to match your actual Obsidian path)
# Use env var if set, otherwise default to current directory
vault_env = os.getenv("OBSIDIAN_VAULT_PATH")
OBSIDIAN_VAULT_PATH = Path(vault_env) if vault_env else Path(".")
CONTEXT_FILE = OBSIDIAN_VAULT_PATH / "ActiveProblems.md"
DAILY_NOTE_FOLDER = OBSIDIAN_VAULT_PATH / "Daily Notes" # Adjust format if needed

# --- SETUP CLIENTS ---

class LLMClient(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass

class ClaudeClient(LLMClient):
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-opus-4-5"

    def generate_response(self, prompt: str) -> str:
        # Retry logic could be encapsulated here or reused
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    raise e
        return ""

class GeminiClient(LLMClient):
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
        self.model = genai.GenerativeModel(model_name)

    def generate_response(self, prompt: str) -> str:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    raise e
        return ""
        return ""

def get_llm_client() -> LLMClient:
    if LLM_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found")
        return GeminiClient(GEMINI_API_KEY)
    else:
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found")
        return ClaudeClient(ANTHROPIC_API_KEY)

def get_recent_readwise_docs(hours=24):
    """Fetch articles/highlights updated in the last X hours."""
    print(f"📥 Fetching Readwise docs from the last {hours} hours...")
    
    # Calculate time window
    time_window = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    # time_window = datetime.datetime.now() - datetime.timedelta(days=1)
    iso_date = time_window.isoformat()
    
    try:
        response = requests.get(
            "https://readwise.io/api/v3/list/",
            params={
                "updatedAfter": iso_date,
                "withHtmlContent": "true", # We need full text
                "location": "new"          # Only items in 'Inbox' or 'Later'
            },
            headers={"Authorization": f"Token {READWISE_TOKEN}"},
            timeout=30 # Add timeout
        )
        
        if response.status_code != 200:
            sys.stderr.write(f"Error fetching Readwise: {response.status_code}\n")
            return []
        
        results = response.json().get('results', [])
        print(f"   Found {len(results)} new documents.")
        return results
    except Exception as e:
        sys.stderr.write(f"Exception fetching Readwise: {e}\n")
        return []

def read_context_file():
    """Read the 12 Problems file."""
    if not CONTEXT_FILE.exists():
        sys.stderr.write(f"❌ Error: Context file not found at {CONTEXT_FILE}\n")
        return None
    with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
        return f.read()

def analyze_document(doc, context, client: LLMClient):
    """Send document + context to LLM for Feynman analysis.
    
    Args:
        doc: Document dictionary with title, html_content, etc.
        context: Active problems context string
        client: LLM client instance to use for analysis
    
    Returns:
        Dictionary with insight data if connection found, None otherwise
    """

    title = doc.get('title', 'Untitled')
    content = doc.get('html_content', '') or doc.get('summary', '')

    # Skip if content is too short (likely just a link)
    if len(content) < 500:

        return None

    print(f"🧠 Analyzing: {title}...")

    prompt = f"""
    You are an expert research assistant using the Feynman Technique.
    
    CONTEXT (My Active Problems):
    {context}
    
    INPUT TEXT (New Article):
    Title: {title}
    {content[:15000]}  # Truncate to avoid massive token costs if article is huge
    
    ---
    YOUR TASK:
    Run the Input Text against my Active Problems. Look for high-value connections.
    
    Apply these filters:
    1. THE INVERSION: Does this contradict my current hypothesis?
    2. THE MECHANISM: Is there an abstract mechanism here I can steal?
    3. THE SOLUTION: Does this directly solve a bottleneck?
    
    OUTPUT FORMAT:
    If NO strong connection is found, output exactly: "NO_HIT"
    
    If a connection is found, output a JSON object:
    {{
        "project_name": "Name of the relevant project",
        "insight_type": "Mechanism" or "Contradiction" or "Solution",
        "summary": "One sentence summary of the connection.",
        "actionable_advice": "Specific thing I should do based on this.",
        "source_name": "Name of the article"
    }}
    """
    


    try:
        result_text = client.generate_response(prompt)
    except Exception as e:
        sys.stderr.write(f"Error generating response: {e}\n")
        return None

    # result_text is already obtained via client abstraction
    if not result_text:
        return None
    
    result_text = result_text.strip()
    
    if "NO_HIT" in result_text:
        return None
    
    try:
        # Extract JSON if Claude adds extra text
        start = result_text.find('{')
        end = result_text.rfind('}') + 1
        json_str = result_text[start:end]
        return json.loads(json_str)
    except:
        return None

def append_to_daily_note(hits):
    """Append hits to today's Daily Note."""
    today_str = datetime.datetime.now().strftime("%Y-%m-%d") # Adjust to your vault format
    daily_note_path = DAILY_NOTE_FOLDER / f"{today_str}.md"
    
    # Ensure the daily note folder exists
    DAILY_NOTE_FOLDER.mkdir(parents=True, exist_ok=True)

    # Create daily note if it doesn't exist
    if not daily_note_path.exists():
        with open(daily_note_path, "w", encoding="utf-8") as f:
            f.write(f"# Daily Note {today_str}\n\n")

    with open(daily_note_path, "a", encoding="utf-8") as f:
        f.write("\n\n## 🎯 Feynman Hits\n")
        for hit in hits:
            f.write(f"### Match: {hit['project_name']}\n")
            f.write(f"> **{hit['insight_type']}**: {hit['summary']}\n\n")
            f.write(f"👉 **Action:** {hit['actionable_advice']}\n")
            f.write(f"🔗 [{hit['source_name']}]({hit['source_url']})\n\n")
            f.write("---\n")
    
    print(f"✅ Added {len(hits)} hits to {daily_note_path}")

def main():
    # Fail fast if client configuration is invalid and create client once
    try:
        client = get_llm_client()
    except Exception as e:
        sys.stderr.write(f"Configuration Error: {e}\n")
        return

    context = read_context_file()
    if not context:
        sys.stderr.write("Missing context file. Exiting.\n")
        return

    docs = get_recent_readwise_docs(hours=24)

    hits = []

    for i, doc in enumerate(docs):
        try:
            # Add delay between requests to avoid rate limiting
            if i > 0:
                delay = 1.0  # 1 second delay between documents
                time.sleep(delay)
            
            insight = analyze_document(doc, context, client)
            if insight:
                insight['source_url'] = doc.get('source_url', '#')
                hits.append(insight)
                print(f"   🔥 HIT FOUND: {insight['project_name']}")
            else:
                print("   (No hit)")
        except Exception as e:
            sys.stderr.write(f"Error processing document '{doc.get('title', 'Unknown')}': {e}\n")
            continue

    if hits:
        append_to_daily_note(hits)
    else:
        print("No hits found today.")

if __name__ == "__main__":
    main()