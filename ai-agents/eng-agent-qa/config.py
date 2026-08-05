import os
from dataclasses import dataclass, field


@dataclass
class Config:
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = "claude-sonnet-4-5"
    max_tokens: int = 16000
    db_path: str = "memory/agent_memory.db"
    checkpoint_dir: str = "checkpoints"
    log_dir: str = "logs"
    reports_dir: str = "reports"
    output_dir: str = "output"
    improvement_threshold: float = 0.7


config = Config()