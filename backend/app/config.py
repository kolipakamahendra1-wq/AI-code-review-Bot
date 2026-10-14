import os

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # ollama | openai | anthropic | rules
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:3b")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GITHUB_API = os.getenv("GITHUB_API", "https://api.github.com")

DB_PATH = os.getenv("DB_PATH", "data/reviews.db")
FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")

MAX_FILES = int(os.getenv("MAX_FILES", "20"))
MAX_DIFF_CHARS = int(os.getenv("MAX_DIFF_CHARS", "6000"))  # per-file prompt budget
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "180"))
ENABLE_RULES = os.getenv("ENABLE_RULES", "true").lower() == "true"
