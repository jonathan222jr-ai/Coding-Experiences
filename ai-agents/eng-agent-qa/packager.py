"""
packager.py – ReportPackager

Reads a completed run report (Markdown), extracts the project structure
and all code blocks, maps them to real file paths, and writes a zip you
can actually run.

Called automatically at the end of every orchestrator run.
Can also be used standalone:
    from packager import ReportPackager
    zip_path = ReportPackager().package_from_report("reports/report_xxx.md")
"""
from __future__ import annotations

import io
import json
import os
import re
import zipfile
from pathlib import Path
from datetime import datetime


class ReportPackager:
    """Extracts generated code from a run report and packages it as a zip."""

    def package_from_steps(
        self,
        steps: list,
        prompt: str,
        output_dir: str = "output",
    ) -> str | None:
        """
        Build a zip directly from orchestrator step records.

        Walks every step result, finds code fences, pairs them with file paths
        extracted from any project-structure block, and writes a zip.

        Returns the zip path, or None if no code was found.
        """
        # Collect all text output from steps
        all_output = "\n\n".join(
            s.get("result", "") for s in steps if s.get("success") and s.get("result")
        )
        return self._build_zip_from_text(all_output, prompt, output_dir)

    def package_from_report(
        self,
        report_path: str,
        output_dir: str = "output",
    ) -> str | None:
        """Build a zip from a saved Markdown report file."""
        content = Path(report_path).read_text(encoding="utf-8")
        # Extract the objective line as the prompt
        prompt = "project"
        m = re.search(r"##\s+1\.\s+Objective\s*\n+>\s*(.+)", content)
        if m:
            prompt = m.group(1).strip()
        return self._build_zip_from_text(content, prompt, output_dir)

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _build_zip_from_text(self, text: str, prompt: str, output_dir: str) -> str | None:
        """Core logic: parse text, extract files, write zip."""
        file_map = self._extract_files(text)
        if not file_map:
            return None

        os.makedirs(output_dir, exist_ok=True)
        project_name = self._project_name_from_prompt(prompt)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(output_dir, f"{project_name}_{timestamp}.zip")

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filepath, content in file_map.items():
                arc_path = f"{project_name}/{filepath}"
                zf.writestr(arc_path, content)

            # Write a manifest
            manifest = {
                "project_name": project_name,
                "generated_at": timestamp,
                "prompt": prompt[:200],
                "files": sorted(file_map.keys()),
            }
            zf.writestr(f"{project_name}/MANIFEST.json", json.dumps(manifest, indent=2))

        with open(zip_path, "wb") as f:
            f.write(buffer.getvalue())

        return os.path.abspath(zip_path)

    def _extract_files(self, text: str) -> dict[str, str]:
        """
        Build a filepath → content mapping from the text.

        Strategy (in order of priority):
        1. Named file blocks:  lines like  ### `src/config.py`  or  # File: src/config.py
           followed by a code fence
        2. Project structure + indexed code fences:  match the tree listing to fenced blocks
        3. Fallback: keep every non-trivial code fence, name them sequentially
        """
        file_map: dict[str, str] = {}

        # ── Strategy 1: explicit file headers ──────────────────────────
        # Handles the agent output format:
        #   ### 1. Configuration (`app/config.py`)   ← most common
        #   ### `src/config.py`
        #   **File:** src/main.py
        #   # src/config.py   (comment header)
        #
        # Two-step approach: locate the heading/label position, then find
        # the immediately following code fence. This avoids the m.group(5)
        # IndexError that occurred in the old single-regex approach (which
        # only compiled 4 groups but tried to read a 5th).

        # Headings containing a filepath inside backticks (plain or paren-wrapped)
        filepath_in_heading = re.compile(
            r'^\#{1,4}[^\n]*?'
            r'(?:'
            r'`([\w][\w\-./]*\.[\w]+)`'           # `path/file.ext`
            r'|'
            r'\(`([\w][\w\-./]*\.[\w]+)`\)'        # (`path/file.ext`)
            r')',
            re.MULTILINE,
        )
        # **File:** or **Filename:** labels
        file_label = re.compile(
            r'\*\*(?:File|Filename):\*\*\s*`?([\w\-./]+\.[\w]+)`?'
        )
        # Bare comment header:  # path/file.ext
        comment_header = re.compile(
            r'^\s*#\s+([\w\-./]+\.[\w]+)\s*$', re.MULTILINE
        )

        next_fence = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)

        heading_positions: list[tuple[int, str]] = []
        for m in filepath_in_heading.finditer(text):
            fp = (m.group(1) or m.group(2) or '').strip()
            if fp:
                heading_positions.append((m.end(), fp))
        for m in file_label.finditer(text):
            heading_positions.append((m.end(), m.group(1).strip()))
        for m in comment_header.finditer(text):
            heading_positions.append((m.end(), m.group(1).strip()))

        for pos, filepath in heading_positions:
            segment = text[pos:pos + 8000]
            fm = next_fence.search(segment)
            if fm:
                code = fm.group(2).strip()
                if code and len(code) > 30 and filepath not in file_map:
                    file_map[filepath] = code

        if file_map:
            return file_map

        # ── Strategy 2: project structure tree + sequential code fences ─
        structure_paths = self._extract_structure_paths(text)
        code_blocks = self._extract_all_code_blocks(text)

        if structure_paths and code_blocks:
            # Filter code blocks to only substantial ones
            substantial = [
                (lang, code) for lang, code in code_blocks
                if len(code.strip()) > 100 and lang not in ("text", "bash", "shell", "sh", "")
            ]
            # Match structure paths to code blocks by index
            for i, (lang, code) in enumerate(substantial):
                if i < len(structure_paths):
                    file_map[structure_paths[i]] = code.strip()
                else:
                    # Extra blocks beyond the structure list — add with generated names
                    ext = self._lang_to_ext(lang)
                    file_map[f"src/extra_{i + 1}.{ext}"] = code.strip()
            if file_map:
                return file_map

        # ── Strategy 3: fallback — sequential naming ────────────────────
        counters: dict[str, int] = {}
        for lang, code in code_blocks:
            if len(code.strip()) < 100:
                continue
            ext = self._lang_to_ext(lang)
            counters[ext] = counters.get(ext, 0) + 1
            name = f"src/file_{counters[ext]}.{ext}"
            file_map[name] = code.strip()

        return file_map

    def _extract_structure_paths(self, text: str) -> list[str]:
        """
        Find a project-structure tree block and extract all file paths from it.
        Handles both plain-text trees and code-fenced trees.
        """
        paths: list[str] = []

        # Look for a fenced tree block first
        tree_fence = re.search(r"```(?:text|tree|)?\s*\n((?:.*\n)*?)```", text)
        tree_text = tree_fence.group(1) if tree_fence else ""

        # Also scan for indented tree lines outside fences
        if not tree_text:
            # Look for a "Project Structure" section heading followed by tree lines
            struct_section = re.search(
                r"(?:Project Structure|Directory Structure|File Structure)[^\n]*\n+((?:[^\n]*[├└│─][^\n]*\n)+)",
                text, re.IGNORECASE
            )
            if struct_section:
                tree_text = struct_section.group(1)

        if not tree_text:
            return paths

        # Extract lines that look like file paths (have an extension)
        file_line = re.compile(
            r"[│├└─\s]*"       # tree drawing characters
            r"([\w\-./]+\.\w+)"  # the actual filename/path part
        )
        # Track directory context from indentation
        dir_stack: list[str] = []
        for line in tree_text.splitlines():
            m = file_line.search(line)
            if not m:
                continue
            filename = m.group(1).strip()
            # Skip meta files we don't need to create
            if filename in ("MANIFEST.json",):
                continue
            # Compute indent depth by counting leading tree chars
            depth = len(re.match(r"^[\s│├└─]*", line).group(0)) // 4
            # Simple: if it looks like a path already (has /), use as-is
            if "/" in filename:
                paths.append(filename)
            else:
                paths.append(filename)

        return paths

    def _extract_all_code_blocks(self, text: str) -> list[tuple[str, str]]:
        """Extract all ```lang ... ``` blocks from text."""
        pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
        return [(m.group(1), m.group(2)) for m in pattern.finditer(text)]

    def _lang_to_ext(self, lang: str) -> str:
        mapping = {
            "python": "py", "py": "py",
            "typescript": "ts", "ts": "ts",
            "javascript": "js", "js": "js",
            "toml": "toml", "yaml": "yaml", "yml": "yaml",
            "json": "json", "sql": "sql", "sh": "sh",
            "bash": "sh", "dockerfile": "dockerfile",
            "markdown": "md", "md": "md",
        }
        return mapping.get(lang.lower(), lang.lower() or "txt")

    def _project_name_from_prompt(self, prompt: str) -> str:
        """Derive a snake_case project name from the prompt."""
        # Grab first 6 words, lowercase, strip punctuation
        words = re.sub(r"[^\w\s]", "", prompt.lower()).split()[:6]
        name = "_".join(w for w in words if len(w) > 2)
        return name[:40] or "generated_project"