"""
agents/scaffolder.py – ScaffolderAgent

Generates a complete, runnable project from a natural-language description
and packages it as a downloadable zip file.
"""
from __future__ import annotations

import io
import json
import os
import re
import zipfile
from datetime import datetime

from agents.base import BaseAgent


class ScaffolderAgent(BaseAgent):
    name = "scaffolder"
    default_system_prompt = """You are a project scaffolding agent for a Python data platform
using FastAPI, PostgreSQL, Delta Lake, Dagster, ClickHouse, Docker, HashiCorp stack, and AWS.

Given a project description you will output a COMPLETE, RUNNABLE project as a JSON structure.

You MUST respond with only a JSON object in exactly this format — no prose before or after:
{
  "project_name": "snake_case_name",
  "description": "one line description",
  "files": {
    "relative/path/to/file.py": "full file content as a string",
    "another/file.py": "full file content"
  }
}

RULES:
- Every file must have complete, working content — no placeholders, no "# TODO: implement"
- Always include: main entrypoint, requirements.txt, Dockerfile, docker-compose.yml, .env.example, README.md
- Python files must have correct imports, type hints, and docstrings
- requirements.txt must contain only valid pip package specs (no comments, no shebangs)
- Use the stack: FastAPI + Pydantic v2 + SQLAlchemy async + structlog + python-dotenv
- Include at least one pytest test file under tests/
- All secrets via environment variables — never hardcoded
- Dockerfile must be multi-stage and run as non-root user"""

    def scaffold(
        self,
        description: str,
        output_dir: str = "output",
        *,
        prompt_id: int | None = None,
        session_id: str | None = None,
    ) -> str:
        """Generate a project from a description and return the path to the zip file."""
        raw = self.call(description, prompt_id=prompt_id, session_id=session_id)
        project = self._parse_response(raw)
        return self._build_zip(project, output_dir)

    def _parse_response(self, raw: str) -> dict:
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"No JSON object found in scaffolder response:\n{raw[:300]}")
        try:
            project = json.loads(cleaned[start:end])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Scaffolder returned invalid JSON: {exc}") from exc
        if "files" not in project or not project["files"]:
            raise ValueError("Scaffolder JSON missing 'files' key or files is empty.")
        return project

    def _build_zip(self, project: dict, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        project_name = project.get("project_name", "project").replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(output_dir, f"{project_name}_{timestamp}.zip")

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filepath, content in project["files"].items():
                clean_path = filepath.lstrip("/").lstrip("\\")
                zf.writestr(f"{project_name}/{clean_path}", content)
            manifest = {
                "project_name": project_name,
                "description": project.get("description", ""),
                "generated_at": timestamp,
                "files": list(project["files"].keys()),
            }
            zf.writestr(f"{project_name}/MANIFEST.json", json.dumps(manifest, indent=2))

        with open(zip_path, "wb") as f:
            f.write(buffer.getvalue())
        return os.path.abspath(zip_path)
