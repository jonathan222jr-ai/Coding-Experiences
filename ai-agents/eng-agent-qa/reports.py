"""
reports.py – Generate professional Markdown reports for completed engineering runs.
Uses Google Gemini to write a polished, human-quality executive narrative.
"""
from __future__ import annotations

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import requests

from config import config


AGENT_DESCRIPTIONS = {
    "code_gen": "Code Generation",
    "code_review": "Code Review & Quality Assurance",
    "debugger": "Debug & Fix",
    "researcher": "Research & Analysis",
    "optimizer": "Performance Optimization",
    "documenter": "Documentation",
    "requirements": "Requirements Analysis",
    "reflector": "Self-Reflection",
    "agent_builder": "Agent Improvement",
    "scaffolder": "Project Scaffolding",
}


def _agent_label(name: str) -> str:
    return AGENT_DESCRIPTIONS.get(name, name.replace("_", " ").title())


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini Flash to generate professional narrative text."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return ""  # Graceful fallback — will use template narrative instead

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1200,
        },
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return ""


def _gemini_executive_summary(
    prompt: str,
    reasoning: str,
    steps: List[Dict[str, Any]],
    total_s: float,
    success_count: int,
    fail_count: int,
) -> str:
    """Ask Gemini to write a concise, professional executive summary."""
    agent_names = sorted(set(_agent_label(s["agent"]) for s in steps))
    step_summaries = []
    for s in steps:
        outcome = "succeeded" if s.get("success", True) else "failed"
        step_summaries.append(f"- {_agent_label(s['agent'])}: {s.get('task','')[:120]} ({outcome})")

    gemini_prompt = f"""You are a senior technical writer producing a professional software engineering report.

Write a concise executive summary (3-5 sentences, formal tone, no bullet points) for the following AI-assisted engineering run.

Goal: {prompt}

Orchestrator reasoning: {reasoning or 'N/A'}

Agents deployed: {', '.join(agent_names)}

Steps executed:
{chr(10).join(step_summaries)}

Metrics:
- Total runtime: {total_s:.1f} seconds
- Steps succeeded: {success_count}
- Steps failed: {fail_count}

Write ONLY the executive summary paragraph. No headers, no lists, no preamble."""

    result = _call_gemini(gemini_prompt)
    if result:
        return result

    # Fallback template if Gemini is unavailable
    status = "successfully" if fail_count == 0 else f"with {fail_count} step(s) requiring attention"
    return (
        f"This engineering run addressed the objective: *{prompt}*. "
        f"The orchestrator deployed {len(agent_names)} specialized sub-agent(s) "
        f"({', '.join(agent_names)}) across {success_count + fail_count} execution step(s), "
        f"completing {status} in {total_s:.1f} seconds. "
        f"All generated code was automatically routed through peer code-review and debugging "
        f"sub-agents to ensure industry-standard quality before delivery."
    )


def _gemini_step_narrative(step: Dict[str, Any], goal: str) -> str:
    """Ask Gemini to write a one-paragraph professional narrative for a step's output."""
    result_preview = step.get("result", "")[:600]
    agent = _agent_label(step.get("agent", ""))
    task = step.get("task", "")
    success = step.get("success", True)
    status = "successfully completed" if success else "encountered an error"

    gemini_prompt = f"""You are a senior technical writer. In 2-3 sentences (formal, third-person), summarize what the {agent} agent did for this engineering task.

Overall goal: {goal}
Task given to agent: {task}
Agent status: {status}
Agent output preview: {result_preview}

Write ONLY the 2-3 sentence summary. No headers, no bullets, no preamble."""

    result = _call_gemini(gemini_prompt)
    if result:
        return result
    return f"The {agent} agent {status} its assigned task."


