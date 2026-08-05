"""
reports.py – Generate full Markdown reports for completed engineering runs.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from config import config


AGENT_DESCRIPTIONS = {
    "code_gen": "Code Generation",
    "code_review": "Code Review",
    "debugger": "Debug & Fix",
    "researcher": "Research & Requirements",
    "optimizer": "Performance Optimization",
    "documenter": "Documentation",
    "requirements": "Requirements Analysis",
    "reflector": "Self-Reflection",
    "agent_builder": "Agent Improvement",
}


def _agent_label(name: str) -> str:
    return AGENT_DESCRIPTIONS.get(name, name.replace("_", " ").title())


def _badge(text: str, colour: str = "blue") -> str:
    """Return a simple markdown bold badge."""
    return f"**`{text}`**"


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
    Build a comprehensive Markdown report and save it to disk.

    Returns the file path of the saved report.
    """
    Path(config.reports_dir).mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow()
    ts_human = ts.strftime("%Y-%m-%d %H:%M UTC")
    filename = f"report_{ts.strftime('%Y%m%d_%H%M%S')}_prompt{prompt_id}.md"
    filepath = Path(config.reports_dir) / filename

    successful_steps = [s for s in steps if s.get("success", True)]
    failed_steps = [s for s in steps if not s.get("success", True)]
    total_s = total_duration_ms / 1000

    lines: List[str] = []

    # ── Header ────────────────────────────────────────────────────────────
    lines += [
        "# 🤖 Engineering Agent Run Report",
        "",
        f"> **Prompt ID:** `{prompt_id}` · **Session:** `{session_id[:8]}…` · **Generated:** {ts_human}",
        "",
        "---",
        "",
        "## 📋 Objective",
        "",
        f"> {prompt}",
        "",
    ]

    # ── Executive Summary ─────────────────────────────────────────────────
    lines += [
        "## ⚡ Executive Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Steps | {len(steps)} |",
        f"| Successful | {len(successful_steps)} |",
        f"| Failed | {len(failed_steps)} |",
        f"| Total Runtime | {total_s:.1f}s |",
        f"| Agents Used | {', '.join(sorted(set(s['agent'] for s in steps)))} |",
        "",
    ]

    # ── Orchestrator Reasoning ─────────────────────────────────────────────
    if reasoning:
        lines += [
            "## 🧠 Orchestrator Reasoning",
            "",
            reasoning,
            "",
        ]

    # ── Execution Plan ─────────────────────────────────────────────────────
    if plan:
        lines += ["## 📐 Execution Plan", ""]
        for i, step in enumerate(plan, 1):
            lines.append(f"{i}. **[{_agent_label(step['agent'])}]** — {step['task']}")
        lines.append("")

    # ── Step-by-Step Results ──────────────────────────────────────────────
    lines += ["## 🔬 Sub-Agent Activity", ""]

    for step in steps:
        agent = step.get("agent", "unknown")
        task = step.get("task", "")
        result = step.get("result", "")
        duration = step.get("duration_ms", 0)
        step_num = step.get("step", "?")
        success = step.get("success", True)

        status_icon = "✅" if success else "❌"

        lines += [
            f"### {status_icon} Step {step_num}: {_agent_label(agent)}",
            "",
            f"**Agent:** `{agent}` · **Duration:** `{duration}ms`",
            "",
            f"**Task:** {task}",
            "",
            "**Output:**",
            "",
        ]

        # Detect if output contains code blocks — preserve them, otherwise wrap
        if "```" in result:
            lines.append(result)
        else:
            lines += [
                "<details>",
                f"<summary>View full output ({len(result)} chars)</summary>",
                "",
                result,
                "",
                "</details>",
            ]
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── Implemented Artifacts ─────────────────────────────────────────────
    # Extract code blocks from all results
    all_code: List[tuple] = []
    for step in steps:
        result = step.get("result", "")
        for m in re.finditer(r"```(\w+)\n(.*?)```", result, re.DOTALL):
            lang, code = m.group(1), m.group(2).strip()
            if lang not in ("", "text", "bash", "shell", "sh") and len(code) > 50:
                all_code.append((lang, code, step.get("agent", "unknown")))

    if all_code:
        lines += ["## 🗂️ Implemented Code Artifacts", ""]
        for i, (lang, code, agent) in enumerate(all_code, 1):
            lines += [
                f"### Artifact {i} — `{lang}` (from `{agent}`)",
                "",
                f"```{lang}",
                code,
                "```",
                "",
            ]

    # ── Metrics ───────────────────────────────────────────────────────────
    if steps:
        lines += [
            "## 📊 Performance Metrics",
            "",
            "| Step | Agent | Duration | Status |",
            "|------|-------|----------|--------|",
        ]
        for step in steps:
            icon = "✅" if step.get("success", True) else "❌"
            lines.append(
                f"| {step.get('step','?')} | {_agent_label(step.get('agent','?'))} "
                f"| {step.get('duration_ms', 0)}ms | {icon} |"
            )
        lines.append("")

    # ── Footer ────────────────────────────────────────────────────────────
    lines += [
        "---",
        "",
        f"*Report generated by Engineering Agent System · {ts_human}*",
        "",
    ]

    content = "\n".join(lines)
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)
