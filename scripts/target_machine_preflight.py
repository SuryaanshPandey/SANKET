"""SANKET target-machine preflight checks.

The script does not modify the environment. It checks the local Python runtime,
required backend imports, frontend lockfile, environment-file hygiene, and the
local Ollama endpoint when one is configured.

A running local SQLite database is expected during development, so its presence
is reported as informational rather than treated as a failure.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_IMPORTS = [
    "fastapi",
    "pydantic",
    "sqlalchemy",
    "PIL",
    "cv2",
    "clarity",
]


def check_python() -> tuple[str, str]:
    version = sys.version_info
    ok = version >= (3, 11)
    return ("PASS" if ok else "FAIL", f"Python {version.major}.{version.minor}.{version.micro}")


def check_imports() -> tuple[str, str]:
    missing: list[str] = []
    for module in REQUIRED_IMPORTS:
        try:
            __import__(module)
        except Exception as exc:
            missing.append(f"{module} ({exc})")
    return ("PASS", "all core imports available") if not missing else ("FAIL", "missing: " + ", ".join(missing))


def check_frontend_lockfile() -> tuple[str, str]:
    path = ROOT / "frontend" / "package-lock.json"
    return ("PASS", str(path.relative_to(ROOT))) if path.is_file() else ("FAIL", "frontend/package-lock.json missing")


def check_environment_hygiene() -> tuple[str, str]:
    env_file = ROOT / ".env"
    db_files = list(ROOT.glob("*.db")) + list(ROOT.glob("*.db-wal")) + list(ROOT.glob("*.db-shm"))
    if env_file.exists():
        return "FAIL", ".env exists at repository root; use environment-specific secrets outside the submission tree"
    if db_files:
        return "WARN", "local SQLite runtime files are present (expected for local development; exclude from final submission)"
    return "PASS", "no root .env or local runtime DB files detected"


def check_ollama() -> tuple[str, str]:
    base = os.getenv("OPENAI_API_BASE", "http://127.0.0.1:11434/v1").rstrip("/")
    if not any(host in base for host in ("127.0.0.1:11434", "localhost:11434", "[::1]:11434")):
        return "PASS", f"non-local planner endpoint configured; Ollama probe skipped ({base})"
    root = base[:-3] if base.endswith("/v1") else base
    try:
        with urlopen(f"{root}/api/tags", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        names = [str(item.get("name")) for item in payload.get("models", []) if isinstance(item, dict)]
        model = os.getenv("VLM_DEFAULT_MODEL", "qwen2.5vl:3b")
        if model in names:
            return "PASS", f"Ollama reachable; configured model={model} is installed"
        return "WARN", f"Ollama reachable but configured model={model} was not listed; installed models={names[:8]}"
    except Exception as exc:
        return "WARN", f"Ollama not reachable from this process ({exc}); required only for live AI planner execution"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    checks = [
        ("python", *check_python()),
        ("backend imports", *check_imports()),
        ("frontend lockfile", *check_frontend_lockfile()),
        ("submission hygiene", *check_environment_hygiene()),
        ("local Ollama", *check_ollama()),
    ]
    failed = [name for name, status, _ in checks if status == "FAIL"]
    print("=" * 78)
    print("SANKET TARGET-MACHINE PREFLIGHT")
    print("=" * 78)
    for name, status, detail in checks:
        print(f"[{status}] {name}: {detail}")
    print("\nResult:", "FAIL" if failed else "PASS (warnings may require attention)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
