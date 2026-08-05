#!/usr/bin/env python3
"""
app.py – Engineering Agent Web Server
Run: python app.py  →  http://localhost:5001
"""
from __future__ import annotations

import json
import os
import queue
import threading
from pathlib import Path

import pathlib
from dotenv import load_dotenv
load_dotenv(dotenv_path=pathlib.Path(__file__).parent / ".env")

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

for d in ("logs", "reports", "memory", "checkpoints", "output"):
    os.makedirs(d, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_memory():
    from memory.store import memory
    return memory


def get_orchestrator():
    from orchestrator import Orchestrator
    return Orchestrator()


# ── Sessions ──────────────────────────────────────────────────────────────────

@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    return jsonify(get_memory().get_sessions(limit=100))


@app.route("/api/sessions", methods=["POST"])
def create_session():
    body = request.get_json(silent=True) or {}
    sid = get_memory().create_session(title=body.get("title") or None)
    return jsonify({"session_id": sid})


@app.route("/api/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
    mem = get_memory()
    session = mem.get_session(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404
    return jsonify({**session, "prompts": mem.get_prompts(session_id)})


# ── History ───────────────────────────────────────────────────────────────────

@app.route("/api/history", methods=["GET"])
def history():
    limit = int(request.args.get("limit", 100))
    return jsonify(get_memory().get_all_prompts(limit=limit))


# ── Run (SSE streaming) ───────────────────────────────────────────────────────

def _worker(goal: str, session_id: str, prompt_id: int, q: queue.Queue):
    try:
        get_orchestrator().run(goal, session_id=session_id, prompt_id=prompt_id, event_queue=q)
    except Exception as e:
        q.put({"type": "error", "text": str(e)})
    finally:
        q.put(None)


@app.route("/api/run", methods=["GET"])
def run_agent():
    goal = request.args.get("goal", "").strip()
    session_id = request.args.get("session_id", "").strip() or None
    if not goal:
        return jsonify({"error": "No goal provided"}), 400

    mem = get_memory()
    session_id = mem.get_or_create_session(session_id)
    prompt_id = mem.log_prompt(session_id, goal)

    q: queue.Queue = queue.Queue()
    threading.Thread(target=_worker, args=(goal, session_id, prompt_id, q), daemon=True).start()

    def generate():
        yield f"data: {json.dumps({'type': 'init', 'session_id': session_id, 'prompt_id': prompt_id})}\n\n"
        while True:
            try:
                # Heartbeat every 20s keeps the SSE stream alive while agents are thinking
                item = q.get(timeout=20)
                if item is None:
                    break
                yield f"data: {json.dumps(item)}\n\n"
            except queue.Empty:
                # Send a keep-alive comment — browsers ignore it, but it prevents stream timeout
                yield ": heartbeat\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Scaffold + Download ───────────────────────────────────────────────────────

@app.route("/api/scaffold", methods=["POST"])
def scaffold_project():
    """Generate a full project zip from a natural-language description."""
    data = request.get_json(force=True)
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"error": "description is required"}), 400

    mem = get_memory()
    sid = mem.get_or_create_session()
    pid = mem.log_prompt(sid, description)

    result = {}

    def _run():
        from agents.scaffolder import ScaffolderAgent
        agent = ScaffolderAgent()
        try:
            zip_path = agent.scaffold(description, output_dir="output", prompt_id=pid, session_id=sid)
            mem.complete_prompt(pid)
            result["zip"] = Path(zip_path).name
            result["session_id"] = sid
        except Exception as e:
            result["error"] = str(e)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=120)

    if "error" in result:
        return jsonify({"error": result["error"]}), 500
    if "zip" not in result:
        return jsonify({"error": "Scaffold timed out"}), 500
    return jsonify(result)


@app.route("/api/download/<filename>", methods=["GET"])
def download_file(filename: str):
    """Download a generated zip from the output directory."""
    return send_from_directory(os.path.abspath("output"), filename, as_attachment=True)


# ── Reports ───────────────────────────────────────────────────────────────────

@app.route("/api/reports", methods=["GET"])
def list_reports():
    reports_dir = Path("reports")
    if not reports_dir.exists():
        return jsonify([])
    files = sorted(reports_dir.glob("*.md"), reverse=True)
    return jsonify([{"filename": f.name, "size": f.stat().st_size} for f in files[:100]])


@app.route("/api/reports/<filename>", methods=["GET"])
def get_report(filename: str):
    path = Path("reports") / filename
    if not path.exists():
        return jsonify({"error": "Not found"}), 404
    return jsonify({"filename": filename, "content": path.read_text(encoding="utf-8")})


@app.route("/api/prompts/<int:prompt_id>/report", methods=["GET"])
def prompt_report(prompt_id: int):
    mem = get_memory()
    row = mem.conn.execute("SELECT * FROM prompts WHERE id=?", (prompt_id,)).fetchone()
    if not row:
        return jsonify({"error": "Prompt not found"}), 404
    rpath = row["report_path"]
    if not rpath or not Path(rpath).exists():
        return jsonify({"error": "Report not yet generated"}), 404
    return jsonify({"filename": Path(rpath).name, "content": Path(rpath).read_text(encoding="utf-8")})


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
def stats():
    mem = get_memory()
    return jsonify({
        "success_rate": mem.get_success_rate(),
        "total_sessions": mem.conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"],
        "total_prompts": mem.conn.execute("SELECT COUNT(*) as c FROM prompts").fetchone()["c"],
        "total_tasks": mem.conn.execute("SELECT COUNT(*) as c FROM tasks").fetchone()["c"],
        "recent_sessions": mem.get_sessions(limit=5),
        "recent_tasks": mem.get_recent_tasks(10),
    })


@app.route("/api/logs", methods=["GET"])
def list_logs():
    log_dir = Path("logs")
    if not log_dir.exists():
        return jsonify([])
    files = sorted(log_dir.glob("*.txt"), reverse=True)
    return jsonify([{"filename": f.name, "size": f.stat().st_size} for f in files[:100]])


# ── Static ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    print("\n🤖  Engineering Agent System")
    print("    http://localhost:5001\n")
    app.run(debug=False, port=5001, threaded=True)