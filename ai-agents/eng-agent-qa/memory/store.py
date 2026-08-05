import sqlite3
import uuid
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
        schema_path = Path("memory/schema.sql")
        if schema_path.exists():
            schema = schema_path.read_text()
        else:
            schema_path = Path(__file__).parent / "schema.sql"
            schema = schema_path.read_text()
        self.conn.executescript(schema)
        self.conn.commit()

    # ── Session management ──────────────────────────────────────────────
    def create_session(self, title: str = None) -> str:
        sid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            "INSERT INTO sessions (session_id, started_at, last_active, title) VALUES (?,?,?,?)",
            (sid, now, now, title or f"Session {now[:10]}"),
        )
        self.conn.commit()
        return sid

    def get_or_create_session(self, session_id: str = None) -> str:
        if session_id:
            row = self.conn.execute(
                "SELECT session_id FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            if row:
                self.conn.execute(
                    "UPDATE sessions SET last_active=? WHERE session_id=?",
                    (datetime.utcnow().isoformat(), session_id),
                )
                self.conn.commit()
                return session_id
        return self.create_session()

    def get_sessions(self, limit: int = 50):
        rows = self.conn.execute(
            "SELECT * FROM sessions ORDER BY last_active DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_session(self, session_id: str):
        row = self.conn.execute(
            "SELECT * FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── Prompt logging ──────────────────────────────────────────────────
    def log_prompt(self, session_id: str, prompt: str) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            "INSERT INTO prompts (session_id, timestamp, prompt, status) VALUES (?,?,?,?)",
            (session_id, now, prompt, "running"),
        )
        self.conn.execute(
            "UPDATE sessions SET last_active=?, total_prompts=total_prompts+1 WHERE session_id=?",
            (now, session_id),
        )
        self.conn.commit()
        return cur.lastrowid

    def complete_prompt(self, prompt_id: int, report_path: str = None, status: str = "completed"):
        self.conn.execute(
            "UPDATE prompts SET status=?, report_path=? WHERE id=?",
            (status, report_path, prompt_id),
        )
        self.conn.commit()

    def get_prompts(self, session_id: str):
        rows = self.conn.execute(
            "SELECT * FROM prompts WHERE session_id=? ORDER BY id DESC",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_prompts(self, limit: int = 200):
        rows = self.conn.execute(
            """SELECT p.*, s.title as session_title
               FROM prompts p JOIN sessions s ON p.session_id = s.session_id
               ORDER BY p.id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Task logging ────────────────────────────────────────────────────
    def log_task(self, goal, agent, status, output, duration_ms, success,
                 prompt_id=None, session_id=None, step_number=1):
        self.conn.execute(
            """INSERT INTO tasks
               (prompt_id, session_id, timestamp, goal, agent, status, output, duration_ms, success, step_number)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (prompt_id, session_id, datetime.utcnow().isoformat(),
             goal[:500], agent, status, output[:2000], duration_ms, int(success), step_number),
        )
        self.conn.commit()

    def get_tasks_for_prompt(self, prompt_id: int):
        rows = self.conn.execute(
            "SELECT * FROM tasks WHERE prompt_id=? ORDER BY step_number",
            (prompt_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Stats ───────────────────────────────────────────────────────────
    def get_recent_tasks(self, limit=20):
        rows = self.conn.execute(
            "SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_success_rate(self, agent=None, window=50):
        if agent:
            rows = self.conn.execute(
                "SELECT success FROM tasks WHERE agent=? ORDER BY id DESC LIMIT ?",
                (agent, window),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT success FROM tasks ORDER BY id DESC LIMIT ?", (window,)
            ).fetchall()
        if not rows:
            return 1.0
        return sum(r["success"] for r in rows) / len(rows)

    # ── Agent prompts ───────────────────────────────────────────────────
    def save_agent_prompt(self, agent_name, prompt, version):
        self.conn.execute(
            "UPDATE agent_prompts SET active=0 WHERE agent_name=?", (agent_name,)
        )
        self.conn.execute(
            """INSERT INTO agent_prompts
               (agent_name, version, prompt, performance_score, created_at, active)
               VALUES (?,?,?,?,?,1)""",
            (agent_name, version, prompt, 0.0, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def get_active_prompt(self, agent_name):
        row = self.conn.execute(
            "SELECT prompt FROM agent_prompts WHERE agent_name=? AND active=1",
            (agent_name,),
        ).fetchone()
        return row["prompt"] if row else None

    def log_learning(self, category, insight, source_task_id=None):
        self.conn.execute(
            "INSERT INTO learnings (timestamp, category, insight, source_task_id) VALUES (?,?,?,?)",
            (datetime.utcnow().isoformat(), category, insight, source_task_id),
        )
        self.conn.commit()

    def get_learnings(self, category=None, limit=30):
        if category:
            rows = self.conn.execute(
                "SELECT * FROM learnings WHERE category=? ORDER BY id DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM learnings ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def log_improvement(self, proposed_by, description):
        cur = self.conn.execute(
            "INSERT INTO improvements (timestamp, proposed_by, description) VALUES (?,?,?)",
            (datetime.utcnow().isoformat(), proposed_by, description),
        )
        self.conn.commit()
        return cur.lastrowid

    def mark_improvement_applied(self, improvement_id):
        self.conn.execute(
            "UPDATE improvements SET applied=1 WHERE id=?", (improvement_id,)
        )
        self.conn.commit()


memory = MemoryStore()
