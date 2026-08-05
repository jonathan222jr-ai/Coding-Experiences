#!/usr/bin/env python3
"""
main.py – CLI for the Engineering Agent System

Usage:
  python main.py goal "Write a FastAPI auth service"
  python main.py scaffold "FastAPI service with JWT and PostgreSQL"
  python main.py status
  python main.py reflect
  python main.py improve
  python main.py research "Dagster partition strategies"
  python main.py fix path/to/file.py
  python main.py serve
"""
import click
from dotenv import load_dotenv
load_dotenv()


@click.group()
def cli():
    """🤖 Engineering Agent System — multi-agent AI for daily engineering work."""
    pass


@cli.command()
@click.argument("objective")
@click.option("--session", "-s", default=None, help="Session ID to append to")
def goal(objective, session):
    """Run the full agent pipeline on an engineering objective."""
    from memory.store import memory
    from orchestrator import Orchestrator

    sid = memory.get_or_create_session(session)
    pid = memory.log_prompt(sid, objective)
    steps = Orchestrator().run(objective, session_id=sid, prompt_id=pid)

    click.echo("\n" + "═" * 60)
    click.echo(f"✅  Completed {len(steps)} step(s) | Session: {sid[:8]}…")
    for s in steps:
        icon = "✓" if s["success"] else "✗"
        click.echo(f"  {icon} [{s['agent']}] {s['duration_ms']}ms")
    click.echo("═" * 60)


@cli.command()
@click.argument("description")
@click.option("--output", "-o", default="output", help="Directory to save the zip")
def scaffold(description, output):
    """Generate a complete project as a downloadable zip file."""
    from agents.scaffolder import ScaffolderAgent
    from memory.store import memory

    click.echo(f"⚙️  Scaffolding: {description}")
    sid = memory.get_or_create_session()
    pid = memory.log_prompt(sid, description)
    agent = ScaffolderAgent()
    zip_path = agent.scaffold(description, output_dir=output, prompt_id=pid, session_id=sid)
    memory.complete_prompt(pid)
    click.echo(f"✅  Project zip ready: {zip_path}")


@cli.command()
def status():
    """Show system status and recent activity."""
    from memory.store import memory
    rate = memory.get_success_rate()
    sessions = memory.get_sessions(5)
    recent = memory.get_recent_tasks(10)

    click.echo(f"\n{'═'*50}")
    click.echo("  Engineering Agent System — Status")
    click.echo(f"{'═'*50}")
    click.echo(f"  Success rate (last 50 tasks): {rate:.1%}")
    click.echo(f"\n  Recent sessions:")
    for s in sessions:
        click.echo(f"    [{s['session_id'][:8]}] {s['title']} — {s['total_prompts']} prompts")
    click.echo(f"\n  Recent tasks:")
    for t in recent:
        icon = "✓" if t["success"] else "✗"
        click.echo(f"    {icon} [{t['agent']:12}] {t['goal'][:55]}…")
    click.echo("")


@cli.command()
def reflect():
    """Run the self-reflection agent against recent task history."""
    from agents.all_agents import ReflectorAgent
    click.echo(ReflectorAgent().reflect())


@cli.command()
def improve():
    """Trigger a manual self-improvement cycle."""
    from loops.improvement import run_improvement_cycle
    run_improvement_cycle()


@cli.command()
@click.argument("topic")
def research(topic):
    """Research a technical topic using the ResearchAgent."""
    from agents.all_agents import ResearchAgent
    from memory.store import memory
    sid = memory.get_or_create_session()
    pid = memory.log_prompt(sid, topic)
    result = ResearchAgent().call(f"Research this topic thoroughly: {topic}", prompt_id=pid, session_id=sid)
    memory.complete_prompt(pid)
    click.echo(result)


@cli.command()
@click.argument("file")
def fix(file):
    """Debug and fix a source file."""
    from agents.all_agents import DebuggerAgent
    from memory.store import memory
    try:
        content = open(file).read()
    except FileNotFoundError:
        click.echo(f"Error: File not found: {file}")
        raise SystemExit(1)
    sid = memory.get_or_create_session()
    pid = memory.log_prompt(sid, f"Fix file: {file}")
    result = DebuggerAgent().call(f"Analyze and fix this file:\n\n```\n{content}\n```", prompt_id=pid, session_id=sid)
    memory.complete_prompt(pid)
    click.echo(result)


@cli.command()
def serve():
    """Start the web UI server at http://localhost:5001."""
    import subprocess, sys
    subprocess.run([sys.executable, "app.py"])


if __name__ == "__main__":
    cli()