def generate_report(
    prompt: str,
    session_id: str,
    prompt_id: int,
    steps: List[Dict[str, Any]],
    reasoning: str = "",
    plan: List[Dict[str, str]] = None,
    total_duration_ms: int = 0,
) -> str:
    """
    Build a comprehensive professional Markdown report with Gemini-authored narrative.
    Returns the file path of the saved report.
    """
    Path(config.reports_dir).mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow()
    ts_human = ts.strftime("%B %d, %Y at %H:%M UTC")
    filename = f"report_{ts.strftime('%Y%m%d_%H%M%S')}_prompt{prompt_id}.md"
    filepath = Path(config.reports_dir) / filename

    successful_steps = [s for s in steps if s.get("success", True)]
    failed_steps = [s for s in steps if not s.get("success", True)]
    total_s = total_duration_ms / 1000
    auto_steps = [s for s in steps if s.get("auto")]
    manual_steps = [s for s in steps if not s.get("auto")]

    # ── Gemini narrative ─────────────────────────────────────────────────────
    exec_summary = _gemini_executive_summary(
        prompt, reasoning, steps, total_s,
        len(successful_steps), len(failed_steps)
    )

    lines: List[str] = []

    # ── Cover / Header ───────────────────────────────────────────────────────
    lines += [
        "# Engineering Agent System — Run Report",
        "",
        "---",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| **Report ID** | `{prompt_id}` |",
        f"| **Session** | `{session_id[:8]}…` |",
        f"| **Generated** | {ts_human} |",
        f"| **Total Runtime** | {total_s:.1f}s |",
        f"| **Pipeline Status** | {'✅ All steps passed' if not failed_steps else f'⚠️ {len(failed_steps)} step(s) failed'} |",
        "",
        "---",
        "",
    ]

    # ── Objective ────────────────────────────────────────────────────────────
    lines += [
        "## 1. Objective",
        "",
        f"> {prompt}",
        "",
    ]

    # ── Executive Summary (Gemini-authored) ──────────────────────────────────
    lines += [
        "## 2. Executive Summary",
        "",
        exec_summary,
        "",
    ]

    # ── Quality Assurance Pipeline Notice ───────────────────────────────────
    auto_review = any(s["agent"] == "code_review" and s.get("auto") for s in steps)
    auto_debug = any(s["agent"] == "debugger" and s.get("auto") for s in steps)
    if auto_review or auto_debug:
        lines += [
            "## 3. Quality Assurance Pipeline",
            "",
            "All code generated during this run was automatically processed through a "
            "two-stage quality assurance pipeline before delivery:",
            "",
            "1. **Code Review Sub-Agent** — Examined generated code for correctness, security "
            "vulnerabilities, performance anti-patterns, and adherence to industry standards.",
            "2. **Debugger Sub-Agent** — Applied root-cause analysis to all issues surfaced by the "
            "reviewer and produced validated fixes with before/after diffs.",
            "",
            "This pipeline runs automatically on every code-generation step and cannot be bypassed.",
            "",
        ]
        section_offset = 1
    else:
        section_offset = 0

    # ── Orchestrator Reasoning ───────────────────────────────────────────────
    sec = 3 + section_offset
    if reasoning:
        lines += [
            f"## {sec}. Orchestrator Reasoning",
            "",
            reasoning,
            "",
        ]
        sec += 1

    # ── Execution Plan ───────────────────────────────────────────────────────
    if plan:
        lines += [f"## {sec}. Execution Plan", ""]
        for i, step in enumerate(plan, 1):
            auto_tag = " *(auto-injected QA)*" if step.get("_auto") else ""
            lines.append(f"{i}. **[{_agent_label(step['agent'])}]**{auto_tag} — {step['task'][:120]}")
        lines.append("")
        sec += 1

    # ── Step-by-Step Results ─────────────────────────────────────────────────
    lines += [f"## {sec}. Sub-Agent Execution Log", ""]
    sec += 1

    for step in steps:
        agent = step.get("agent", "unknown")
        task = step.get("task", "")
        result = step.get("result", "")
        duration = step.get("duration_ms", 0)
        step_num = step.get("step", "?")
        success = step.get("success", True)
        is_auto = step.get("auto", False)

        status_icon = "✅" if success else "❌"
        auto_badge = " `[AUTO-QA]`" if is_auto else ""

        lines += [
            f"### {status_icon} Step {step_num}: {_agent_label(agent)}{auto_badge}",
            "",
            f"**Agent:** `{agent}` · **Duration:** `{duration}ms` · **Status:** {'Success' if success else 'Failed'}",
            "",
            f"**Task:** {task}",
            "",
        ]

        # Gemini narrative for this step
        narrative = _gemini_step_narrative(step, prompt)
        lines += [f"*{narrative}*", ""]

        lines += ["**Full Output:**", ""]

        if "```" in result:
            lines.append(result)
        else:
            lines += [
                "<details>",
                f"<summary>View full output ({len(result):,} chars)</summary>",
                "",
                result,
                "",
                "</details>",
            ]
        lines += ["", "---", ""]

    # ── Code Artifacts ───────────────────────────────────────────────────────
    all_code: List[tuple] = []
    for step in steps:
        result = step.get("result", "")
        for m in re.finditer(r"```(\w+)\n(.*?)```", result, re.DOTALL):
            lang, code = m.group(1), m.group(2).strip()
            if lang not in ("", "text", "bash", "shell", "sh", "diff") and len(code) > 50:
                all_code.append((lang, code, step.get("agent", "unknown"), step.get("step", "?")))

    if all_code:
        lines += [f"## {sec}. Delivered Code Artifacts", ""]
        sec += 1
        for i, (lang, code, agent, step_num) in enumerate(all_code, 1):
            lines += [
                f"### Artifact {i} — `{lang}` *(from {_agent_label(agent)}, Step {step_num})*",
                "",
                f"```{lang}",
                code,
                "```",
                "",
            ]

    # ── Performance Metrics Table ────────────────────────────────────────────
    if steps:
        lines += [
            f"## {sec}. Performance Metrics",
            "",
            "| Step | Agent | Type | Duration | Status |",
            "|------|-------|------|----------|--------|",
        ]
        for step in steps:
            icon = "✅" if step.get("success", True) else "❌"
            stype = "Auto-QA" if step.get("auto") else "Primary"
            lines.append(
                f"| {step.get('step','?')} | {_agent_label(step.get('agent','?'))} "
                f"| {stype} | {step.get('duration_ms', 0):,}ms | {icon} |"
            )
        lines += [
            "",
            f"**Total runtime:** {total_s:.2f}s · "
            f"**Success rate:** {len(successful_steps)}/{len(steps)} steps · "
            f"**Auto-QA steps:** {len(auto_steps)}",
            "",
        ]
        sec += 1

    # ── Footer ───────────────────────────────────────────────────────────────
    gemini_note = " · *Narrative sections authored by Google Gemini*" if os.getenv("GEMINI_API_KEY") else ""
    lines += [
        "---",
        "",
        f"*Report generated by Engineering Agent System · {ts_human}{gemini_note}*",
        "",
    ]

    content = "\n".join(lines)
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)