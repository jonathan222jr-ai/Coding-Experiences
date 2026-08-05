-- ═══════════════════════════════════════════════════════════
--  D&D Campaign World State Schema
--  Every table here is a "living document" — agents read and
--  write to this as the campaign evolves session by session.
-- ═══════════════════════════════════════════════════════════

-- ── Campaigns ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS campaigns (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    setting     TEXT,           -- e.g. "Forgotten Realms", "Homebrew"
    tone        TEXT,           -- e.g. "grimdark", "high fantasy", "horror"
    dm_notes    TEXT,
    world_state TEXT,           -- JSON blob: current political/environmental state
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    active      INTEGER DEFAULT 1
);

-- ── Sessions ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    session_num INTEGER NOT NULL,
    title       TEXT,
    raw_notes   TEXT,           -- DM's raw session notes
    processed   INTEGER DEFAULT 0,
    played_at   TEXT,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- ── World Events ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS world_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL,
    session_id      INTEGER,
    event_type      TEXT NOT NULL,  -- NPC_ALIGNMENT_CHANGED, LOCATION_DESTROYED, etc.
    entity_type     TEXT,           -- npc | location | faction | item | plot
    entity_id       INTEGER,
    description     TEXT NOT NULL,
    old_value       TEXT,           -- JSON: state before
    new_value       TEXT,           -- JSON: state after
    propagated      INTEGER DEFAULT 0,
    timestamp       TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- ── NPCs ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS npcs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL,
    name            TEXT NOT NULL,
    race            TEXT,
    class_role      TEXT,           -- role in the world (blacksmith, villain, etc.)
    alignment       TEXT,
    faction_id      INTEGER,
    location_id     INTEGER,
    personality     TEXT,           -- JSON: traits, ideals, bonds, flaws
    backstory       TEXT,
    current_status  TEXT DEFAULT 'alive',  -- alive | dead | missing | unknown
    attitude_to_party TEXT DEFAULT 'neutral', -- hostile | neutral | friendly | ally
    secrets         TEXT,           -- JSON array of secrets
    voice_style     TEXT,           -- for GPT-4o dialogue generation
    portrait_url    TEXT,           -- DALL-E generated portrait
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- ── NPC Relationships ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS npc_relationships (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    npc_a_id    INTEGER NOT NULL,
    npc_b_id    INTEGER NOT NULL,
    rel_type    TEXT NOT NULL,      -- ally | enemy | lover | rival | family | unknown
    strength    INTEGER DEFAULT 5,  -- 1-10
    notes       TEXT,
    FOREIGN KEY (npc_a_id) REFERENCES npcs(id),
    FOREIGN KEY (npc_b_id) REFERENCES npcs(id)
);

-- ── Locations ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS locations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL,
    name            TEXT NOT NULL,
    loc_type        TEXT,           -- city | dungeon | wilderness | tavern | region | etc.
    parent_id       INTEGER,        -- for hierarchical geography (region → city → district)
    description     TEXT,
    lore            TEXT,
    map_x           REAL,           -- normalised 0-100 coordinates for the interactive map
    map_y           REAL,
    map_zoom_level  INTEGER DEFAULT 1,  -- 1=world, 2=region, 3=local
    status          TEXT DEFAULT 'intact',  -- intact | ruined | destroyed | unknown
    controlling_faction_id INTEGER,
    revealed        INTEGER DEFAULT 0,   -- fog of war: has party visited?
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
    FOREIGN KEY (parent_id) REFERENCES locations(id)
);

-- ── Factions ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS factions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    goals           TEXT,           -- JSON array
    resources       TEXT,           -- JSON: power, wealth, military, arcane
    territory       TEXT,           -- JSON array of location_ids
    attitude_to_party TEXT DEFAULT 'neutral',
    notable_members TEXT,           -- JSON array of npc_ids
    secrets         TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- ── Plot Threads ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS plot_threads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL,
    title           TEXT NOT NULL,
    thread_type     TEXT,           -- main | side | faction | personal | mystery
    status          TEXT DEFAULT 'active',  -- active | resolved | dormant | failed
    description     TEXT,
    hooks           TEXT,           -- JSON array of upcoming hooks/clues
    involved_npcs   TEXT,           -- JSON array of npc_ids
    involved_factions TEXT,         -- JSON array of faction_ids
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- ── Lore Entries ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lore_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL,
    title           TEXT NOT NULL,
    category        TEXT,           -- history | magic | religion | geography | custom
    content         TEXT NOT NULL,
    related_entities TEXT,          -- JSON: {npcs:[], locations:[], factions:[]}
    created_at      TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- ── Items & Artifacts ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL,
    name            TEXT NOT NULL,
    item_type       TEXT,           -- weapon | armor | magic | artifact | mundane
    rarity          TEXT,           -- common | uncommon | rare | very rare | legendary
    description     TEXT,
    properties      TEXT,           -- JSON: mechanical stats per SRD
    lore            TEXT,
    current_holder  TEXT,           -- npc_id or "party" or "lost"
    location_id     INTEGER,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- ── AI Agent Tasks ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER,
    agent_name  TEXT NOT NULL,
    task        TEXT NOT NULL,
    result      TEXT,
    status      TEXT DEFAULT 'pending',
    duration_ms INTEGER,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- ── Change Events (pub/sub bus) ────────────────────────────
CREATE TABLE IF NOT EXISTS change_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL,
    event_type      TEXT NOT NULL,
    payload         TEXT NOT NULL,  -- JSON
    processed_by    TEXT,           -- JSON array of agent names that handled it
    created_at      TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- ── DM Clarification Queue ─────────────────────────────────
CREATE TABLE IF NOT EXISTS clarifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    question    TEXT NOT NULL,
    context     TEXT,
    answer      TEXT,
    resolved    INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);
