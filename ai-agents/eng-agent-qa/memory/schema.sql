CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    started_at TEXT NOT NULL,
    last_active TEXT NOT NULL,
    total_prompts INTEGER DEFAULT 0,
    title TEXT
);

CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    prompt TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    report_path TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER,
    session_id TEXT,
    timestamp TEXT,
    goal TEXT,
    agent TEXT,
    status TEXT,
    output TEXT,
    duration_ms INTEGER,
    success INTEGER,
    step_number INTEGER DEFAULT 1,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
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
