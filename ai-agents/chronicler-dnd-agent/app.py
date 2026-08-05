#!/usr/bin/env python3
"""
app.py — D&D Campaign AI Agent Web Server
Run: python app.py  →  http://localhost:5001
"""
from __future__ import annotations

import json
import os
import queue
import threading
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

for d in ("logs", "reports", "memory", "checkpoints", "output", "lore"):
    os.makedirs(d, exist_ok=True)


def get_world():
    from memory.store import world
    return world


def get_orchestrator():
    from orchestrator import CampaignOrchestrator
    return CampaignOrchestrator()


# ── Campaigns ─────────────────────────────────────────────────────────

@app.route("/api/campaigns", methods=["GET"])
def list_campaigns():
    return jsonify(get_world().get_all_campaigns())


@app.route("/api/campaigns", methods=["POST"])
def create_campaign():
    data = request.get_json(force=True)
    name = data.get("name", "New Campaign")
    setting = data.get("setting", "Homebrew")
    tone = data.get("tone", "high fantasy")
    dm_notes = data.get("dm_notes", "")
    cid = get_world().create_campaign(name, setting, tone, dm_notes)
    return jsonify({"campaign_id": cid})


@app.route("/api/campaigns/<int:cid>", methods=["GET"])
def get_campaign(cid):
    w = get_world()
    campaign = w.get_campaign(cid)
    if not campaign:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        **campaign,
        "npcs": w.get_npcs(cid),
        "locations": w.get_locations(cid),
        "factions": w.get_factions(cid),
        "plot_threads": w.get_plot_threads(cid),
        "lore": w.get_lore(cid),
        "sessions": w.get_sessions(cid),
        "clarifications": w.get_pending_clarifications(cid),
    })


# ── AI World Building (SSE streaming) ─────────────────────────────────

def _build_world_worker(dm_prompt: str, campaign_id, q: queue.Queue):
    try:
        orch = get_orchestrator()
        result = orch.create_campaign(dm_prompt, campaign_id=campaign_id, event_queue=q)
    except Exception as e:
        q.put({"type": "error", "text": str(e)})
    finally:
        q.put(None)


@app.route("/api/campaigns/build", methods=["GET"])
def build_campaign():
    dm_prompt = request.args.get("prompt", "").strip()
    campaign_id = request.args.get("campaign_id")
    if campaign_id:
        try:
            campaign_id = int(campaign_id)
        except ValueError:
            campaign_id = None
    if not dm_prompt:
        return jsonify({"error": "prompt is required"}), 400

    q: queue.Queue = queue.Queue()
    threading.Thread(target=_build_world_worker, args=(dm_prompt, campaign_id, q), daemon=True).start()

    def generate():
        while True:
            try:
                item = q.get(timeout=30)
                if item is None:
                    break
                yield f"data: {json.dumps(item)}\n\n"
            except queue.Empty:
                yield ": heartbeat\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


# ── Session Ingestion (SSE streaming) ─────────────────────────────────

def _ingest_session_worker(cid: int, notes: str, q: queue.Queue):
    try:
        orch = get_orchestrator()
        result = orch.ingest_session(cid, notes, event_queue=q)
    except Exception as e:
        q.put({"type": "error", "text": str(e)})
    finally:
        q.put(None)


@app.route("/api/campaigns/<int:cid>/sessions", methods=["POST"])
def add_session(cid):
    data = request.get_json(force=True)
    notes = data.get("notes", "").strip()
    stream = data.get("stream", False)
    if not notes:
        return jsonify({"error": "notes required"}), 400

    if stream:
        q: queue.Queue = queue.Queue()
        threading.Thread(target=_ingest_session_worker, args=(cid, notes, q), daemon=True).start()

        def generate():
            while True:
                try:
                    item = q.get(timeout=30)
                    if item is None:
                        break
                    yield f"data: {json.dumps(item)}\n\n"
                except queue.Empty:
                    yield ": heartbeat\n\n"

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
        )
    else:
        session_id = get_world().add_session(cid, notes)
        return jsonify({"session_id": session_id})


# ── NPCs ──────────────────────────────────────────────────────────────

