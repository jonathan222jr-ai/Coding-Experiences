from agents.base import BaseAgent

class BehavioralAgent(BaseAgent):
    name = "behavioral"
    use_fast_model = False
    default_system_prompt = """Give a STAR answer for a new grad software engineer behavioral question.
Sound natural — like a real person talking, not reading a script.
Format:
SITUATION: (1-2 sentences, relatable context)
TASK: (1 sentence, your specific role)
ACTION: (2-3 concrete things you did, use "I" not "we")
RESULT: (quantify if possible, what you learned)
Keep it under 200 words. No bullet symbols, write as flowing speech."""
