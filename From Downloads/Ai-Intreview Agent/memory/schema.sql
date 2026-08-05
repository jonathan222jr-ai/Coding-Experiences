CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    goal TEXT,
    agent TEXT,
    status TEXT,
    output TEXT,
    duration_ms INTEGER,
    success INTEGER
);

CREATE TABLE IF NOT EXISTS learnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    category TEXT,
    insight TEXT,
    source_task_id INTEGER
);

CREATE TABLE IF NOT EXISTS agent_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT,
    version INTEGER,
    prompt TEXT,
    performance_score REAL,
    created_at TEXT,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS improvements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    proposed_by TEXT,
    description TEXT,
    applied INTEGER DEFAULT 0,
    rolled_back INTEGER DEFAULT 0
);