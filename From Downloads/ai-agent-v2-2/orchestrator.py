"""
micro1 Interview Co-Pilot Orchestrator
───────────────────────────────────────
You paste the AI interviewer's question → we instantly give you the best answer.

Token strategy:
- ClassifierAgent (Haiku, ~100ms): detects question type
- SpeedTipAgent (Haiku, parallel with classifier): instant 1-liner
- One primary Sonnet agent fires based on type
- Total: 2 Haiku calls + 1 Sonnet call per question
"""
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from agents.base import BaseAgent
from agents.classifier import ClassifierAgent
from agents.behavioral import BehavioralAgent
from agents.js_explainer import JSExplainerAgent
from agents.coder import CoderAgent
from agents.debugger import DebuggerAgent
from agents.fullstack import FullstackAgent
from agents.motivation import MotivationAgent
from agents.speed_tip import SpeedTipAgent
from memory.store import memory
from loops.improvement import run_improvement_cycle

# Route question type → primary answer agent name
ROUTING = {
    "behavioral":  "behavioral",
    "coding":      "coder",
    "js_concept":  "js_explainer",
    "fullstack":   "fullstack",
    "debugging":   "debugger",
    "motivation":  "motivation",
}

AGENT_LABELS = {
    "behavioral":   ("Behavioral Answer",   "#aed581"),
    "coder":        ("Code Solution",       "#69f0ae"),
    "js_explainer": ("JS/TS Concept",       "#4fc3f7"),
    "fullstack":    ("Fullstack Answer",    "#80cbc4"),
    "debugger":     ("Debug Fix",           "#ff8a65"),
    "motivation":   ("Why micro1 / Role",  "#ce93d8"),
    "speed_tip":    ("Speed Tip",           "#fff176"),
    "classifier":   ("Classifier",          "#b388ff"),
}


class CopilotOrchestrator:
    def __init__(self):
        self.classifier = ClassifierAgent()
        self.speed_tip  = SpeedTipAgent()
        self.agents = {
            "behavioral":   BehavioralAgent(),
            "coder":        CoderAgent(),
            "js_explainer": JSExplainerAgent(),
            "fullstack":    FullstackAgent(),
            "debugger":     DebuggerAgent(),
            "motivation":   MotivationAgent(),
        }
        self._lock = threading.Lock()

    def run(self, question: str, event_callback: Optional[Callable] = None) -> list:
        def emit(e):
            if event_callback: event_callback(e)

        emit({"type": "status", "text": "Classifying..."})

        # ── Wave 1: Classifier + SpeedTip in parallel (both Haiku) ──────────
        emit({"type": "group_start", "group_id": "wave1",
              "description": "Triage", "agent_count": 2})

        classification = {}
        speed_tip_result = ""

        def do_classify():
            try:
                raw = self.classifier.call(question)
                return json.loads(raw)
            except:
                return {"type": "fullstack", "urgency": "normal"}

        def do_speed_tip():
            return self.speed_tip.call(question)

        with ThreadPoolExecutor(max_workers=2) as ex:
            f_cls = ex.submit(do_classify)
            f_tip = ex.submit(do_speed_tip)

            emit({"type": "agent_start", "group_id": "wave1",
                  "agent": "classifier", "task": question[:80]})
            emit({"type": "agent_start", "group_id": "wave1",
                  "agent": "speed_tip", "task": question[:80]})

            for f in as_completed([f_cls, f_tip]):
                if f is f_cls:
                    classification = f.result()
                    emit({"type": "agent_done", "group_id": "wave1",
                          "agent": "classifier", "task": question[:80],
                          "result": json.dumps(classification), "duration_ms": 0, "chars": 30})
                else:
                    speed_tip_result = f.result()
                    emit({"type": "agent_done", "group_id": "wave1",
                          "agent": "speed_tip", "task": question[:80],
                          "result": speed_tip_result, "duration_ms": 0,
                          "chars": len(speed_tip_result)})

        q_type = classification.get("type", "fullstack")
        emit({"type": "classified", "q_type": q_type,
              "difficulty": classification.get("urgency", "normal"), "topic": q_type})
        emit({"type": "group_done", "group_id": "wave1", "outputs": 2})

        # ── Wave 2: Primary answer agent (Sonnet) ────────────────────────────
        agent_name = ROUTING.get(q_type, "fullstack")
        agent = self.agents[agent_name]
        label, _ = AGENT_LABELS.get(agent_name, ("Answer", "#888"))

        emit({"type": "group_start", "group_id": "wave2",
              "description": label, "agent_count": 1})
        emit({"type": "agent_start", "group_id": "wave2",
              "agent": agent_name, "task": question[:80]})

        t0 = time.time()
        try:
            answer = agent.call(question)
            duration_ms = int((time.time() - t0) * 1000)
            emit({"type": "agent_done", "group_id": "wave2",
                  "agent": agent_name, "task": question[:80],
                  "result": answer, "duration_ms": duration_ms, "chars": len(answer)})
        except Exception as e:
            emit({"type": "agent_error", "group_id": "wave2",
                  "agent": agent_name, "error": str(e)})
            answer = ""

        emit({"type": "group_done", "group_id": "wave2", "outputs": 1})
        emit({"type": "done", "total_groups": 2, "total_outputs": 3})

        # Auto-improve every 20 questions
        count = memory.conn.execute("SELECT COUNT(*) as c FROM tasks").fetchone()["c"]
        if count > 0 and count % 20 == 0:
            threading.Thread(target=run_improvement_cycle, daemon=True).start()

        return [speed_tip_result, answer]


# aliases
Orchestrator = CopilotOrchestrator
ParallelOrchestrator = CopilotOrchestrator
