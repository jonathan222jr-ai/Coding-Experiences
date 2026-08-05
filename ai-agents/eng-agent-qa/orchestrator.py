"""
orchestrator.py – Routes engineering goals through specialized sub-agents.
Always enforces a code_gen → code_review → debugger review pipeline for code tasks.
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

# Agents that produce code and must go through review + debug pipeline
CODE_PRODUCING_AGENTS = {"code_gen", "scaffolder"}

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
- Max 5 steps per run (not counting automatic review/debug steps)
- Each step should build on the previous
- Be specific in task descriptions — give the agent real context
- For any goal involving code generation, your plan does NOT need to include code_review
  or debugger — they are automatically appended after every code_gen step.
- If the goal asks to "design and implement", "build", "create", or "deliver" a full
  application or service, use scaffolder (not debugger). Debugger is ONLY for fixing
  existing broken code.
- If the goal mentions delivering a ZIP, repository, or packaged project, always use scaffolder.

Respond ONLY with valid JSON."""


def _is_code_task(goal: str) -> bool:
    code_keywords = [
        "write", "create", "build", "implement", "generate", "code", "develop",
        "scaffold", "make", "add", "refactor", "fix", "new project", "boilerplate",
    ]
    return any(w in goal.lower() for w in code_keywords)


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

    def _inject_review_steps(self, steps: list, goal: str) -> list:
        """After every code-producing step, automatically inject code_review then debugger."""
        expanded = []
        for step in steps:
            expanded.append(step)
            if step["agent"] in CODE_PRODUCING_AGENTS:
                expanded.append({
                    "agent": "code_review",
                    "task": (
                        f"Review the code generated in the previous step for the goal: '{goal}'. "
                        "Check for correctness, security issues, performance problems, missing error "
                        "handling, and adherence to industry standards. Be thorough."
                    ),
                    "_auto": True,
                })
                expanded.append({
                    "agent": "debugger",
                    "task": (
                        f"Based on the code review findings for goal: '{goal}', identify any bugs, "
                        "logical errors, or issues flagged by the reviewer. Provide concrete fixes "
                        "with before/after diffs. If the review was clean, confirm correctness and "
                        "list any edge cases to watch."
                    ),
                    "_auto": True,
                })
        return expanded

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
        raw_steps = plan.get("steps", [])

        # Inject automatic review + debug after every code-producing step
        steps = self._inject_review_steps(raw_steps, goal)

        if reasoning:
            emit({"type": "reasoning", "text": reasoning})
        emit({"type": "plan", "steps": [{"agent": s["agent"], "task": s["task"]} for s in steps]})

        results = []
        step_records = []
        run_start = time.time()

        for i, step in enumerate(steps, 1):
            agent_name = step["agent"]
            task = step["task"]
            is_auto = step.get("_auto", False)

            emit({"type": "step_start", "step": i, "agent": agent_name, "task": task, "auto": is_auto})

            agent = self.agents.get(agent_name)
            if not agent:
                emit({"type": "step_error", "step": i, "agent": agent_name, "error": f"Unknown agent: {agent_name}"})
                continue

            context = "\n\n---\n\n".join(results[-2:]) if results else ""
            step_start = time.time()

            try:
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
                        "success": True, "zip_path": zip_path, "auto": is_auto,
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
                        "success": True, "auto": is_auto,
                    }
                step_records.append(rec)
                emit({"type": "step_done", **rec})

            except Exception as e:
                duration_ms = int((time.time() - step_start) * 1000)
                err = str(e)
                rec = {
                    "step": i, "agent": agent_name, "task": task,
                    "result": f"ERROR: {err}", "duration_ms": duration_ms,
                    "success": False, "auto": is_auto,
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

        # ── Auto-package: extract code from this run into a zip ────────────────
        zip_path = None
        try:
            from packager import ReportPackager
            zip_path = ReportPackager().package_from_steps(
                steps=step_records,
                prompt=goal,
                output_dir=config.output_dir,
            )
        except Exception as _pack_err:
            pass  # Packaging failure never kills the run

        emit({
            "type": "done",
            "total_steps": len(steps),
            "report_path": report_path,
            "zip_path": zip_path,
            "total_ms": total_ms,
        })

        task_count = memory.conn.execute("SELECT COUNT(*) as c FROM tasks").fetchone()["c"]
        if task_count > 0 and task_count % 10 == 0:
            from loops.improvement import run_improvement_cycle
            run_improvement_cycle()

        return step_records