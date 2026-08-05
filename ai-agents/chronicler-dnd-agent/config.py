import os
from dataclasses import dataclass, field


@dataclass
class Config:
    # Primary AI — Claude as orchestrator
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = "claude-sonnet-4-5"
    max_tokens: int = 16000

    # Optional multi-model keys
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    google_api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))

    # Model routing
    dialogue_model: str = "gpt-4o"           # GPT-4o for NPC voice/dialogue
    lore_check_model: str = "gemini-1.5-pro" # Gemini for long-context contradiction checks
    rules_model: str = "o3-mini"             # OpenAI reasoning for D&D mechanics

    # Paths
    db_path: str = "memory/world.db"
    checkpoint_dir: str = "checkpoints"
    log_dir: str = "logs"
    reports_dir: str = "reports"
    output_dir: str = "output"
    lore_dir: str = "lore"

    # D&D SRD embeddings path
    srd_path: str = "lore/srd5.txt"


config = Config()
