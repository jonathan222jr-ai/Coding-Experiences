"""
orchestrator.py — The Campaign Master AI Orchestrator.

This is the brain that:
1. Routes DM input to the right agents
2. Propagates world state changes across all agents
3. Detects contradictions before committing changes
4. Maintains the event bus
5. Asks clarifying questions when input is ambiguous
"""
from __future__ import annotations

import json
import queue
import time
from typing import Any

from agents import (
    WorldBuilderAgent, SessionIngestionAgent, NPCAgent,
    LoreKeeperAgent, MapAgent, RulesAgent, PlotWeaverAgent,
    ContradictionAgent, FactionAgent,
)
from memory.store import world
from config import config


class CampaignOrchestrator:
    def __init__(self):
        self.world_builder = WorldBuilderAgent()
        self.session_ingestion = SessionIngestionAgent()
        self.npc_agent = NPCAgent()
        self.lore_keeper = LoreKeeperAgent()
        self.map_agent = MapAgent()
        self.rules_agent = RulesAgent()
        self.plot_weaver = PlotWeaverAgent()
        self.contradiction_agent = ContradictionAgent()
        self.faction_agent = FactionAgent()

    # ── Campaign Creation ──────────────────────────────────────────────
    def create_campaign(self, dm_prompt: str, campaign_id: int = None, event_queue: queue.Queue = None) -> dict:
        def emit(event: dict):
            if event_queue:
                event_queue.put(event)

        emit({"type": "status", "text": "🌍 World Builder is crafting your campaign world..."})

        # Step 1: World Builder generates the initial world
        world_data = self.world_builder.build_world(dm_prompt)
        if not world_data or "campaign" not in world_data:
            emit({"type": "error", "text": "World Builder returned unexpected data"})
            return {}

        # Step 2: Create campaign in DB (or update existing)
        c = world_data.get("campaign", {})
        if campaign_id:
            # Updating existing campaign
            world.conn.execute(
                "UPDATE campaigns SET name=COALESCE(?,name), setting=COALESCE(?,setting), tone=COALESCE(?,tone), updated_at=datetime('now') WHERE id=?",
                (c.get("name"), c.get("setting"), c.get("tone"), campaign_id),
            )
            world.conn.commit()
        else:
            campaign_id = world.create_campaign(
                name=c.get("name", "Unnamed Campaign"),
                setting=c.get("setting", "Homebrew"),
                tone=c.get("tone", "high fantasy"),
                dm_notes=c.get("dm_notes", ""),
            )

        emit({"type": "status", "text": f"📍 Placing {len(world_data.get('locations', []))} locations on the map..."})

        # Step 3: Persist locations
        for loc in world_data.get("locations", []):
            world.upsert_location(campaign_id, loc)

        emit({"type": "status", "text": f"🧙 Creating {len(world_data.get('npcs', []))} NPCs..."})

        # Step 4: Persist NPCs
        for npc in world_data.get("npcs", []):
            world.upsert_npc(campaign_id, npc)

        emit({"type": "status", "text": f"⚔️ Establishing {len(world_data.get('factions', []))} factions..."})

        # Step 5: Persist factions
        for fac in world_data.get("factions", []):
            world.upsert_faction(campaign_id, fac)

        # Step 6: Persist plot threads
        for pt in world_data.get("plot_threads", []):
            world.upsert_plot_thread(campaign_id, pt)

        # Step 7: Persist lore
        for le in world_data.get("lore_entries", []):
            world.add_lore(campaign_id, le.get("title", "Untitled"), le.get("category", "misc"), le.get("content", ""))

        # Step 8: Queue clarifications if needed
        for q_text in world_data.get("clarifications_needed", []):
            world.add_clarification(campaign_id, q_text)

        emit({"type": "status", "text": "✅ Campaign world created!"})
        emit({"type": "campaign_created", "campaign_id": campaign_id, "data": world_data})

        return {"campaign_id": campaign_id, "world": world_data}

    # ── Session Ingestion ──────────────────────────────────────────────
    def ingest_session(self, campaign_id: int, session_notes: str, event_queue: queue.Queue = None) -> dict:
        def emit(event: dict):
            if event_queue:
                event_queue.put(event)

        snapshot = world.get_world_snapshot(campaign_id)
        emit({"type": "status", "text": "📖 Reading session notes..."})

        # Step 1: Parse session into structured events
        session_delta = self.session_ingestion.ingest(session_notes, snapshot)
        if not session_delta:
            return {}

        emit({"type": "status", "text": f"🔍 Checking for {len(session_delta.get('events', []))} world changes..."})

        # Step 2: Contradiction check before committing
        contradiction_report = self.contradiction_agent.check(
            json.dumps(session_delta), snapshot
        )
        if contradiction_report.get("has_contradictions"):
            for c in contradiction_report.get("contradictions", []):
                if c.get("severity") == "BLOCKING":
                    world.add_clarification(
                        campaign_id,
                        f"CONTRADICTION: {c.get('established_fact')} ↔ {c.get('new_claim')}",
                        context=c.get("suggested_resolution", ""),
                    )
            emit({"type": "contradictions", "data": contradiction_report})

        # Step 3: Save the session
        session_id = world.add_session(campaign_id, session_notes)

        # Step 4: Apply world changes
        emit({"type": "status", "text": "🌐 Propagating changes across the world..."})
        for npc in session_delta.get("updated_npcs", []):
            world.upsert_npc(campaign_id, npc)
        for loc in session_delta.get("updated_locations", []):
            world.upsert_location(campaign_id, loc)
        for npc in session_delta.get("new_npcs", []):
            world.upsert_npc(campaign_id, npc)
        for loc in session_delta.get("new_locations", []):
            world.upsert_location(campaign_id, loc)
        for le in session_delta.get("new_lore", []):
            world.add_lore(campaign_id, le.get("title", "Session Lore"), "session", le.get("content", ""))

        # Step 5: Emit events to the bus
        for event in session_delta.get("events", []):
            world.emit_event(campaign_id, event.get("event_type", "UNKNOWN"), event)

        # Step 6: Advance plot threads
        emit({"type": "status", "text": "📜 Advancing plot threads..."})
        fresh_snapshot = world.get_world_snapshot(campaign_id)
        plot_update = self.plot_weaver.advance_plots(session_delta.get("events", []), fresh_snapshot)
        for thread in plot_update.get("updated_threads", []):
            if thread.get("title"):
                world.upsert_plot_thread(campaign_id, thread)

        # Step 7: Faction reactions
        emit({"type": "status", "text": "🏰 Factions are responding..."})
        for event in session_delta.get("events", [])[:5]:  # Top 5 events
            self.faction_agent.propagate_event(event, fresh_snapshot)

        # Step 8: Queue DM clarifications
        for q_text in session_delta.get("clarifications_needed", []):
            world.add_clarification(campaign_id, q_text, context="Session ingestion")

        emit({"type": "session_ingested", "session_id": session_id, "delta": session_delta, "plot_update": plot_update})
        emit({"type": "status", "text": "✅ World updated!"})

        return {"session_id": session_id, "delta": session_delta, "plot_update": plot_update}

    # ── NPC Dialogue ───────────────────────────────────────────────────
    def get_npc_dialogue(self, campaign_id: int, npc_name: str, situation: str) -> str:
        snapshot = world.get_world_snapshot(campaign_id)
        return self.npc_agent.generate_dialogue(npc_name, situation, snapshot)

    # ── Encounter Generation ───────────────────────────────────────────
    def generate_encounter(self, campaign_id: int, party_level: int, party_size: int, difficulty: str, environment: str) -> dict:
        snapshot = world.get_world_snapshot(campaign_id)
        return self.rules_agent.generate_encounter(party_level, party_size, difficulty, environment, snapshot)

    # ── Lore Query ─────────────────────────────────────────────────────
    def query_lore(self, campaign_id: int, topic: str) -> str:
        snapshot = world.get_world_snapshot(campaign_id)
        return self.lore_keeper.generate_lore(topic, snapshot)

    # ── Plot Hooks ─────────────────────────────────────────────────────
    def get_plot_hooks(self, campaign_id: int, context: str = "") -> list[str]:
        snapshot = world.get_world_snapshot(campaign_id)
        if not context:
            active_threads = [t for t in snapshot.get("plot_threads", []) if t.get("status") == "active"]
            context = f"Active threads: {json.dumps([t['title'] for t in active_threads[:5]])}"
        return self.plot_weaver.generate_hooks(context, snapshot)