@app.route("/api/campaigns/<int:cid>/npcs", methods=["GET"])
def get_npcs(cid):
    return jsonify(get_world().get_npcs(cid))


@app.route("/api/campaigns/<int:cid>/npcs/<int:npc_id>", methods=["GET"])
def get_npc(cid, npc_id):
    npc = get_world().get_npc(npc_id)
    if not npc:
        return jsonify({"error": "Not found"}), 404
    return jsonify(npc)


@app.route("/api/campaigns/<int:cid>/npcs/<int:npc_id>/dialogue", methods=["POST"])
def npc_dialogue(cid, npc_id):
    data = request.get_json(force=True)
    situation = data.get("situation", "")
    npc = get_world().get_npc(npc_id)
    if not npc:
        return jsonify({"error": "NPC not found"}), 404
    dialogue = get_orchestrator().get_npc_dialogue(cid, npc["name"], situation)
    return jsonify({"dialogue": dialogue})


# ── Locations ─────────────────────────────────────────────────────────

@app.route("/api/campaigns/<int:cid>/locations", methods=["GET"])
def get_locations(cid):
    return jsonify(get_world().get_locations(cid))


# ── Map Data ──────────────────────────────────────────────────────────

@app.route("/api/campaigns/<int:cid>/map", methods=["GET"])
def get_map_data(cid):
    w = get_world()
    locations = w.get_locations(cid)
    factions = w.get_factions(cid)
    npcs = w.get_npcs(cid)
    # Enrich locations with faction control and NPC presence
    faction_map = {f["id"]: f for f in factions}
    return jsonify({
        "locations": locations,
        "factions": factions,
        "npc_count": len(npcs),
    })


# ── Encounters ────────────────────────────────────────────────────────

@app.route("/api/campaigns/<int:cid>/encounter", methods=["POST"])
def generate_encounter(cid):
    data = request.get_json(force=True)
    encounter = get_orchestrator().generate_encounter(
        cid,
        party_level=data.get("party_level", 1),
        party_size=data.get("party_size", 4),
        difficulty=data.get("difficulty", "medium"),
        environment=data.get("environment", "dungeon"),
    )
    return jsonify(encounter)


# ── Lore ──────────────────────────────────────────────────────────────

@app.route("/api/campaigns/<int:cid>/lore", methods=["GET"])
def get_lore(cid):
    return jsonify(get_world().get_lore(cid))


@app.route("/api/campaigns/<int:cid>/lore/query", methods=["POST"])
def query_lore(cid):
    data = request.get_json(force=True)
    topic = data.get("topic", "")
    lore = get_orchestrator().query_lore(cid, topic)
    return jsonify({"lore": lore})


# ── Plot Threads & Hooks ──────────────────────────────────────────────

@app.route("/api/campaigns/<int:cid>/plots", methods=["GET"])
def get_plots(cid):
    return jsonify(get_world().get_plot_threads(cid))


@app.route("/api/campaigns/<int:cid>/hooks", methods=["POST"])
def get_hooks(cid):
    data = request.get_json(force=True)
    context = data.get("context", "")
    hooks = get_orchestrator().get_plot_hooks(cid, context)
    return jsonify({"hooks": hooks})


# ── Factions ──────────────────────────────────────────────────────────

@app.route("/api/campaigns/<int:cid>/factions", methods=["GET"])
def get_factions(cid):
    return jsonify(get_world().get_factions(cid))


# ── Clarifications ────────────────────────────────────────────────────

@app.route("/api/campaigns/<int:cid>/clarifications", methods=["GET"])
def get_clarifications(cid):
    return jsonify(get_world().get_pending_clarifications(cid))


@app.route("/api/campaigns/<int:cid>/clarifications/<int:qid>", methods=["POST"])
def answer_clarification(cid, qid):
    data = request.get_json(force=True)
    answer = data.get("answer", "")
    get_world().answer_clarification(qid, answer)
    return jsonify({"ok": True})


# ── Static ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    print("\n🐉  D&D Campaign AI Agent System")
    print("    http://localhost:5001\n")
    app.run(debug=False, port=5001, threaded=True)
