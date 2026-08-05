from agents.base import BaseAgent

class SpeedTipAgent(BaseAgent):
    name = "speed_tip"
    use_fast_model = True
    default_system_prompt = """Give a 1-sentence tip for answering this interview question confidently.
Start with the most important thing to say first. No preamble. Max 30 words."""
