"""
improvement.py — Self-improvement cycle.
Runs every 20 questions (triggered by orchestrator).
Reads recent task history, identifies weak spots, proposes better system prompts,
and saves them to the DB so agents pick them up on the next call.
"""
import json
import anthropic
from config import config
from memory.store import memory


def run_improvement_cycle():
    """
    Analyse recent task outputs and refine underperforming agent prompts.
    Runs in a background daemon thread — never blocks the main interview loop.
    """
    try:
        recent = memory.get_recent_tasks(limit=40)
        if not recent:
            return

        # ── 1. Find which agents have low success rate ──────────────────
        agent_stats: dict[str, dict] = {}
        for task in recent:
            agent = task.get("agent", "unknown")
            if agent not in agent_stats:
                agent_stats[agent] = {"total": 0, "success": 0, "outputs": []}
            agent_stats[agent]["total"] += 1
            agent_stats[agent]["success"] += int(task.get("success", 1))
            if len(agent_stats[agent]["outputs"]) < 3:
                agent_stats[agent]["outputs"].append(task.get("output", "")[:300])

        threshold = config.improvement_threshold
        weak_agents = [
            (name, stats)
            for name, stats in agent_stats.items()
            if stats["total"] >= 3
            and (stats["success"] / stats["total"]) < threshold
        ]

        if not weak_agents:
            memory.log_learning(
                category="improvement",
                insight="Auto-improvement cycle ran — all agents above threshold, no changes needed."
            )
            return

        client = anthropic.Anthropic(api_key=config.anthropic_api_key)

        for agent_name, stats in weak_agents:
            success_rate = stats["success"] / stats["total"]
            sample_outputs = "\n---\n".join(stats["outputs"])

            analysis_prompt = f"""\
You are improving an AI interview co-pilot agent called "{agent_name}".
Recent success rate: {success_rate:.0%} (target: {threshold:.0%}).

Sample recent outputs (may be errors or low-quality answers):
{sample_outputs}

Current system prompt for this agent (if stored):
{memory.get_active_prompt(agent_name) or "(using default)"}

Task: Write an improved system prompt for this agent that would produce \
higher-quality, more reliable answers. Focus on:
- Clearer output format constraints
- More specific domain guidance for the micro1 Zara new-grad interview
- Better error-avoidance for the patterns you see in the sample outputs

Return ONLY the new system prompt text — no explanation, no wrapper."""

            resp = client.messages.create(
                model=config.model_smart,
                max_tokens=500,
                messages=[{"role": "user", "content": analysis_prompt}],
            )
            new_prompt = resp.content[0].text.strip()

            # ── 2. Version and save the improved prompt ──────────────────
            existing = memory.get_active_prompt(agent_name)
            version = "v2" if not existing else _bump_version(existing)

            improvement_id = memory.log_improvement(
                proposed_by="improvement_loop",
                description=f"Auto-improved {agent_name} prompt (success rate was {success_rate:.0%})"
            )
            memory.save_agent_prompt(agent_name, new_prompt, version)
            memory.mark_improvement_applied(improvement_id)

            memory.log_learning(
                category="improvement",
                insight=f"Rewrote {agent_name} prompt ({version}) — was at {success_rate:.0%} success.",
                source_task_id=None,
            )

    except Exception as e:
        # Never crash the main thread
        try:
            memory.log_learning(
                category="improvement_error",
                insight=f"Improvement cycle failed: {str(e)[:200]}"
            )
        except Exception:
            pass


def _bump_version(current_prompt: str) -> str:
    """Generate a new version string based on timestamp."""
    import time
    return f"v{int(time.time())}"
