import json
from agents.base import BaseAgent
from memory.store import memory

class ReflectorAgent(BaseAgent):
    name = "reflector"
    use_fast_model = False
    default_system_prompt = """Analyze interview session data. Return JSON only:
{"successes":["..."],"failures":["..."],"prompt_issues":[{"agent":"...","issue":"...","suggested_fix":"..."}],"improvement_proposals":[{"priority":"high|medium|low","description":"..."}]}"""

    def reflect(self):
        recent = memory.get_recent_tasks(20)
        rate = memory.get_success_rate()
        result = self.call(f"Success:{rate:.0%}\nTasks:{json.dumps(recent[:10])}")
        try:
            data = json.loads(result)
            for s in data.get("successes", []):
                memory.log_learning("success", s)
            for f in data.get("failures", []):
                memory.log_learning("failure", f)
        except:
            memory.log_learning("reflection", result[:300])
        return result
