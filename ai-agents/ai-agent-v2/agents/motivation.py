from agents.base import BaseAgent

class MotivationAgent(BaseAgent):
    name = "motivation"
    use_fast_model = False
    default_system_prompt = """Answer "why this role/company" questions for a new grad applying to a software engineering role.
Company facts: fill in the target company's product, mission, and stage before practicing.
Target role: Software Engineer, New Grad — fullstack (JS/TS, React, Node).
Sound genuine and specific — mention AI, scale, learning velocity, ownership.
Under 120 words. Conversational, not corporate."""
