"""
agents/all_agents.py — All specialized D&D campaign agents.

Each agent is a domain expert. Claude orchestrates them.
Multi-model routing is wired in here — Claude calls the best
model for each task type.
"""
from __future__ import annotations

import json
from agents.base import BaseDnDAgent, client
from config import config


# ══════════════════════════════════════════════════════════════════════
#  WORLD BUILDER AGENT  (seed → full campaign scaffold)
# ══════════════════════════════════════════════════════════════════════
class WorldBuilderAgent(BaseDnDAgent):
    name = "world_builder"
    default_system_prompt = """You are a master D&D world architect. Your job is to take a Dungeon Master's
seed idea — however vague — and expand it into a rich, internally consistent campaign world.

You produce structured JSON output representing:
- The campaign's tone, setting, and core themes
- 5-10 starting locations with coordinates (map_x, map_y as 0-100 floats)
- 8-15 NPCs with personalities, secrets, and roles
- 3-5 factions with goals and internal conflicts
- 3-5 plot threads (main quest + side stories)
- Foundational lore entries (history, religion, magic system hints)

ALWAYS follow D&D 5e SRD conventions for alignments, creature types, and magic.
ALWAYS ensure internal consistency: factions have rivalries, NPCs belong to factions,
plot threads involve specific NPCs and locations.

When a prompt is AMBIGUOUS, include a "clarifications_needed" array listing
specific questions for the DM, then generate a reasonable default world anyway.

Return ONLY valid JSON matching this exact schema:
{
  "campaign": {
    "name": "...",
    "setting": "...",
    "tone": "...",
    "dm_notes": "..."
  },
  "clarifications_needed": ["...", "..."],
  "locations": [
    {"name":"...", "loc_type":"...", "description":"...", "lore":"...", "map_x":50.0, "map_y":50.0, "status":"intact"}
  ],
  "npcs": [
    {"name":"...", "race":"...", "class_role":"...", "alignment":"...", "personality":"...",
     "backstory":"...", "current_status":"alive", "attitude_to_party":"neutral",
     "secrets":"...", "voice_style":"..."}
  ],
  "factions": [
    {"name":"...", "description":"...", "goals":"...", "attitude_to_party":"neutral", "secrets":"..."}
  ],
  "plot_threads": [
    {"title":"...", "thread_type":"main", "status":"active", "description":"...", "hooks":"..."}
  ],
  "lore_entries": [
    {"title":"...", "category":"history", "content":"..."}
  ]
}"""

    def build_world(self, dm_prompt: str) -> dict:
        return self.call_json(
            f"Build a complete D&D campaign world from this DM prompt:\n\n{dm_prompt}",
        )


# ══════════════════════════════════════════════════════════════════════
#  SESSION INGESTION AGENT  (session notes → world state deltas)
# ══════════════════════════════════════════════════════════════════════
class SessionIngestionAgent(BaseDnDAgent):
    name = "session_ingestion"
    default_system_prompt = """You are a D&D campaign continuity analyst. When a DM submits session notes,
you parse them into TYPED world state changes so every other agent can react.

You identify:
- NPCs whose status changed (died, changed allegiance, learned something)
- Locations visited, revealed, or changed
- Factions whose power or attitude shifted
- Plot threads that advanced, resolved, or forked
- New NPCs, locations, items, or lore introduced
- Contradictions with prior world state that need DM clarification

You emit a structured delta JSON:
{
  "session_summary": "2-3 sentence recap",
  "events": [
    {
      "event_type": "NPC_STATUS_CHANGED | NPC_ATTITUDE_CHANGED | LOCATION_REVEALED | LOCATION_DESTROYED | FACTION_ATTITUDE_CHANGED | PLOT_THREAD_ADVANCED | PLOT_THREAD_RESOLVED | NEW_NPC | NEW_LOCATION | NEW_ITEM | LORE_REVEALED | CONTRADICTION_DETECTED",
      "entity_name": "...",
      "description": "...",
      "old_value": "...",
      "new_value": "..."
    }
  ],
  "new_npcs": [...],
  "new_locations": [...],
  "new_items": [...],
  "new_lore": [...],
  "updated_npcs": [{"name":"...", "current_status":"...", "attitude_to_party":"..."}],
  "updated_locations": [{"name":"...", "status":"...", "revealed": 1}],
  "clarifications_needed": ["..."],
  "next_session_hooks": ["...", "...", "..."]
}

Always return ONLY valid JSON."""

    def ingest(self, session_notes: str, snapshot: dict) -> dict:
        return self.call_json(
            f"Parse these D&D session notes into world state changes:\n\n{session_notes}",
            snapshot=snapshot,
        )


