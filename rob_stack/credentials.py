"""Interactive credential prompts for service API keys."""

import sys
from typing import Optional


# Well-known Supabase local dev defaults
SUPABASE_LOCAL_URL = "http://127.0.0.1:54321"
SUPABASE_LOCAL_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9."
    "CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)
SUPABASE_LOCAL_SERVICE_ROLE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0."
    "EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
)


def _ask_optional(prompt: str) -> str:
    """Like input() but returns '' on EOF instead of raising."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def _section(title: str) -> None:
    print(f"\n  {title}")
    print("  " + "-" * len(title))


def prompt_credentials(name: str, schema: str, is_nextjs: bool) -> dict:
    """Prompt for each service's API keys. Returns a dict of env key -> value.

    Auto-populates Supabase local defaults and derived values.
    Empty strings mean the user skipped that key.
    """
    creds = {}  # type: dict[str, str]

    print("\n  Configure services (press Enter to skip any key):\n")

    # ── Clerk ────────────────────────────────────────────────────
    _section("Clerk (auth)")
    creds["CLERK_PUBLISHABLE_KEY"] = _ask_optional("    Publishable key (pk_test_...): ")
    creds["CLERK_SECRET_KEY"] = _ask_optional("    Secret key (sk_test_...): ")
    if not is_nextjs:
        creds["CLERK_JWKS_URL"] = _ask_optional("    JWKS URL (https://...clerk.accounts.dev/.well-known/jwks.json): ")

    # ── Upstash Redis ────────────────────────────────────────────
    _section("Upstash Redis (local Redis is not compatible with Upstash REST protocol)")
    creds["UPSTASH_REDIS_REST_URL"] = _ask_optional("    REST URL (https://...upstash.io): ")
    creds["UPSTASH_REDIS_REST_TOKEN"] = _ask_optional("    REST token: ")

    # ── Resend ───────────────────────────────────────────────────
    _section("Resend (email)")
    creds["RESEND_API_KEY"] = _ask_optional("    API key (re_...): ")

    # ── Cloudflare R2 ────────────────────────────────────────────
    _section("Cloudflare R2 (storage)")
    creds["R2_ACCOUNT_ID"] = _ask_optional("    Account ID: ")
    creds["R2_ACCESS_KEY_ID"] = _ask_optional("    Access key ID: ")
    creds["R2_SECRET_ACCESS_KEY"] = _ask_optional("    Secret access key: ")

    # ── PostHog ──────────────────────────────────────────────────
    _section("PostHog (analytics)")
    creds["POSTHOG_KEY"] = _ask_optional("    Project API key (phc_...): ")

    # ── Sentry ───────────────────────────────────────────────────
    _section("Sentry (error tracking)")
    creds["SENTRY_DSN"] = _ask_optional("    DSN (https://...): ")

    # ── BetterStack ──────────────────────────────────────────────
    _section("BetterStack (logging)")
    creds["BETTERSTACK_SOURCE_TOKEN"] = _ask_optional("    Source token: ")

    # ── Auto-populated values ────────────────────────────────────
    db_url = (
        f"postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        f"?search_path={schema}"
    )
    creds["SUPABASE_URL"] = SUPABASE_LOCAL_URL
    creds["SUPABASE_ANON_KEY"] = SUPABASE_LOCAL_ANON_KEY
    creds["SUPABASE_SERVICE_ROLE_KEY"] = SUPABASE_LOCAL_SERVICE_ROLE_KEY
    creds["DATABASE_URL"] = db_url
    creds["R2_BUCKET_NAME"] = name
    creds["POSTHOG_HOST"] = "https://us.i.posthog.com"
    creds["RESEND_FROM_EMAIL"] = "noreply@yourdomain.com"

    # Next.js-specific auto values
    if is_nextjs:
        creds["CLERK_SIGN_IN_URL"] = "/sign-in"
        creds["CLERK_SIGN_UP_URL"] = "/sign-up"
        creds["CLERK_AFTER_SIGN_IN_URL"] = "/dashboard"
        creds["CLERK_AFTER_SIGN_UP_URL"] = "/dashboard"

    # Go+Cloudflare auto values
    if not is_nextjs:
        creds["ALLOWED_ORIGINS"] = "http://localhost:5173"
        creds["VITE_API_URL"] = "http://localhost:8787/api"

    return creds
