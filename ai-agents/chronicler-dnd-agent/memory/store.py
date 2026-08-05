"""
memory/store.py — The living world database.
All agents read and write through this single interface,
ensuring the shared world state stays consistent.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from config import config


class WorldMemory:
    def __init__(self):
        Path(config.db_path).parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(config.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        schema = (Path(__file__).parent / "schema.sql").read_text()
        self.conn.executescript(schema)
        self.conn.commit()

    # ── Campaigns ─────────────────────────────────────────────────────
    def create_campaign(self, name: str, setting: str = "", tone: str = "", dm_notes: str = "") -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            "INSERT INTO campaigns (name,setting,tone,dm_notes,world_state,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (name, setting, tone, dm_notes, json.dumps({}), now, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_campaign(self, campaign_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
        return dict(row) if row else None

    def get_all_campaigns(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM campaigns ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]

    def update_world_state(self, campaign_id: int, state: dict):
        self.conn.execute(
            "UPDATE campaigns SET world_state=?, updated_at=? WHERE id=?",
            (json.dumps(state), datetime.utcnow().isoformat(), campaign_id),
        )
        self.conn.commit()

    # ── Sessions ──────────────────────────────────────────────────────
    def add_session(self, campaign_id: int, raw_notes: str, session_num: int = None) -> int:
        if session_num is None:
            row = self.conn.execute(
                "SELECT MAX(session_num) as mx FROM sessions WHERE campaign_id=?", (campaign_id,)
            ).fetchone()
            session_num = (row["mx"] or 0) + 1
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            "INSERT INTO sessions (campaign_id,session_num,raw_notes,created_at) VALUES (?,?,?,?)",
            (campaign_id, session_num, raw_notes, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_sessions(self, campaign_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM sessions WHERE campaign_id=? ORDER BY session_num", (campaign_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── NPCs ──────────────────────────────────────────────────────────
    def upsert_npc(self, campaign_id: int, data: dict) -> int:
        now = datetime.utcnow().isoformat()
        existing = None
        if data.get("name"):
            existing = self.conn.execute(
                "SELECT id FROM npcs WHERE campaign_id=? AND name=?", (campaign_id, data["name"])
            ).fetchone()
        if existing:
            npc_id = existing["id"]
            self.conn.execute(
                """UPDATE npcs SET race=COALESCE(?,race), class_role=COALESCE(?,class_role),
                   alignment=COALESCE(?,alignment), personality=COALESCE(?,personality),
                   backstory=COALESCE(?,backstory), current_status=COALESCE(?,current_status),
                   attitude_to_party=COALESCE(?,attitude_to_party), secrets=COALESCE(?,secrets),
                   voice_style=COALESCE(?,voice_style), updated_at=? WHERE id=?""",
                (
                    data.get("race"), data.get("class_role"), data.get("alignment"),
                    data.get("personality"), data.get("backstory"), data.get("current_status"),
                    data.get("attitude_to_party"), data.get("secrets"), data.get("voice_style"),
                    now, npc_id,
                ),
            )
        else:
            cur = self.conn.execute(
                """INSERT INTO npcs (campaign_id,name,race,class_role,alignment,personality,
                   backstory,current_status,attitude_to_party,secrets,voice_style,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    campaign_id, data.get("name"), data.get("race"), data.get("class_role"),
                    data.get("alignment"), data.get("personality"), data.get("backstory"),
                    data.get("current_status", "alive"), data.get("attitude_to_party", "neutral"),
                    data.get("secrets"), data.get("voice_style"), now, now,
                ),
            )
            npc_id = cur.lastrowid
        self.conn.commit()
        return npc_id

    def get_npcs(self, campaign_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM npcs WHERE campaign_id=? ORDER BY name", (campaign_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_npc(self, npc_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM npcs WHERE id=?", (npc_id,)).fetchone()
        return dict(row) if row else None

    # ── Locations ─────────────────────────────────────────────────────
    def upsert_location(self, campaign_id: int, data: dict) -> int:
        now = datetime.utcnow().isoformat()
        existing = None
        if data.get("name"):
            existing = self.conn.execute(
                "SELECT id FROM locations WHERE campaign_id=? AND name=?", (campaign_id, data["name"])
            ).fetchone()
        if existing:
            loc_id = existing["id"]
            self.conn.execute(
                """UPDATE locations SET loc_type=COALESCE(?,loc_type),
                   description=COALESCE(?,description), lore=COALESCE(?,lore),
                   map_x=COALESCE(?,map_x), map_y=COALESCE(?,map_y),
                   status=COALESCE(?,status), revealed=COALESCE(?,revealed), updated_at=? WHERE id=?""",
                (
                    data.get("loc_type"), data.get("description"), data.get("lore"),
                    data.get("map_x"), data.get("map_y"), data.get("status"),
                    data.get("revealed"), now, loc_id,
                ),
            )
        else:
            cur = self.conn.execute(
                """INSERT INTO locations (campaign_id,name,loc_type,description,lore,
                   map_x,map_y,status,revealed,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    campaign_id, data["name"], data.get("loc_type"), data.get("description"),
                    data.get("lore"), data.get("map_x", 50.0), data.get("map_y", 50.0),
                    data.get("status", "intact"), data.get("revealed", 0), now, now,
                ),
            )
            loc_id = cur.lastrowid
        self.conn.commit()
        return loc_id

    def get_locations(self, campaign_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM locations WHERE campaign_id=? ORDER BY name", (campaign_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Factions ──────────────────────────────────────────────────────
    def upsert_faction(self, campaign_id: int, data: dict) -> int:
        now = datetime.utcnow().isoformat()
        existing = self.conn.execute(
            "SELECT id FROM factions WHERE campaign_id=? AND name=?", (campaign_id, data["name"])
        ).fetchone()
        if existing:
            fac_id = existing["id"]
            self.conn.execute(
                """UPDATE factions SET description=COALESCE(?,description),
                   goals=COALESCE(?,goals), attitude_to_party=COALESCE(?,attitude_to_party),
                   secrets=COALESCE(?,secrets), updated_at=? WHERE id=?""",
                (data.get("description"), data.get("goals"), data.get("attitude_to_party"),
                 data.get("secrets"), now, fac_id),
            )
        else:
            cur = self.conn.execute(
                """INSERT INTO factions (campaign_id,name,description,goals,attitude_to_party,secrets,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (campaign_id, data["name"], data.get("description"), data.get("goals"),
                 data.get("attitude_to_party", "neutral"), data.get("secrets"), now, now),
            )
            fac_id = cur.lastrowid
        self.conn.commit()
        return fac_id

    def get_factions(self, campaign_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM factions WHERE campaign_id=? ORDER BY name", (campaign_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Plot Threads ──────────────────────────────────────────────────
    def upsert_plot_thread(self, campaign_id: int, data: dict) -> int:
        now = datetime.utcnow().isoformat()
        existing = self.conn.execute(
            "SELECT id FROM plot_threads WHERE campaign_id=? AND title=?", (campaign_id, data["title"])
        ).fetchone()
        if existing:
            t_id = existing["id"]
            self.conn.execute(
                """UPDATE plot_threads SET status=COALESCE(?,status),
                   description=COALESCE(?,description), hooks=COALESCE(?,hooks), updated_at=? WHERE id=?""",
                (data.get("status"), data.get("description"), data.get("hooks"), now, t_id),
            )
        else:
            cur = self.conn.execute(
                """INSERT INTO plot_threads (campaign_id,title,thread_type,status,description,hooks,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (campaign_id, data["title"], data.get("thread_type", "main"),
                 data.get("status", "active"), data.get("description"), data.get("hooks"), now, now),
            )
            t_id = cur.lastrowid
        self.conn.commit()
        return t_id

    def get_plot_threads(self, campaign_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM plot_threads WHERE campaign_id=? ORDER BY thread_type, title", (campaign_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Lore ──────────────────────────────────────────────────────────
    def add_lore(self, campaign_id: int, title: str, category: str, content: str) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            "INSERT INTO lore_entries (campaign_id,title,category,content,created_at) VALUES (?,?,?,?,?)",
            (campaign_id, title, category, content, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_lore(self, campaign_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM lore_entries WHERE campaign_id=? ORDER BY category, title", (campaign_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Change Event Bus ──────────────────────────────────────────────
    def emit_event(self, campaign_id: int, event_type: str, payload: dict) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            "INSERT INTO change_events (campaign_id,event_type,payload,processed_by,created_at) VALUES (?,?,?,?,?)",
            (campaign_id, event_type, json.dumps(payload), json.dumps([]), now),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_unprocessed_events(self, campaign_id: int, agent_name: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM change_events WHERE campaign_id=? AND processed_by NOT LIKE ? ORDER BY id",
            (campaign_id, f'%"{agent_name}"%'),
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_event_processed(self, event_id: int, agent_name: str):
        row = self.conn.execute("SELECT processed_by FROM change_events WHERE id=?", (event_id,)).fetchone()
        processed = json.loads(row["processed_by"]) if row else []
        if agent_name not in processed:
            processed.append(agent_name)
        self.conn.execute(
            "UPDATE change_events SET processed_by=? WHERE id=?",
            (json.dumps(processed), event_id),
        )
        self.conn.commit()

    # ── Clarifications ────────────────────────────────────────────────
    def add_clarification(self, campaign_id: int, question: str, context: str = "") -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            "INSERT INTO clarifications (campaign_id,question,context,created_at) VALUES (?,?,?,?)",
            (campaign_id, question, context, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_pending_clarifications(self, campaign_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM clarifications WHERE campaign_id=? AND resolved=0 ORDER BY id",
            (campaign_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def answer_clarification(self, clarification_id: int, answer: str):
        self.conn.execute(
            "UPDATE clarifications SET answer=?, resolved=1 WHERE id=?",
            (answer, clarification_id),
        )
        self.conn.commit()

    # ── Agent Tasks ───────────────────────────────────────────────────
    def log_task(self, campaign_id: int, agent_name: str, task: str) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            "INSERT INTO agent_tasks (campaign_id,agent_name,task,status,created_at) VALUES (?,?,?,?,?)",
            (campaign_id, agent_name, task[:500], "running", now),
        )
        self.conn.commit()
        return cur.lastrowid

    def complete_task(self, task_id: int, result: str, duration_ms: int, success: bool):
        self.conn.execute(
            "UPDATE agent_tasks SET result=?, duration_ms=?, status=? WHERE id=?",
            (result[:4000], duration_ms, "success" if success else "error", task_id),
        )
        self.conn.commit()

    # ── Full World Snapshot (for context injection) ────────────────────
    def get_world_snapshot(self, campaign_id: int) -> dict:
        """Returns a compact snapshot of the entire campaign world state."""
        return {
            "campaign": self.get_campaign(campaign_id),
            "npcs": self.get_npcs(campaign_id),
            "locations": self.get_locations(campaign_id),
            "factions": self.get_factions(campaign_id),
            "plot_threads": self.get_plot_threads(campaign_id),
            "lore": self.get_lore(campaign_id),
            "sessions": self.get_sessions(campaign_id),
        }


world = WorldMemory()
