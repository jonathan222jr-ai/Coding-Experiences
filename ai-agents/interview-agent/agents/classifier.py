"""
ClassifierAgent — uses Haiku to classify the interview question type.
Returns a JSON string: {"type": "...", "urgency": "..."}
"""
from agents.base import BaseAgent


class ClassifierAgent(BaseAgent):
    name = "classifier"
    use_fast_model = True   # Haiku — fast triage

    default_system_prompt = """\
Classify the interview question into exactly one type and one urgency level.

TYPES (pick one):
- behavioral    → STAR stories, teamwork, conflict, growth, failure, feedback
- coding        → algorithms, data structures, LeetCode-style problems, complexity
- js_concept    → JS/TS language concepts (closures, promises, event loop, types, etc.)
- fullstack     → system design, REST APIs, React patterns, Node architecture, DB design
- debugging     → find the bug, fix the code, explain the error
- motivation    → "why micro1", "why this role", career goals, strengths/weaknesses

URGENCY (pick one):
- fast    → simple recall / 1-liner answer
- normal  → moderate depth expected
- deep    → multi-part or design question, needs structure

Respond ONLY with valid JSON, no explanation, no markdown:
{"type": "<type>", "urgency": "<urgency>"}"""
