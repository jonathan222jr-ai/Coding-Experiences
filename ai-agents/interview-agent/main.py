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

@cli.command()
@click.option("--loop",  is_flag=True, help="Keep listening after each answer (Ctrl+C to quit).")
@click.option("--file",  "audio_file", default=None, help="Transcribe an existing audio file instead of recording.")
def listen(loop, audio_file):
    """🎙  Record your voice, transcribe it, and get an instant answer.

    \b
    Examples:
      python3 main.py listen              # record once, get answer
      python3 main.py listen --loop       # keep going until Ctrl+C
      python3 main.py listen --file q.wav # transcribe an existing file

    \b
    Install deps first (one-time):
      pip install sounddevice soundfile openai-whisper numpy
    """
    from mic import listen_once, listen_loop, listen_file

    if audio_file:
        listen_file(audio_file)
    elif loop:
        listen_loop()
    else:
        listen_once()

if __name__ == "__main__":
    cli()
