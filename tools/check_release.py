"""Limited candidate-file scan and historical integrity check; no secret output."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {"app.py", "README.md", "LICENSE", "CHANGELOG.md", "requirements.in",
              "requirements.txt", "requirements-dev.txt", ".gitignore", ".env.example"}
FOLDERS = {"core", "tests", "docs", "examples", "evaluation", "samples", "tools", ".github", ".streamlit"}
SUFFIXES = {".py", ".md", ".txt", ".json", ".csv", ".yml", ".yaml", ".toml"}


def candidates():
    for name in sorted(ROOT_FILES):
        yield ROOT / name
    for folder in sorted(FOLDERS):
        for path in sorted((ROOT / folder).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix in SUFFIXES:
                yield path


def main():
    failures = []
    recorded = json.loads((ROOT / "docs/historical/sha256.json").read_text())
    for name, expected in recorded.items():
        path = ROOT / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(f"Historical integrity mismatch: {name}")
    patterns = [re.compile(r"\b(?:gsk_|sk-ant-|sk-proj-|AIza)[A-Za-z0-9_-]{20,}"),
                re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")]
    paths = list(candidates())
    for path in paths:
        name = path.relative_to(ROOT).as_posix()
        if path.name.startswith(("credentials", "secrets")):
            failures.append(f"Forbidden candidate: {name}")
            continue
        if not path.is_file():
            failures.append(f"Missing candidate: {name}")
            continue
        if any(pattern.search(path.read_text(encoding="utf-8", errors="replace")) for pattern in patterns):
            failures.append(f"Possible secret in candidate: {name}")
    if "--list" in sys.argv:
        print("\n".join(path.relative_to(ROOT).as_posix() for path in paths))
    print(f"Checked {len(recorded)} historical files and {len(paths)} candidate text files.")
    print("\n".join(failures) if failures else "Limited integrity/pattern checks passed. Ownership and full release review remain required.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
