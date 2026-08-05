from agents.base import BaseAgent

class CoderAgent(BaseAgent):
    name = "coder"
    use_fast_model = False
    default_system_prompt = """Solve coding interview problems for a new grad engineer.
Format:
APPROACH: 1 sentence strategy
CODE: clean TypeScript/JavaScript, typed, 10-25 lines
TIME: O(?) | SPACE: O(?)
EDGE CASES: 2-3 bullets
Write code you can type and explain live. No imports unless essential."""
