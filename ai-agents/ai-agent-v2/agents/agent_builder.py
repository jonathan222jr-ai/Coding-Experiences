import json
from datetime import datetime
from pathlib import Path
from agents.base import BaseAgent
from memory.store import memory
from config import config

class AgentBuilderAgent(BaseAgent):
    name = "agent_builder"
    use_fast_model = False
    default_system_prompt = 'Improve agent prompts. Return JSON: {"agent_name":"...","new_prompt":"...","rationale":"..."}'

    def improve_agent(self, agent_name, reflection, current_prompt):
        self._checkpoint(agent_name, current_prompt)
        result = self.call(f"Agent:{agent_name}\nPrompt:{current_prompt[:400]}\nReflection:{reflection[:800]}")
        try:
            data = json.loads(result)
            new_prompt = data.get("new_prompt", "")
            if new_prompt:
                rows = memory.conn.execute("SELECT MAX(version) as v FROM agent_prompts WHERE agent_name=?", (agent_name,)).fetchone()
                version = (rows["v"] or 0) + 1
                memory.save_agent_prompt(agent_name, new_prompt, version)
                imp_id = memory.log_improvement("agent_builder", f"{agent_name} v{version}: {data.get('rationale','')}")
                memory.mark_improvement_applied(imp_id)
                return f"Upgraded {agent_name} to v{version}"
        except: pass
        return "No change"

    def _checkpoint(self, agent_name, prompt):
        Path(config.checkpoint_dir).mkdir(exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        (Path(config.checkpoint_dir) / f"{agent_name}_{ts}.txt").write_text(prompt)
