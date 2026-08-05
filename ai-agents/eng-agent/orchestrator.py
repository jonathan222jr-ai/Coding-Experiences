"""
orchestrator.py – Routes engineering goals through specialized sub-agents.
"""
from __future__ import annotations

import json
import time

import anthropic

from agents import (
    CodeGenAgent, CodeReviewAgent, DebuggerAgent, ResearchAgent,
    OptimizerAgent, DocumenterAgent, RequirementsAgent,
    ReflectorAgent, AgentBuilderAgent, ScaffolderAgent,
)
from agents.base import client
from config import config
from memory.store import memory

AGENTS = {
    "code_gen": CodeGenAgent,
    "code_review": CodeReviewAgent,
    "debugger": DebuggerAgent,
    "researcher": ResearchAgent,
    "optimizer": OptimizerAgent,
    "documenter": DocumenterAgent,
    "requirements": RequirementsAgent,
    "reflector": ReflectorAgent,
    "agent_builder": AgentBuilderAgent,
    "scaffolder": ScaffolderAgent,
}

ORCHESTRATOR_PROMPT = """You are the Master Orchestrator of an engineering AI system.

Given a user goal, respond with a JSON plan:
{
  "reasoning": "Why these agents in this order",
  "steps": [
    {"agent": "<agent_name>", "task": "<specific task description>"}
  ]
}

Available agents and their roles:
- code_gen: Write clean, production-ready code with tests
- code_review: Review code for correctness, security, performance
- debugger: Root-cause analysis and fixes for broken code/systems
- researcher: Research tech topics, translate requirements to specs
- optimizer: Performance profiling and architectural improvements
- documenter: Generate README, API docs, runbooks
- requirements: Analyze and clarify stakeholder requirements
- scaffolder: Generate a complete, runnable project as a downloadable zip file

Rules:
- Choose agents that directly serve the goal
- Max 5 steps per run
- Each step should build on the previous
- Be specific in task descriptions — give the agent real context

Respond ONLY with valid JSON."""


class Orchestrator:
    def __init__(self):
        self.agents = {name: cls() for name, cls in AGENTS.items()}

    def plan(self, goal: str) -> dict:
        response = client.messages.create(
            model=config.model,
            max_tokens=1024,
            system=ORCHESTRATOR_PROMPT,
            messages=[{"role": "user", "content": goal}],
        )
        plan_text = response.content[0].text
        try:
            return json.loads(plan_text)
        except json.JSONDecodeError:
            goal_lower = goal.lower()
            if any(w in goal_lower for w in ["fix", "bug", "error", "crash", "debug"]):
                agent = "debugger"
            elif any(w in goal_lower for w in ["scaffold", "generate project", "create project", "new project", "boilerplate"]):
                agent = "scaffolder"
            elif any(w in goal_lower for w in ["review", "check", "audit", "security"]):
                agent = "code_review"
            elif any(w in goal_lower for w in ["research", "how", "what", "explain", "best practice"]):
                agent = "researcher"
            elif any(w in goal_lower for w in ["optimize", "performance", "slow", "faster"]):
                agent = "optimizer"
            elif any(w in goal_lower for w in ["document", "readme", "docs", "api doc"]):
                agent = "documenter"
            elif any(w in goal_lower for w in ["require", "spec", "stakeholder", "feature"]):
                agent = "requirements"
            else:
                agent = "code_gen"
            return {"reasoning": "Fallback routing.", "steps": [{"agent": agent, "task": goal}]}

    def run(
        self,
        goal: str,
        session_id: str = None,
        prompt_id: int = None,
        event_queue=None,
    ) -> list:
        def emit(event: dict):
            if event_queue is not None:
                event_queue.put(event)

        emit({"type": "status", "text": "Orchestrator planning…"})
        plan = self.plan(goal)

        reasoning = plan.get("reasoning", "")
        steps = plan.get("steps", [])

        if reasoning:
            emit({"type": "reasoning", "text": reasoning})
        emit({"type": "plan", "steps": [{"agent": s["agent"], "task": s["task"]} for s in steps]})

        results = []
        step_records = []
        run_start = time.time()

        for i, step in enumerate(steps, 1):
            agent_name = step["agent"]
            task = step["task"]

            emit({"type": "step_start", "step": i, "agent": agent_name, "task": task})

            agent = self.agents.get(agent_name)
            if not agent:
                emit({"type": "step_error", "step": i, "agent": agent_name, "error": f"Unknown agent: {agent_name}"})
                continue

            context = "\n\n---\n\n".join(results[-2:]) if results else ""
            step_start = time.time()

            try:
                # ScaffolderAgent uses scaffold() which returns a zip path
                if agent_name == "scaffolder" and hasattr(agent, "scaffold"):
                    zip_path = agent.scaffold(
                        task,
                        output_dir=config.output_dir,
                        prompt_id=prompt_id,
                        session_id=session_id,
                    )
                    result = f"✅ Project generated: {zip_path}"
                    duration_ms = int((time.time() - step_start) * 1000)
                    results.append(result)
                    rec = {
                        "step": i, "agent": agent_name, "task": task,
                        "result": result, "duration_ms": duration_ms,
                        "success": True, "zip_path": zip_path,
                    }
                else:
                    result = agent.call(
                        task,
                        context=context,
                        prompt_id=prompt_id,
                        session_id=session_id,
                        step_number=i,
                    )
                    duration_ms = int((time.time() - step_start) * 1000)
                    results.append(result)
                    rec = {
                        "step": i, "agent": agent_name, "task": task,
                        "result": result, "duration_ms": duration_ms,
                        "success": True,
                    }
                step_records.append(rec)
                emit({"type": "step_done", **rec})

            except Exception as e:
                duration_ms = int((time.time() - step_start) * 1000)
                err = str(e)
                rec = {
                    "step": i, "agent": agent_name, "task": task,
                    "result": f"ERROR: {err}", "duration_ms": duration_ms,
                    "success": False,
                }
                step_records.append(rec)
                emit({"type": "step_error", "step": i, "agent": agent_name, "error": err})

        total_ms = int((time.time() - run_start) * 1000)

        from reports import generate_report
        report_path = generate_report(
            prompt=goal,
            session_id=session_id or "cli",
            prompt_id=prompt_id or 0,
            steps=step_records,
            reasoning=reasoning,
            plan=steps,
            total_duration_ms=total_ms,
        )

        if prompt_id:
            memory.complete_prompt(prompt_id, report_path=report_path)

        emit({"type": "done", "total_steps": len(steps), "report_path": report_path, "total_ms": total_ms})

        # Auto self-improvement every 10 tasks
        task_count = memory.conn.execute("SELECT COUNT(*) as c FROM tasks").fetchone()["c"]
        if task_count > 0 and task_count % 10 == 0:
            from loops.improvement import run_improvement_cycle
            run_improvement_cycle()

        return step_records
