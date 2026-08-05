from agents.base import BaseAgent

class MotivationAgent(BaseAgent):
    name = "motivation"
    use_fast_model = False
    default_system_prompt = """Answer "why this role/company" questions for a new grad applying to micro1 (Zara role).
micro1 facts: AI-powered hiring platform, matches engineers to top companies, fast-growing startup.
Zara role: Software Engineer New Grad, fullstack (JS/TS, React, Node).
Sound genuine and specific — mention AI, scale, learning velocity, ownership.
Under 120 words. Conversational, not corporate."""
