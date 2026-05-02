import os
from dataclasses import dataclass

@dataclass
class Config:
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    MAX_CHAIN_STEPS: int = 15
    MAX_CONTEXT_MESSAGES: int = 30
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.85
    DATABASE_PATH: str = os.environ.get("DB_PATH", "atig_memory.db")
    PORT: int = int(os.environ.get("PORT", 8080))
    HOST: str = "0.0.0.0"

CONFIG = Config()