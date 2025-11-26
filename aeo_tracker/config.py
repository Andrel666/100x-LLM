"""
AEO Tracker Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "aeo_tracker.db"

# LLM API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# LLM Models Configuration
LLM_MODELS = {
    "chatgpt": {
        "provider": "openai",
        "model": "gpt-4o",
        "display_name": "ChatGPT (GPT-4o)"
    },
    "claude": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "display_name": "Claude (Sonnet)"
    },
    "gemini": {
        "provider": "google",
        "model": "gemini-1.5-flash",
        "display_name": "Gemini 1.5 Flash"
    }
}

# Content Types for tracking
CONTENT_TYPES = [
    "YouTube Video",
    "Reddit Answer",
    "Quora Answer",
    "StackOverflow Answer",
    "LinkedIn Post",
    "TikTok Video",
    "Instagram Post",
    "Landing Page",
    "Use Case Page",
    "Template Page",
    "Help Center Article",
    "Integration Page",
    "Blog Post",
    "Product Hunt Launch",
    "Affiliate List",
    "Press Release",
    "Other"
]

# Experiment settings
DEFAULT_CONTROL_PERIOD_DAYS = 14
DEFAULT_TEST_PERIOD_DAYS = 28

# Visibility scoring
VISIBILITY_SCORES = {
    "featured": 100,      # Brand is prominently featured/recommended
    "mentioned": 70,      # Brand is mentioned positively
    "listed": 40,         # Brand appears in a list
    "cited_source": 30,   # Brand's content is cited as source
    "not_found": 0        # Brand doesn't appear
}
