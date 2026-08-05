import json
from agents.reflector import ReflectorAgent
from agents.agent_builder import AgentBuilderAgent
from memory.store import memory

def run_improvement_cycle():
    reflector = ReflectorAgent()
    reflection = reflector.reflect()
    try:
        data = json.loads(reflection)
        issues = data.get("prompt_issues", [])
    except:
        return
    builder = AgentBuilderAgent()
    for issue in issues:
        name = issue.get("agent")
        if not name: continue
        prompt = memory.get_active_prompt(name)
        if prompt:
            builder.improve_agent(name, reflection, prompt)
