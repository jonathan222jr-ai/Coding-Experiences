# 🐉 Chronicler — D&D Campaign AI Agent System

A living, breathing D&D campaign intelligence system. Feed it a DM prompt, it builds a world.
Log session notes, it propagates consequences across every NPC, faction, and plot thread.

---

## Architecture

```
DM Prompt → WorldBuilderAgent → Campaign World (NPCs, Locations, Factions, Plots)
                                        ↓
Session Notes → SessionIngestionAgent → ContradictionAgent → World State Delta
                                                                  ↓
              ┌─────────────────────────┬───────────────────────────┐
              ↓                         ↓                           ↓
        NPCAgent                  PlotWeaverAgent           FactionAgent
   (dialogue, reactions)    (plot advancement, hooks)   (faction reactions)
              ↓                         ↓                           ↓
              └─────────────────── WorldMemory ───────────────────┘
                                 (SQLite world.db)
                                        ↓
                              Flask API + Interactive UI
                         (Map, NPCs, Plots, Lore, Encounter Builder)
```

## Agents

| Agent | Role |
|-------|------|
| `WorldBuilderAgent` | Turns a DM seed prompt into a full campaign world |
| `SessionIngestionAgent` | Parses session notes into typed world state events |
| `ContradictionAgent` | Catches conflicts before committing world changes |
| `NPCAgent` | Generates dialogue, reactions, and profiles for each NPC |
| `LoreKeeperAgent` | Maintains and expands campaign lore; answers oracle queries |
| `MapAgent` | Handles geography, location placement, travel descriptions |
| `PlotWeaverAgent` | Advances plot threads, generates hooks, models villain plans |
| `FactionAgent` | Models faction politics and reactions to world events |
| `RulesAgent` | D&D 5e SRD mechanics: encounters, items, spell rulings |

## Key Features

- **Living World**: Every session note automatically updates NPCs, factions, and plot threads
- **Event Bus**: Changes propagate — if an NPC dies, every agent that references them knows
- **Contradiction Detection**: Catches "dead NPCs doing things" before it commits
- **Interactive Map**: Drag/zoom world map with fog of war, location detail popups
- **NPC Dialogue AI**: Generates in-character responses based on personality and world state
- **Encounter Builder**: CR-balanced encounters using D&D 5e math
- **Lore Oracle**: Query the AI about any aspect of your world

## Setup

```bash
pip install -r requirements.txt

# Create a .env file:
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Optional additional models:
echo "OPENAI_API_KEY=..." >> .env
echo "GOOGLE_API_KEY=..." >> .env

python app.py
# → http://localhost:5001
```

## Usage Flow

1. **Create Campaign**: Enter a campaign concept, click "Forge This World"
2. **Review World**: Explore the generated map, NPCs, factions, and plot threads
3. **Answer Clarifications**: The AI will ask questions if your prompt was ambiguous
4. **Log Sessions**: After each session, paste your notes and click "Process Session"
5. **Watch the World Evolve**: NPCs update, plots advance, factions react

## Multi-Model Architecture (Future)

The system is designed to route to specialist models:
- **Claude**: Orchestration, world building, lore (primary)
- **GPT-4o**: NPC dialogue voice (set `OPENAI_API_KEY`)
- **Gemini 1.5 Pro**: Long-context contradiction checking across all sessions
- **OpenAI o-series**: D&D rules math and encounter balance
- **DALL-E**: NPC portrait generation

Enable each by adding the relevant API key to `.env`.

## Database

All world state lives in `memory/world.db` (SQLite). Key tables:
- `campaigns` — Campaign metadata
- `npcs` — Every character with status, attitude, secrets
- `locations` — The world map with coordinates
- `factions` — Political entities
- `plot_threads` — Story arcs (main, side, faction, personal, mystery)
- `lore_entries` — Campaign history, religion, magic
- `change_events` — The event bus: every world change logged
- `clarifications` — Pending DM questions from the AI
- `sessions` — Raw session notes history
