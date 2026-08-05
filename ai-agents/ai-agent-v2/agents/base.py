from dotenv import load_dotenv
load_dotenv()
import time
import anthropic
from config import config
from memory.store import memory

client = anthropic.Anthropic(api_key=config.anthropic_api_key)

# Shared role context — injected into every agent so they never
# waste tokens re-explaining the role or candidate background.
ROLE_CONTEXT = """Role: Software Engineer, New Grad — fullstack.
Stack: Fullstack, JS/TS, React, Node.js.
Interview focus: Fullstack Fundamentals, JS/TS Proficiency, Problem Solving & Debugging, Ownership & Learning Velocity.
Candidate profile: New grad, eager, fast learner. Answers should sound natural, confident, not memorized."""

class BaseAgent:
    name: str = "base"
    default_system_prompt: str = "You are a helpful AI agent."
    use_fast_model: bool = True

    def __init__(self):
        saved = memory.get_active_prompt(self.name)
        self.system_prompt = saved if saved else self.default_system_prompt
        self.model = config.model_fast if self.use_fast_model else config.model_smart
        self.max_tokens = config.max_tokens_fast if self.use_fast_model else config.max_tokens_smart

    def call(self, user_message: str, context: str = "") -> str:
        # System = role context + agent instructions (saves tokens vs repeating in user turn)
        full_system = f"{ROLE_CONTEXT}\n\n{self.system_prompt}"
        messages = []
        if context:
            messages.append({"role": "user", "content": context[:600]})
            messages.append({"role": "assistant", "content": "Got it."})
        messages.append({"role": "user", "content": user_message})

        start = time.time()
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=full_system,
                messages=messages
            )
            output = response.content[0].text
            duration_ms = int((time.time() - start) * 1000)
            memory.log_task(user_message[:150], self.name, "success", output[:400], duration_ms, True)
            return output
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            memory.log_task(user_message[:150], self.name, "error", str(e), duration_ms, False)
            raise
