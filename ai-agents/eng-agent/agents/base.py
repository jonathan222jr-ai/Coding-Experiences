from dotenv import load_dotenv
load_dotenv()

import time
import anthropic
from config import config
from memory.store import memory

client = anthropic.Anthropic(api_key=config.anthropic_api_key)


class BaseAgent:
    name: str = "base"
    default_system_prompt: str = "You are a helpful AI engineering agent."

    def __init__(self):
        saved = memory.get_active_prompt(self.name)
        self.system_prompt = saved if saved else self.default_system_prompt

    def call(
        self,
        user_message: str,
        context: str = "",
        prompt_id: int = None,
        session_id: str = None,
        step_number: int = 1,
    ) -> str:
        messages = []
        if context:
            messages.append({"role": "user", "content": f"Context from previous steps:\n{context}"})
            messages.append({"role": "assistant", "content": "Understood. I have the prior context and am ready for your task."})
        messages.append({"role": "user", "content": user_message})

        start = time.time()
        try:
            response = client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                system=self.system_prompt,
                messages=messages,
            )
            output = response.content[0].text
            duration_ms = int((time.time() - start) * 1000)
            memory.log_task(
                user_message[:200], self.name, "success",
                output[:2000], duration_ms, True,
                prompt_id=prompt_id, session_id=session_id, step_number=step_number,
            )
            return output
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            memory.log_task(
                user_message[:200], self.name, "error",
                str(e), duration_ms, False,
                prompt_id=prompt_id, session_id=session_id, step_number=step_number,
            )
            raise
