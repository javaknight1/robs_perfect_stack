"""Pre-flight checks — verify required CLI tools are installed."""

import re
import subprocess
import sys
from typing import Optional, Tuple


def _run(cmd: list) -> Optional[str]:
    """Run a command with a 10 s timeout. Return stdout or None on failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() or result.stderr.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def _parse_version(text: str) -> Optional[Tuple[int, ...]]:
    """Extract a version tuple from strings like 'v20.11.0', 'go1.23.2', '3.2.1'."""
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    if not m:
        return None
    major, minor = int(m.group(1)), int(m.group(2))
    patch = int(m.group(3)) if m.group(3) else 0
    return (major, minor, patch)


def check_tool(name: str, cmd: list, min_version: Optional[Tuple[int, ...]] = None) -> Optional[str]:
    """Return None on success, or an error message string."""
    output = _run(cmd)
    if output is None:
        return f"{name} — not found (run: {' '.join(cmd)})"
    if min_version is not None:
        ver = _parse_version(output)
        if ver is None:
            return f"{name} — could not parse version from: {output!r}"
        if ver < min_version:
            want = ".".join(str(v) for v in min_version)
            got = ".".join(str(v) for v in ver)
            return f"{name} — found {got}, need >= {want}"
    return None


def run_preflight(is_nextjs: bool, has_mobile: bool) -> None:
    """Check that all required CLI tools are installed. Exits on failure."""
    errors = []

    # Common tools
    checks = [
        ("Node.js", ["node", "--version"], (18, 0, 0)),
        ("npm", ["npm", "--version"], (9, 0, 0)),
        ("Docker", ["docker", "--version"], (24, 0, 0)),
        ("Git", ["git", "--version"], (2, 0, 0)),
        ("Supabase CLI", ["supabase", "--version"], None),
    ]

    # Go+Cloudflare extras
    if not is_nextjs:
        checks.extend([
            ("Go", ["go", "version"], (1, 23, 0)),
            ("TinyGo", ["tinygo", "version"], (0, 32, 0)),
            ("Wrangler", ["wrangler", "--version"], (3, 0, 0)),
        ])

    # Mobile
    if has_mobile:
        checks.append(("Expo CLI", ["npx", "expo", "--version"], None))

    for name, cmd, min_ver in checks:
        err = check_tool(name, cmd, min_ver)
        if err:
            errors.append(err)

    if errors:
        print("\n Pre-flight check failed:\n")
        for e in errors:
            print(f"  - {e}")
        print()
        sys.exit(1)
