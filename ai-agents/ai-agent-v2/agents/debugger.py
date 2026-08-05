from agents.base import BaseAgent

class DebuggerAgent(BaseAgent):
    name = "debugger"
    use_fast_model = False
    default_system_prompt = """Debug code shown in an interview. Be fast and precise.
Format:
BUG: exactly what's wrong (1 sentence)
WHY: why it breaks (1 sentence)
FIX: corrected code only (no surrounding fluff)
PREVENT: 1-line tip to avoid this class of bug
Under 150 words."""
