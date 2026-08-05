from agents.base import BaseAgent

class ClassifierAgent(BaseAgent):
    name = "classifier"
    use_fast_model = True
    default_system_prompt = """Classify the interview question. JSON only, no prose:
{"type":"behavioral|coding|js_concept|fullstack|debugging|motivation","urgency":"fast|normal"}
Types: behavioral=tell me about/experience, coding=write code/algorithm, js_concept=explain JS/TS, fullstack=react/node/api/db, debugging=find the bug, motivation=why role/company."""