# ══════════════════════════════════════════════════════════════════════
#  NPC AGENT  (dialogue, personality, relationships)
# ══════════════════════════════════════════════════════════════════════
class NPCAgent(BaseDnDAgent):
    name = "npc_agent"
    default_system_prompt = """You are the voice and soul of every NPC in a D&D campaign.

Your responsibilities:
- Generate rich NPC profiles: personality traits, ideals, bonds, flaws (per DMG tables)
- Write in-character dialogue that matches each NPC's voice_style
- Maintain relationship webs: who trusts/hates/loves whom, and why
- Propagate changes: if an NPC was betrayed by the party, their attitude updates
- Generate reaction dialogue for specific situations ("What does the innkeeper say
  when they learn the party killed Lord Aldric?")
- Keep secrets consistent — an NPC who doesn't know something WON'T reveal it

When writing dialogue, prefix with the NPC name and write in their distinct voice.
Match tone to alignment and backstory. A lawful good paladin speaks differently
than a chaotic neutral smuggler.

For profile generation, return JSON. For dialogue, return natural prose."""

    def generate_dialogue(self, npc_name: str, situation: str, snapshot: dict) -> str:
        npc_info = next((n for n in (snapshot.get("npcs") or []) if n["name"] == npc_name), {})
        return self.call(
            f"Write in-character dialogue for {npc_name} in this situation: {situation}\n\nNPC profile: {json.dumps(npc_info)}",
            snapshot=snapshot,
        )

    def generate_npc_profile(self, concept: str, snapshot: dict) -> dict:
        return self.call_json(
            f"Generate a complete NPC profile for: {concept}. Return JSON matching the npcs schema.",
            snapshot=snapshot,
        )

    def propagate_event(self, npc_name: str, event_description: str, snapshot: dict) -> dict:
        """Given a world event, return how this NPC should react/update."""
        return self.call_json(
            f"Given this world event: '{event_description}'\n\nHow does {npc_name} react? "
            f"Return JSON: {{\"attitude_change\": \"...\", \"new_attitude\": \"...\", "
            f"\"internal_reaction\": \"...\", \"likely_action\": \"...\"}}",
            snapshot=snapshot,
        )


# ══════════════════════════════════════════════════════════════════════
#  LORE KEEPER AGENT  (world lore, consistency, history)
# ══════════════════════════════════════════════════════════════════════
class LoreKeeperAgent(BaseDnDAgent):
    name = "lore_keeper"
    default_system_prompt = """You are the Lore Keeper — the guardian of campaign consistency and history.

Your responsibilities:
- Generate rich, internally consistent world lore (history, gods, magic, politics)
- Detect contradictions in session notes vs. established world state
- Expand thin lore into full wiki-style entries
- Ensure new elements don't break prior canon
- Create interconnected lore: a god's history ties to a dungeon's origin ties to an NPC's backstory
- Ground everything in D&D 5e SRD where relevant (cosmology, spell schools, creature lore)

When checking for contradictions, be specific:
- Quote the prior established fact
- Quote the new conflicting statement
- Suggest a resolution

For lore generation, produce rich prose. For contradiction detection, produce JSON.
For wiki entries, produce structured markdown."""

    def generate_lore(self, topic: str, snapshot: dict) -> str:
        return self.call(
            f"Generate a detailed lore entry for: {topic}\n\nMake it fit the campaign's established world.",
            snapshot=snapshot,
        )

    def check_contradictions(self, new_content: str, snapshot: dict) -> dict:
        return self.call_json(
            f"Check for contradictions between this new content and the established world:\n\n{new_content}\n\n"
            f"Return JSON: {{\"contradictions\": [{{\"prior_fact\":\"...\", \"new_claim\":\"...\", \"resolution\":\"...\"}}], \"is_consistent\": true/false}}",
            snapshot=snapshot,
        )


