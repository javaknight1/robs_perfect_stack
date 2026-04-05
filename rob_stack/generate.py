"""Project generation — `rob-stack new`"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

from .templates.shared import gitignore, readme, supabase_config, init_db_sql
from .templates.nextjs import generate_nextjs
from .templates.cloudflare import generate_go_cloudflare
from .templates.mobile import generate_mobile
from .templates.ci import (
    github_ci_nextjs, github_ci_go,
    github_deploy_nextjs, github_deploy_go,
    concurrent_dev_package_json,
)
from .templates.docs import claude_md, contributing_md, architecture_md, deployment_md
from .preflight import run_preflight
from .credentials import prompt_credentials


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


def run_generate(dry_run: bool = False) -> None:
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

    # ── Description (optional) ────────────────────────────────────
    description = ask("Description (optional, press Enter to skip): ")

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

    # ── GitHub username (Go only) ──────────────────────────────────
    github_user = ""
    if not is_nextjs:
        github_user = ask("GitHub username (for go.mod module path): ")
        if not github_user:
            github_user = "yourusername"

    # ── Pre-flight checks ─────────────────────────────────────────
    run_preflight(is_nextjs, has_mobile)

    # ── Credential prompts ────────────────────────────────────────
    schema = schema_name(name)
    creds = None  # type: Optional[dict]
    if not dry_run:
        creds = prompt_credentials(name, schema, is_nextjs)

    # ── Dry run writer ─────────────────────────────────────────────
    file_count = [0]
    if dry_run:
        def dry_write(base, rel, content):
            file_count[0] += 1
            print(f"  [dry-run] {rel}")
        writer = dry_write
    else:
        writer = write

    # ── Validate destination ───────────────────────────────────────
    root = Path.cwd() / name
    if not dry_run and root.exists():
        print(f"\n❌  Directory {name!r} already exists.")
        sys.exit(1)

    # ── Generate ───────────────────────────────────────────────────
    ctx = {
        "name": name,
        "title": title_case(name),
        "schema": schema,
        "description": description,
        "github_user": github_user,
    }

    if is_nextjs:
        generate_nextjs(root, ctx, writer, creds=creds)
    else:
        generate_go_cloudflare(root, ctx, writer, creds=creds)

    if has_mobile:
        generate_mobile(root, ctx, writer, is_nextjs=is_nextjs)

    # ── CI/CD ─────────────────────────────────────────────────────
    if is_nextjs:
        writer(root, ".github/workflows/ci.yml", github_ci_nextjs())
        writer(root, ".github/workflows/deploy.yml", github_deploy_nextjs())
    else:
        writer(root, ".github/workflows/ci.yml", github_ci_go())
        writer(root, ".github/workflows/deploy.yml", github_deploy_go())
        writer(root, "package.json", concurrent_dev_package_json(name))

    writer(root, ".gitignore", gitignore())
    writer(root, "supabase/config.toml", supabase_config(ctx))
    writer(root, "scripts/init-db.sql", init_db_sql(schema))
    writer(root, "supabase/migrations/001_init.sql", init_db_sql(schema))
    writer(root, "README.md", readme(ctx, is_nextjs, has_mobile))
    writer(root, "CLAUDE.md", claude_md(ctx, is_nextjs, has_mobile))
    writer(root, "CONTRIBUTING.md", contributing_md(ctx, is_nextjs, has_mobile))
    writer(root, "ARCHITECTURE.md", architecture_md(ctx, is_nextjs, has_mobile))
    writer(root, "DEPLOYMENT.md", deployment_md(ctx, is_nextjs, has_mobile))

    if dry_run:
        print(f"\n📋 Dry run complete. {file_count[0]} files would be created.")
        return

    # ── Git init ──────────────────────────────────────────────────
    print("\n🔧 Initializing git repository...")
    subprocess.run(["git", "init"], cwd=root, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=root, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial scaffold from rob-stack"],
        cwd=root, capture_output=True,
    )
    print("  ✓ git init + initial commit")

    # ── Next steps ─────────────────────────────────────────────────
    port = "3000" if is_nextjs else "5173"
    env_file = ".env.local" if is_nextjs else "api/.dev.vars"

    print(f"""
✅  Created {name}/ (git repo initialised)

─────────────────────────────────────────────
  Next steps:

  1.  cd {name}
  2.  make dev
      → Starts Supabase (Postgres + REST API) + dev server(s)
      → App running at http://localhost:{port}
      → Supabase Studio at http://localhost:54323
      → Inbucket (email) at http://localhost:54324

  Any empty API keys can be filled in later in {env_file}.
  See README.md for full setup guide & service checklist.
─────────────────────────────────────────────
""")
