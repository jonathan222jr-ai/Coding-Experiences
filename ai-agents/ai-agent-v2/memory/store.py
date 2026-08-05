import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config import config

class MemoryStore:
    def __init__(self):
        Path(config.db_path).parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(config.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        schema = Path("memory/schema.sql").read_text()
        self.conn.executescript(schema)
        self.conn.commit()

    def log_task(self, goal, agent, status, output, duration_ms, success):
        self.conn.execute(
            "INSERT INTO tasks (timestamp, goal, agent, status, output, duration_ms, success) VALUES (?,?,?,?,?,?,?)",
            (datetime.utcnow().isoformat(), goal, agent, status, output, duration_ms, int(success))
        )
        self.conn.commit()

    def log_learning(self, category, insight, source_task_id=None):
        self.conn.execute(
            "INSERT INTO learnings (timestamp, category, insight, source_task_id) VALUES (?,?,?,?)",
            (datetime.utcnow().isoformat(), category, insight, source_task_id)
        )
        self.conn.commit()

    def get_recent_tasks(self, limit=20):
        rows = self.conn.execute(
            "SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_success_rate(self, agent=None, window=50):
        if agent:
            rows = self.conn.execute(
                "SELECT success FROM tasks WHERE agent=? ORDER BY id DESC LIMIT ?",
                (agent, window)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT success FROM tasks ORDER BY id DESC LIMIT ?", (window,)
            ).fetchall()
        if not rows:
            return 1.0
        return sum(r["success"] for r in rows) / len(rows)

    def get_learnings(self, category=None, limit=30):
        if category:
            rows = self.conn.execute(
                "SELECT * FROM learnings WHERE category=? ORDER BY id DESC LIMIT ?",
                (category, limit)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM learnings ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def save_agent_prompt(self, agent_name, prompt, version):
        # deactivate old
        self.conn.execute(
            "UPDATE agent_prompts SET active=0 WHERE agent_name=?", (agent_name,)
        )
        self.conn.execute(
            "INSERT INTO agent_prompts (agent_name, version, prompt, performance_score, created_at, active) VALUES (?,?,?,?,?,1)",
            (agent_name, version, prompt, 0.0, datetime.utcnow().isoformat())
        )
        self.conn.commit()

    def get_active_prompt(self, agent_name):
        row = self.conn.execute(
            "SELECT prompt FROM agent_prompts WHERE agent_name=? AND active=1",
            (agent_name,)
        ).fetchone()
        return row["prompt"] if row else None

    def log_improvement(self, proposed_by, description):
        cur = self.conn.execute(
            "INSERT INTO improvements (timestamp, proposed_by, description) VALUES (?,?,?)",
            (datetime.utcnow().isoformat(), proposed_by, description)
        )
        self.conn.commit()
        return cur.lastrowid

    def mark_improvement_applied(self, improvement_id):
        self.conn.execute(
            "UPDATE improvements SET applied=1 WHERE id=?", (improvement_id,)
        )
        self.conn.commit()

memory = MemoryStore()