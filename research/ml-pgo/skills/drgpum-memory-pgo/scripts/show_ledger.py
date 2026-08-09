#!/usr/bin/env python3
"""Show the append-only record of optimization attempts.

    python scripts/show_ledger.py [path/to/ledger.jsonl]

Consult this before proposing a fix: it is how the agent answers "what have we
already tried?" without re-reading the whole conversation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from agent.ledger import Ledger

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "runs/ledger.jsonl"
    print(Ledger(path).format())
