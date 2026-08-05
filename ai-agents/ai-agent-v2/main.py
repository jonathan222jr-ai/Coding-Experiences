#!/usr/bin/env python3
import click
from dotenv import load_dotenv
load_dotenv()

@click.group()
def cli():
    """Interview Prep Agent — practice interview assistant"""
    pass

@cli.command()
def serve():
    """Start co-pilot at http://localhost:5000"""
    import subprocess, sys
    print("Starting Interview Prep Agent at http://localhost:5000")
    subprocess.run([sys.executable, "app.py"])

@cli.command()
@click.argument("question")
def ask(question):
    """Test a question from the CLI."""
    from orchestrator import CopilotOrchestrator
    orc = CopilotOrchestrator()
    def on_event(e):
        if e.get("type") == "agent_done":
            print(f"\n[{e['agent']}]\n{e['result']}")
    orc.run(question, event_callback=on_event)

if __name__ == "__main__":
    cli()
