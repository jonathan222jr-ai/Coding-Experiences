"""
mic.py — Microphone capture + Whisper transcription for the interview co-pilot.

Usage modes:
  1. python3 main.py listen          # hold ENTER to record, release to transcribe + answer
  2. python3 main.py listen --loop   # continuous — keeps listening after each answer
  3. python3 main.py listen --file recording.wav  # transcribe an existing audio file

Dependencies (install once):
  pip install sounddevice soundfile openai-whisper numpy

Whisper model is downloaded once (~39 MB for 'base') and cached locally.
Everything runs offline — no API key needed for transcription.
"""

import sys
import threading
import tempfile
import os
import time

# ── Lazy imports so missing packages give a clear message ───────────────────
def _require(pkg, install_name=None):
    import importlib
    try:
        return importlib.import_module(pkg)
    except ModuleNotFoundError:
        name = install_name or pkg
        print(f"\n❌  Missing package: {name}")
        print(f"    Run: pip install {name}\n")
        sys.exit(1)


# ── Core recorder ────────────────────────────────────────────────────────────
class MicRecorder:
    """
    Records audio from the default microphone.
    Call start() / stop() or use as a context manager.
    """
    SAMPLE_RATE = 16_000   # Whisper expects 16 kHz
    CHANNELS    = 1        # mono

    def __init__(self):
        self.sd = _require("sounddevice")
        self.np = _require("numpy")
        self._frames = []
        self._stream = None

    def start(self):
        self._frames = []
        self._stream = self.sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> "np.ndarray":
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._frames:
            return self.np.array([], dtype="float32")
        return self.np.concatenate(self._frames, axis=0).flatten()

    def _callback(self, indata, frames, time_info, status):
        self._frames.append(indata.copy())

    # context manager support
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        return self.stop()


# ── Whisper transcriber ──────────────────────────────────────────────────────
class Transcriber:
    MODEL_NAME = "base"   # tiny / base / small / medium / large — base is fastest+accurate enough

    def __init__(self):
        self._model = None

    def _load(self):
        if self._model is None:
            whisper = _require("whisper", "openai-whisper")
            print("  Loading Whisper model (first run downloads ~39 MB)…", end=" ", flush=True)
            self._model = whisper.load_model(self.MODEL_NAME)
            print("ready.")
        return self._model

    def transcribe_array(self, audio_np, sample_rate=16_000) -> str:
        """Transcribe a numpy float32 audio array."""
        np = _require("numpy")
        model = self._load()
        # Whisper expects float32 at 16 kHz
        result = model.transcribe(audio_np.astype("float32"), fp16=False)
        return result["text"].strip()

    def transcribe_file(self, path: str) -> str:
        """Transcribe an existing .wav / .mp3 / .m4a file."""
        model = self._load()
        result = model.transcribe(path, fp16=False)
        return result["text"].strip()


# ── Save array → tmp WAV ─────────────────────────────────────────────────────
def _save_wav(audio_np, sample_rate: int) -> str:
    sf = _require("soundfile")
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    sf.write(tmp.name, audio_np, sample_rate)
    return tmp.name


# ── Pretty printer ───────────────────────────────────────────────────────────
def _run_agents(question: str):
    """Run the orchestrator and print results exactly like `ask` does."""
    print(f"\n🎤  Transcribed: \"{question}\"\n")
    if not question:
        print("  (nothing heard — try again)")
        return

    from orchestrator import CopilotOrchestrator
    orc = CopilotOrchestrator()

    def on_event(e):
        t = e.get("type")
        if t == "agent_done":
            agent = e["agent"]
            if agent in ("classifier",):
                return   # skip noisy internal events in voice mode
            label = agent.upper().replace("_", " ")
            print(f"\n{'─'*60}")
            print(f"  {label}")
            print(f"{'─'*60}")
            print(e["result"])

    orc.run(question, event_callback=on_event)
    print(f"\n{'═'*60}\n")


# ── Main entry points called from main.py ────────────────────────────────────
def listen_once(hint: str = ""):
    """
    Record until the user releases ENTER, then transcribe + answer.
    """
    _require("sounddevice")
    _require("numpy")

    recorder    = MicRecorder()
    transcriber = Transcriber()

    print("\n🎙️  Interview Prep Agent — Voice Mode")
    print("   Press  ENTER  to start recording.")
    print("   Press  ENTER  again to stop and get your answer.")
    if hint:
        print(f"   Tip: {hint}")
    print()

    input("   ▶  Press ENTER to start recording… ")
    print("   🔴  Recording… (speak now)")
    recorder.start()
    t_start = time.time()

    input("   ⏹  Press ENTER to stop… ")
    audio = recorder.stop()
    duration = round(time.time() - t_start, 1)
    print(f"   Captured {duration}s — transcribing…")

    if len(audio) < 3_200:   # < 0.2 s at 16kHz — nothing recorded
        print("  ⚠️  Recording too short. Check your microphone.\n")
        return ""

    text = transcriber.transcribe_array(audio, MicRecorder.SAMPLE_RATE)
    _run_agents(text)
    return text


def listen_loop():
    """Continuous loop — keeps listening after each answer until Ctrl+C."""
    print("\n🎙️  Interview Prep Agent — Continuous Voice Mode  (Ctrl+C to quit)\n")
    while True:
        try:
            listen_once()
        except KeyboardInterrupt:
            print("\n\n  👋  Voice mode exited.\n")
            break


def listen_file(path: str):
    """Transcribe an existing audio file and run agents on it."""
    if not os.path.exists(path):
        print(f"❌  File not found: {path}")
        sys.exit(1)
    transcriber = Transcriber()
    print(f"  Transcribing {path}…")
    text = transcriber.transcribe_file(path)
    _run_agents(text)
