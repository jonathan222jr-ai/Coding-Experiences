"""
BaseAgent — shared call logic for all co-pilot agents.
Handles model selection, prompt loading (DB override or default),
API call, memory logging, and error wrapping.
"""
import time
import anthropic
from config import config

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.anthropic_api_key)
    return _client


class BaseAgent:
    name: str = "base"
    use_fast_model: bool = False          # True → Haiku, False → Sonnet
    default_system_prompt: str = "You are a helpful assistant."

    # ── public API ──────────────────────────────────────────────────────
    def call(self, user_message: str) -> str:
        system = self._get_system_prompt()
        model  = config.model_fast if self.use_fast_model else config.model_smart
        max_tokens = config.max_tokens_fast if self.use_fast_model else config.max_tokens_smart

        t0 = time.time()
        try:
            resp = _get_client().messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )
            result = resp.content[0].text
            duration_ms = int((time.time() - t0) * 1000)
            self._log(user_message, result, duration_ms, success=True)
            return result
        except Exception as e:
            duration_ms = int((time.time() - t0) * 1000)
            self._log(user_message, str(e), duration_ms, success=False)
            raise

    # ── internals ───────────────────────────────────────────────────────
    def _get_system_prompt(self) -> str:
        """Check DB for a live-updated prompt; fall back to default."""
        try:
            from memory.store import memory
            saved = memory.get_active_prompt(self.name)
            if saved:
                return saved
        except Exception:
            pass
        return self.default_system_prompt

    def _log(self, goal: str, output: str, duration_ms: int, success: bool):
        try:
            from memory.store import memory
            status = "success" if success else "error"
            memory.log_task(goal, self.name, status, output, duration_ms, success)
        except Exception:
            pass
