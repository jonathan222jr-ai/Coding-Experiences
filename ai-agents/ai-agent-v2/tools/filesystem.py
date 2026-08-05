from pathlib import Path

def read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"Error: {path} does not exist"
    if p.stat().st_size > 500_000:
        return f"Error: file too large (>{500}KB)"
    return p.read_text(errors="replace")

def write_file(path: str, content: str) -> bool:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return True

def list_files(directory: str = ".", pattern: str = "*") -> list:
    return [str(p) for p in Path(directory).rglob(pattern) if p.is_file()]