"""
loops/improvement.py – Self-improvement cycle triggered after every 10 tasks.
"""
from memory.store import memory


def run_improvement_cycle():
    from agents import ReflectorAgent
    from agents import AgentBuilderAgent

    print("\n[Improvement Cycle] Reflecting on recent performance…")
    reflector = ReflectorAgent()
    try:
        insights = reflector.reflect()
        imp_id = memory.log_improvement("reflector", insights[:500])

        # Try to improve each active agent's prompt
        import json, re
        try:
            # Strip markdown fences if present
            clean = re.sub(r"```json|```", "", insights).strip()
            data = json.loads(clean)
            suggestions = data.get("prompt_improvements", [])
        except Exception:
            suggestions = []

        builder = AgentBuilderAgent()
        for s in suggestions[:3]:
            agent_name = s.get("agent")
            suggestion = s.get("suggestion", "")
            current_prompt = memory.get_active_prompt(agent_name) or ""
            if not current_prompt or not agent_name:
                continue
            try:
                new_prompt = builder.call(
                    f"Current prompt:\n{current_prompt}\n\nImprovement suggestion:\n{suggestion}\n\n"
                    "Return only the improved system prompt."
                )
                # Get current version
                row = memory.conn.execute(
                    "SELECT MAX(version) as v FROM agent_prompts WHERE agent_name=?",
                    (agent_name,),
                ).fetchone()
                version = (row["v"] or 0) + 1
                memory.save_agent_prompt(agent_name, new_prompt, version)
                memory.mark_improvement_applied(imp_id)
                print(f"  [+] Improved {agent_name} prompt → v{version}")
            except Exception as e:
                print(f"  [!] Could not improve {agent_name}: {e}")

    except Exception as e:
        print(f"  [!] Improvement cycle error: {e}")
    print("[Improvement Cycle] Done.\n")
