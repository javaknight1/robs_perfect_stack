"""Project generation — `rob-stack new`"""

import os
import sys
from pathlib import Path

from .templates.shared import gitignore, readme
from .templates.nextjs import generate_nextjs
from .templates.go_cloudflare import generate_go_cloudflare
from .templates.mobile import generate_mobile


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


def write(base: Path, rel: str, content: str) -> None:
    full = base / rel
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    print(f"  ✓ {rel}")


def title_case(name: str) -> str:
    return " ".join(w.capitalize() for w in name.split("-"))


def schema_name(name: str) -> str:
    return name.replace("-", "_")


def run_generate() -> None:
    print()
    print("╔══════════════════════════════════════╗")
    print("║      🚀  Rob's Stack Generator       ║")
    print("╚══════════════════════════════════════╝")
    print()

    # ── Project name ──────────────────────────────────────────────
    raw = ask("Project name (kebab-case): ")
    name = raw.lower().replace(" ", "-")
    name = "".join(c for c in name if c.isalnum() or c == "-")
    if not name:
        print("❌  Name is required.")
        sys.exit(1)

    # ── Architecture ───────────────────────────────────────────────
    print()
    print("Architecture:")
    print("  1. Next.js  ──▶  Vercel")
    print("  2. Go + React ──▶  Cloudflare Workers (API) + Cloudflare Pages (web)")
    arch_raw = ask("Choose [1/2]: ")
    is_nextjs = arch_raw.strip() != "2"

    # ── Mobile ─────────────────────────────────────────────────────
    mob_raw = ask("Include Expo mobile app? [y/n]: ").lower()
    has_mobile = mob_raw.startswith("y")

    # ── Validate destination ───────────────────────────────────────
    root = Path.cwd() / name
    if root.exists():
        print(f"\n❌  Directory {name!r} already exists.")
        sys.exit(1)

    # ── Generate ───────────────────────────────────────────────────
    ctx = {"name": name, "title": title_case(name), "schema": schema_name(name)}

    if is_nextjs:
        generate_nextjs(root, ctx, write)
    else:
        generate_go_cloudflare(root, ctx, write)

    if has_mobile:
        generate_mobile(root, ctx, write)

    write(root, ".gitignore", gitignore())
    write(root, "README.md", readme(ctx, is_nextjs, has_mobile))

    # ── Next steps ─────────────────────────────────────────────────
    schema = ctx["schema"]
    env_file = ".env.local" if is_nextjs else ".env"

    print(f"""
✅  Created {name}/

─────────────────────────────────────────────
  Next steps:

  1.  cd {name}

  2.  Supabase — run in SQL editor:
        CREATE SCHEMA {schema};
        CREATE ROLE {schema}_app LOGIN PASSWORD '...';
        GRANT USAGE ON SCHEMA {schema} TO {schema}_app;
        GRANT ALL ON ALL TABLES IN SCHEMA {schema} TO {schema}_app;
        ALTER DEFAULT PRIVILEGES IN SCHEMA {schema}
          GRANT ALL ON TABLES TO {schema}_app;

  3.  cp .env.example {env_file}  # fill in all values

  4.  Provision services (see README.md checklist)

  5.  {"npm install && npm run dev" if is_nextjs else "cd api && go mod tidy && npm run dev (from web/)"}
{"" if not has_mobile else f"  6.  cd mobile && npm install && npx expo start"}
─────────────────────────────────────────────
""")
