#!/usr/bin/env python3
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import json
import os
import time
import queue
import threading
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(BASE_DIR, "logs")
TRANSCRIPT_DIR = os.path.join(BASE_DIR, "transcripts")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)


def run_parallel_streaming(goal: str, q: queue.Queue):
    """Run the parallel orchestrator and push SSE events into the queue."""
    try:
        from orchestrator import ParallelOrchestrator
        orchestrator = ParallelOrchestrator()

        run_start = time.time()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        all_events = []
        agent_results = []  # (group_id, agent, task, result, duration_ms)

        def on_event(event):
            q.put(event)
            all_events.append(event)
            if event.get("type") == "agent_done":
                agent_results.append(event)

        orchestrator.run(goal, event_callback=on_event)

        # ── Build full transcript ──────────────────────────────────────
        total_duration = round(time.time() - run_start, 2)
        lines = []
        lines.append("=" * 72)
        lines.append("SWARM — PARALLEL AI AGENT TRANSCRIPT")
        lines.append("=" * 72)
        lines.append(f"Timestamp : {timestamp}")
        lines.append(f"Duration  : {total_duration}s")
        lines.append(f"Agents run: {len(agent_results)}")
        lines.append("")
        lines.append("GOAL / PROMPT")
        lines.append("-" * 72)
        lines.append(goal)
        lines.append("")

        # Orchestrator reasoning
        for ev in all_events:
            if ev.get("type") == "reasoning":
                lines.append("ORCHESTRATOR REASONING")
                lines.append("-" * 72)
                lines.append(ev.get("text", ""))
                lines.append("")
                break

        # Group plan
        for ev in all_events:
            if ev.get("type") == "plan":
                groups = ev.get("groups", [])
                lines.append("EXECUTION PLAN")
                lines.append("-" * 72)
                for g in groups:
                    agents_in_g = [a["agent"] for a in g.get("agents", [])]
                    lines.append(f"  Wave {g['group_id']}: [{', '.join(agents_in_g)}]  — {g.get('description','')}")
                lines.append("")
                break

        # Each agent's output
        current_group = None
        for ev in all_events:
            if ev.get("type") == "group_start":
                gid = ev["group_id"]
                lines.append("")
                lines.append(f"{'─'*72}")
                lines.append(f"WAVE {gid} — {ev.get('description','')}  ({ev.get('agent_count',0)} agents in parallel)")
                lines.append(f"{'─'*72}")
                current_group = gid

            elif ev.get("type") == "agent_done":
                agent = ev.get("agent", "?")
                task = ev.get("task", "")
                result = ev.get("result", "")
                duration_ms = ev.get("duration_ms", 0)
                lines.append("")
                lines.append(f"▸ AGENT: {agent.upper().replace('_', ' ')}  ({duration_ms}ms)")
                lines.append(f"  Task: {task}")
                lines.append("")
                # indent output
                for line in result.splitlines():
                    lines.append(f"  {line}")
                lines.append("")

            elif ev.get("type") == "agent_error":
                agent = ev.get("agent", "?")
                lines.append(f"▸ AGENT: {agent.upper()}  [ERROR]")
                lines.append(f"  {ev.get('error','')}")
                lines.append("")

        lines.append("=" * 72)
        lines.append("END OF TRANSCRIPT")
        lines.append("=" * 72)

        transcript_text = "\n".join(lines)
        transcript_filename = f"{timestamp}_transcript.txt"
        transcript_path = os.path.join(TRANSCRIPT_DIR, transcript_filename)
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)

        # Also save raw JSON log
        log_path = os.path.join(LOG_DIR, f"{timestamp}_parallel_run.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump({"goal": goal, "timestamp": timestamp, "events": all_events}, f, indent=2)

        # Tell the frontend the transcript is ready
        q.put({
            "type": "transcript_ready",
            "filename": transcript_filename,
            "text": transcript_text,
            "duration": total_duration
        })

    except Exception as e:
        q.put({"type": "error", "text": str(e)})
    finally:
        q.put(None)  # sentinel


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/run", methods=["GET"])
def run_agent():
    goal = request.args.get("goal", "").strip()
    if not goal:
        return jsonify({"error": "No goal provided"}), 400

    q = queue.Queue()
    thread = threading.Thread(target=run_parallel_streaming, args=(goal, q), daemon=True)
    thread.start()

    def generate():
        while True:
            item = q.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/improve", methods=["POST"])
def trigger_improve():
    def do_improve():
        from loops.improvement import run_improvement_cycle
        run_improvement_cycle()
    threading.Thread(target=do_improve, daemon=True).start()
    return jsonify({"status": "improvement cycle started"})


@app.route("/api/status", methods=["GET"])
def get_status():
    from memory.store import memory
    rate = memory.get_success_rate()
    recent = memory.get_recent_tasks(10)
    learnings = memory.get_learnings(limit=10)
    improvements = memory.conn.execute(
        "SELECT * FROM improvements ORDER BY id DESC LIMIT 5"
    ).fetchall()
    return jsonify({
        "success_rate": round(rate, 3),
        "recent_tasks": recent,
        "learnings": learnings,
        "improvements": [dict(r) for r in improvements],
    })


@app.route("/api/transcripts", methods=["GET"])
def list_transcripts():
    if not os.path.exists(TRANSCRIPT_DIR):
        return jsonify([])
    files = sorted(os.listdir(TRANSCRIPT_DIR), reverse=True)
    result = []
    for f in files:
        if f.endswith("_transcript.txt"):
            path = os.path.join(TRANSCRIPT_DIR, f)
            size = os.path.getsize(path)
            result.append({"filename": f, "size": size})
    return jsonify(result)


@app.route("/api/transcripts/<filename>", methods=["GET"])
def get_transcript(filename):
    path = os.path.join(TRANSCRIPT_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "Not found"}), 404
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return jsonify({"filename": filename, "content": content})


@app.route("/api/logs", methods=["GET"])
def list_logs():
    if not os.path.exists(LOG_DIR):
        return jsonify([])
    files = sorted(os.listdir(LOG_DIR), reverse=True)
    logs = []
    for f in files:
        path = os.path.join(LOG_DIR, f)
        size = os.path.getsize(path)
        logs.append({"filename": f, "size": size})
    return jsonify(logs)


@app.route("/api/logs/<filename>", methods=["GET"])
def get_log(filename):
    path = os.path.join(LOG_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "Not found"}), 404
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return jsonify({"filename": filename, "content": content})


if __name__ == "__main__":
    print("Starting Parallel AI Agent System at http://localhost:5000")
    app.run(debug=True, port=5000, threaded=True)