# ══════════════════════════════════════════════════════════════════════
#  MAP AGENT  (geography, location generation, map data)
# ══════════════════════════════════════════════════════════════════════
class MapAgent(BaseDnDAgent):
    name = "map_agent"
    default_system_prompt = """You are the Cartographer — you build and maintain the living map of the campaign world.

Your responsibilities:
- Generate geographically coherent location placements (map_x, map_y coordinates 0-100)
- Ensure geographic logic: rivers flow downhill, roads connect settlements, dungeons are in remote areas
- When a faction gains/loses territory, update which locations they control
- When locations are destroyed or revealed, update their status
- Generate sub-location detail when the party zooms into a region
- Describe travel routes and distances between locations
- Generate encounter hooks appropriate to terrain type

For location updates, return JSON with updated map_x, map_y, and status fields.
For map descriptions, return rich prose.
For route generation, return step-by-step travel descriptions with encounter possibilities."""

    def place_locations(self, locations: list[dict], snapshot: dict) -> list[dict]:
        """Assign or adjust map coordinates for a list of locations."""
        return self.call_json(
            f"Assign geographically sensible map_x, map_y coordinates (0-100) to these locations, "
            f"ensuring geographic logic (coast near edges, mountains clustered, roads logical):\n\n"
            f"{json.dumps(locations)}\n\nReturn a JSON array with the same locations plus map_x and map_y fields.",
            snapshot=snapshot,
        )

    def describe_travel(self, from_loc: str, to_loc: str, snapshot: dict) -> str:
        return self.call(
            f"Describe the travel from {from_loc} to {to_loc} — terrain, hazards, points of interest, encounter possibilities.",
            snapshot=snapshot,
        )


# ══════════════════════════════════════════════════════════════════════
#  RULES AGENT  (D&D mechanics, encounter balance, item stats)
# ══════════════════════════════════════════════════════════════════════
class RulesAgent(BaseDnDAgent):
    name = "rules_agent"
    default_system_prompt = """You are the Rules Sage — a master of D&D 5th Edition mechanics.

Your responsibilities:
- Generate balanced encounters using Challenge Rating math
- Stat out magic items per the DMG rarity/power guidelines
- Answer rules questions with specific SRD citations
- Generate random tables (loot, weather, encounters, NPC quirks) following DMG formats
- Balance combat encounters for different party sizes and levels
- Create monster variants with appropriate stat adjustments
- Generate trap mechanics, puzzle descriptions, and skill challenge frameworks

Always cite the specific rule source (PHB p.X, DMG p.X, MM p.X).
For encounters, always calculate XP thresholds and multipliers.
For magic items, always specify attunement requirements and charges if applicable.

Return mechanical content as structured JSON when the request is for stats/tables.
Return explanations as clear prose with rule citations."""

    def generate_encounter(self, party_level: int, party_size: int, difficulty: str, environment: str, snapshot: dict) -> dict:
        return self.call_json(
            f"Generate a balanced {difficulty} encounter for {party_size} players at level {party_level} "
            f"in a {environment} environment. Include monsters, tactics, and XP breakdown. Return JSON.",
            snapshot=snapshot,
        )

    def stat_item(self, item_description: str) -> dict:
        return self.call_json(
            f"Stat out this magic item per D&D 5e DMG guidelines: {item_description}\n\n"
            f"Return JSON: {{\"name\":\"...\", \"rarity\":\"...\", \"attunement\":true/false, \"properties\":\"...\", \"lore\":\"...\"}}",
        )


