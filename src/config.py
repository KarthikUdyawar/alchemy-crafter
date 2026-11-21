import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/alchemy"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # Redis TTL (seconds) — 24 hours
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "86400"))

    # Context window for AI prompts
    CONTEXT_SIZE: int = int(os.getenv("CONTEXT_SIZE", "10"))

    # Ollama request timeout (seconds)
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "100"))

    # Validation
    MAX_ELEMENT_LENGTH: int = 30


config = Config()
