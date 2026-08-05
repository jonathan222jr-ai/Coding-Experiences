import os
from dataclasses import dataclass

@dataclass
class Config:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    # Token strategy: Haiku for classify/triage, Sonnet for answers
    model_fast:  str = "claude-haiku-4-5-20251001"
    model_smart: str = "claude-sonnet-4-6"
    model:       str = "claude-sonnet-4-6"
    max_tokens_fast:  int = 256
    max_tokens_smart: int = 600
    max_tokens:       int = 600
    db_path:          str = "memory/agent_memory.db"
    transcript_dir:   str = "transcripts"
    checkpoint_dir:   str = "checkpoints"
    log_dir:          str = "logs"
    improvement_threshold: float = 0.7

config = Config()