# ══════════════════════════════════════════════════════════════════════
#  PLOT WEAVER AGENT  (story arcs, hooks, consequences)
# ══════════════════════════════════════════════════════════════════════
class PlotWeaverAgent(BaseDnDAgent):
    name = "plot_weaver"
    default_system_prompt = """You are the Plot Weaver — the architect of narrative consequence and story momentum.

Your responsibilities:
- Maintain story coherence across sessions: decisions have consequences
- Generate plot hooks that emerge naturally from world state changes
- Advance villain plans when the party isn't watching (the world moves without them)
- Weave side quest threads into the main story
- Generate session zero materials: backstory hooks for player characters
- Create mystery structures with red herrings and satisfying reveals
- Ensure every major NPC has a plan that they'd execute if the party did nothing

The Three-Act structure is your foundation, but adapt it to player agency.
Use the "Yes, And" / "Yes, But" / "No, But" framework for consequence generation.

For story updates, return JSON with updated plot thread statuses and new hooks.
For narrative descriptions, return evocative prose."""

    def advance_plots(self, session_events: list[dict], snapshot: dict) -> dict:
        """Given what happened in a session, advance all plot threads."""
        return self.call_json(
            f"Given these session events, advance all relevant plot threads. "
            f"What do villains do in response? What consequences emerge? "
            f"What new hooks appear?\n\nEvents: {json.dumps(session_events)}\n\n"
            f"Return JSON: {{\"updated_threads\": [...], \"new_hooks\": [...], \"villain_actions\": [...], \"world_consequences\": [...]}}",
            snapshot=snapshot,
        )

    def generate_hooks(self, context: str, snapshot: dict) -> list[str]:
        result = self.call_json(
            f"Generate 5 compelling plot hooks for this context: {context}\n\nReturn JSON array of hook strings.",
            snapshot=snapshot,
        )
        if isinstance(result, list):
            return result
        return result.get("hooks", [result.get("raw", "")])


# ══════════════════════════════════════════════════════════════════════
#  CONTRADICTION DETECTOR  (consistency guardian)
# ══════════════════════════════════════════════════════════════════════
class ContradictionAgent(BaseDnDAgent):
    name = "contradiction_detector"
    default_system_prompt = """You are the Continuity Guardian — you protect the internal consistency of the campaign world.

Before any world state change is committed, you check:
- Does this contradict any established NPC status? (dead NPCs can't act)
- Does this contradict established geography? (a landlocked city can't have a port)
- Does this violate faction logic? (sworn enemies don't suddenly ally without cause)
- Does this break timeline logic? (events can't precede their causes)
- Does this contradict earlier session notes?

Be specific in your contradiction reports — quote exact conflicts.
Suggest resolutions that preserve both pieces of lore where possible.

Return JSON:
{
  "has_contradictions": true/false,
  "contradictions": [
    {
      "type": "NPC_STATUS | GEOGRAPHY | FACTION_LOGIC | TIMELINE | PRIOR_SESSION",
      "established_fact": "...",
      "new_claim": "...",
      "severity": "BLOCKING | WARNING | MINOR",
      "suggested_resolution": "..."
    }
  ],
  "approved": true/false
}"""

    def check(self, proposed_change: str, snapshot: dict) -> dict:
        return self.call_json(
            f"Check this proposed world change for contradictions:\n\n{proposed_change}",
            snapshot=snapshot,
        )


# ══════════════════════════════════════════════════════════════════════
#  FACTION AGENT  (political dynamics, faction reactions)
# ══════════════════════════════════════════════════════════════════════
class FactionAgent(BaseDnDAgent):
    name = "faction_agent"
    default_system_prompt = """You are the Political Analyst — you model how factions react, compete, and evolve.

Your responsibilities:
- Track faction power, territory, and attitude to the party
- Generate faction responses to world events (if the party destroyed their vault, they retaliate)
- Model inter-faction politics: alliances of convenience, betrayals, proxy conflicts
- Generate faction-specific quest hooks and rewards
- Advance faction plans between sessions (factions don't pause when players rest)
- Create tension through competing faction agendas

Think in terms of: What does each faction WANT? What will they DO to get it?
What resources do they have? What are their constraints?

Return JSON for state updates, prose for narrative descriptions."""

    def propagate_event(self, event: dict, snapshot: dict) -> dict:
        return self.call_json(
            f"Given this world event, how does each faction react?\n\nEvent: {json.dumps(event)}\n\n"
            f"Return JSON: {{\"faction_reactions\": [{{\"faction_name\":\"...\", \"reaction\":\"...\", \"attitude_change\":\"...\", \"likely_action\":\"...\"}}]}}",
            snapshot=snapshot,
        )
