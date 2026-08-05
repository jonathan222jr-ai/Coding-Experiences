"""
agents/base.py — Base class for all D&D world agents.
Every agent gets: world context injection, event bus awareness,
and the ability to emit structured world changes.
"""
from __future__ import annotations

import json
import time
from typing import Any

import anthropic
from config import config

client = anthropic.Anthropic(api_key=config.anthropic_api_key)


class BaseDnDAgent:
    name: str = "base"
    default_system_prompt: str = "You are a D&D world-building AI agent."

    def __init__(self):
        self.system_prompt = self.default_system_prompt

    def _build_world_context(self, snapshot: dict) -> str:
        """Compact world state formatted for prompt injection."""
        if not snapshot:
            return ""
        parts = []
        if snapshot.get("campaign"):
            c = snapshot["campaign"]
            parts.append(f"CAMPAIGN: {c.get('name','?')} | Setting: {c.get('setting','?')} | Tone: {c.get('tone','?')}")
        if snapshot.get("npcs"):
            npc_lines = [f"  - {n['name']} ({n.get('race','?')}, {n.get('current_status','?')}, {n.get('attitude_to_party','?')} to party)" for n in snapshot["npcs"][:20]]
            parts.append("NPCS:\n" + "\n".join(npc_lines))
        if snapshot.get("locations"):
            loc_lines = [f"  - {l['name']} ({l.get('loc_type','?')}, {l.get('status','?')})" for l in snapshot["locations"][:20]]
            parts.append("LOCATIONS:\n" + "\n".join(loc_lines))
        if snapshot.get("factions"):
            fac_lines = [f"  - {f['name']}: {(f.get('description') or '')[:80]}" for f in snapshot["factions"][:10]]
            parts.append("FACTIONS:\n" + "\n".join(fac_lines))
        if snapshot.get("plot_threads"):
            pt_lines = [f"  - [{p.get('status','?')}] {p['title']}" for p in snapshot["plot_threads"][:10]]
            parts.append("PLOT THREADS:\n" + "\n".join(pt_lines))
        return "\n\n".join(parts)

    def call(
        self,
        user_message: str,
        campaign_id: int = None,
        snapshot: dict = None,
        extra_context: str = "",
        max_tokens: int = None,
    ) -> str:
        messages = []
        if snapshot or extra_context:
            world_ctx = self._build_world_context(snapshot or {})
            ctx_parts = []
            if world_ctx:
                ctx_parts.append(f"=== CURRENT WORLD STATE ===\n{world_ctx}")
            if extra_context:
                ctx_parts.append(extra_context)
            if ctx_parts:
                messages.append({"role": "user", "content": "\n\n".join(ctx_parts)})
                messages.append({"role": "assistant", "content": "I have the world state. Ready for your task."})
        messages.append({"role": "user", "content": user_message})

        response = client.messages.create(
            model=config.model,
            max_tokens=max_tokens or config.max_tokens,
            system=self.system_prompt,
            messages=messages,
        )
        return response.content[0].text

    def call_json(self, user_message: str, campaign_id: int = None, snapshot: dict = None, extra_context: str = "") -> Any:
        """Call and parse JSON response."""
        result = self.call(user_message, campaign_id, snapshot, extra_context)
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception:
            pass
        try:
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception:
            pass
        return {"raw": result}
