"""Stack conformance checker — `rob-stack check [path]`"""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ──────────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────────

@dataclass
class ServiceResult:
    name: str
    status: str          # "pass" | "fail" | "warn" | "na"
    message: str
    alternative: Optional[str] = None   # what was found instead


@dataclass
class CheckReport:
    path: str
    arch: str                            # "nextjs" | "go_react" | "unknown"
    services: list[ServiceResult] = field(default_factory=list)
    hosting: list[ServiceResult] = field(default_factory=list)
    mobile: Optional[ServiceResult] = None

    @property
    def score(self) -> tuple[int, int]:
        checks = self.services + self.hosting
        if self.mobile:
            checks.append(self.mobile)
        passed = sum(1 for r in checks if r.status == "pass")
        return passed, len(checks)


# ──────────────────────────────────────────────────────────────────
# File loaders
# ──────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}


def _find_package_jsons(root: Path) -> list[dict]:
    """Collect all package.json files, excluding node_modules."""
    pkgs = []
    for p in root.rglob("package.json"):
        if "node_modules" in p.parts:
            continue
        pkgs.append(_load_json(p))
    return pkgs


def _all_js_deps(pkgs: list[dict]) -> set[str]:
    """Flatten all JS dependencies across found package.json files."""
    deps: set[str] = set()
    for pkg in pkgs:
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            deps.update(pkg.get(section, {}).keys())
    return deps


def _load_go_mod(root: Path) -> str:
    """Return concatenated content of any go.mod files in the repo."""
    parts = []
    for p in root.rglob("go.mod"):
        if "vendor" in p.parts:
            continue
        parts.append(p.read_text())
    return "\n".join(parts)


def _load_env_examples(root: Path) -> str:
    """Return concatenated content of any .env.example files."""
    parts = []
    for name in (".env.example", ".env.sample", ".env.template"):
        for p in root.rglob(name):
            parts.append(p.read_text())
    return "\n".join(parts)


def _load_source_files(root: Path, extensions: tuple[str, ...]) -> str:
    """Return concatenated source code for a quick grep."""
    parts = []
    skip = {"node_modules", "vendor", ".next", "dist", "build", ".git"}
    for p in root.rglob("*"):
        if any(s in p.parts for s in skip):
            continue
        if p.suffix.lstrip(".") in extensions:
            try:
                parts.append(p.read_text(errors="ignore"))
            except Exception:
                pass
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────
# Architecture detection
# ──────────────────────────────────────────────────────────────────

def detect_arch(root: Path, js_deps: set[str], go_mod: str) -> str:
    if "next" in js_deps:
        return "nextjs"
    has_go = bool(go_mod.strip())
    has_web = (root / "web").is_dir() or (root / "frontend").is_dir()
    if has_go and has_web:
        return "go_react"
    if has_go:
        return "go_react"
    # Vite + React without Go could still be a standalone React app
    if "vite" in js_deps and "react" in js_deps:
        return "go_react"   # treat as frontend portion of go_react
    return "unknown"


# ──────────────────────────────────────────────────────────────────
# Individual service checks
# ──────────────────────────────────────────────────────────────────

_SUPABASE_JS = {"@supabase/supabase-js"}
_SUPABASE_GO = {"pgx", "jackc/pgx"}
_SUPABASE_ENV = {"DATABASE_URL", "SUPABASE_URL"}

_REDIS_CORRECT = {"@upstash/redis"}
_REDIS_ALT = {"ioredis", "redis", "bullmq", "keyv"}
_REDIS_ENV = {"UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_URL"}

_CLERK_JS = {"@clerk/nextjs", "@clerk/clerk-react", "@clerk/clerk-expo"}
_CLERK_GO = {"clerk-sdk-go"}
_CLERK_ENV = {"CLERK_SECRET_KEY", "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"}
_AUTH_ALT = {"next-auth", "auth0", "@auth0/nextjs-auth0", "lucia", "better-auth",
             "firebase-admin", "supabase/auth-helpers"}

_RESEND_JS = {"resend"}
_RESEND_ENV = {"RESEND_API_KEY"}
_EMAIL_ALT = {"nodemailer", "@sendgrid/mail", "@aws-sdk/client-ses",
              "postmark", "@mailchimp/mailchimp_transactional"}

_R2_JS = {"@aws-sdk/client-s3"}
_R2_ENV = {"R2_ACCOUNT_ID", "R2_BUCKET_NAME"}
_STORAGE_ALT = {"@google-cloud/storage", "aws-sdk", "multer", "@vercel/blob"}

_POSTHOG_JS = {"posthog-js", "posthog-node"}
_POSTHOG_ENV = {"POSTHOG_KEY", "NEXT_PUBLIC_POSTHOG_KEY", "VITE_POSTHOG_KEY"}
_ANALYTICS_ALT = {"mixpanel", "@amplitude/analytics-browser", "ga-4", "gtag"}

_SENTRY_JS = {"@sentry/nextjs", "@sentry/react", "@sentry/react-native",
              "@sentry/node", "@sentry/browser"}
_SENTRY_ENV = {"SENTRY_DSN", "NEXT_PUBLIC_SENTRY_DSN", "VITE_SENTRY_DSN"}
_ERROR_ALT = {"@bugsnag/js", "rollbar", "honeybadger-js", "@honeybadger-io/core"}

_BETTERSTACK_ENV = {"BETTERSTACK_SOURCE_TOKEN", "LOGTAIL_SOURCE_TOKEN"}
_LOG_ALT = {"DATADOG_API_KEY", "DD_API_KEY", "PAPERTRAIL", "LOGDNA", "LOGROCKET"}


def _has_any(haystack: set[str], needles: set[str]) -> Optional[str]:
    found = haystack & needles
    return next(iter(found)) if found else None


def _env_has_any(env_text: str, keys: set[str]) -> Optional[str]:
    for key in keys:
        if key in env_text:
            return key
    return None


def check_supabase(js_deps: set[str], go_mod: str, env: str, source: str = "") -> ServiceResult:
    if _has_any(js_deps, _SUPABASE_JS) or any(g in go_mod for g in _SUPABASE_GO):
        return ServiceResult("Supabase", "pass", "@supabase/supabase-js or pgx detected")
    # Go REST API pattern — generated project uses HTTP client against PostgREST
    if go_mod and _env_has_any(env, _SUPABASE_ENV) and "supabase" in source.lower():
        return ServiceResult("Supabase", "pass", "Supabase REST API client detected in Go source")
    if _env_has_any(env, _SUPABASE_ENV):
        return ServiceResult("Supabase", "warn", "SUPABASE_URL/DATABASE_URL in env but client lib not found")
    return ServiceResult("Supabase", "fail", "Not detected — add @supabase/supabase-js")


def check_redis(js_deps: set[str], go_mod: str, env: str, source: str = "") -> ServiceResult:
    if _has_any(js_deps, _REDIS_CORRECT):
        return ServiceResult("Upstash Redis", "pass", "@upstash/redis detected")
    # Go REST pattern — Upstash HTTP API used directly (no SDK needed)
    if go_mod and _env_has_any(env, _REDIS_ENV) and "upstash" in source.lower():
        return ServiceResult("Upstash Redis", "pass", "Upstash Redis HTTP client detected in Go source")
    if "go-redis" in go_mod and _env_has_any(env, {"UPSTASH"}):
        return ServiceResult("Upstash Redis", "pass", "go-redis + Upstash env detected")
    alt = _has_any(js_deps, _REDIS_ALT)
    if alt:
        return ServiceResult("Upstash Redis", "fail", "Wrong Redis client detected",
                             alternative=f"Replace {alt!r} with @upstash/redis")
    if _env_has_any(env, _REDIS_ENV):
        return ServiceResult("Upstash Redis", "warn", "UPSTASH env var found but client not detected")
    return ServiceResult("Upstash Redis", "fail", "Not detected — add @upstash/redis")


def check_clerk(js_deps: set[str], go_mod: str, env: str) -> ServiceResult:
    if _has_any(js_deps, _CLERK_JS) or any(g in go_mod for g in _CLERK_GO):
        pkg = _has_any(js_deps, _CLERK_JS) or "clerk-sdk-go"
        return ServiceResult("Clerk", "pass", f"{pkg!r} detected")
    alt = _has_any(js_deps, _AUTH_ALT)
    if alt:
        return ServiceResult("Clerk", "fail", "Wrong auth provider detected",
                             alternative=f"Replace {alt!r} with @clerk/nextjs or @clerk/clerk-react")
    if _env_has_any(env, _CLERK_ENV):
        return ServiceResult("Clerk", "warn", "CLERK env vars found but Clerk SDK not in deps")
    return ServiceResult("Clerk", "fail", "Not detected — add @clerk/nextjs (Next.js) or @clerk/clerk-react")


def check_resend(js_deps: set[str], go_mod: str, env: str, source: str) -> ServiceResult:
    if "resend" in js_deps or "resend.com" in source:
        return ServiceResult("Resend", "pass", "'resend' package or Resend API detected")
    if _env_has_any(env, _RESEND_ENV):
        return ServiceResult("Resend", "warn", "RESEND_API_KEY in env but 'resend' not in deps")
    alt = _has_any(js_deps, _EMAIL_ALT)
    if alt:
        return ServiceResult("Resend", "fail", "Wrong email provider detected",
                             alternative=f"Replace {alt!r} with 'resend'")
    return ServiceResult("Resend", "fail", "Not detected — add 'resend'")


def check_r2(js_deps: set[str], go_mod: str, env: str, source: str = "") -> ServiceResult:
    has_sdk = "@aws-sdk/client-s3" in js_deps or "aws-sdk-go-v2/service/s3" in go_mod
    has_r2_env = _env_has_any(env, _R2_ENV)
    # Go REST pattern — direct R2 HTTP calls without SDK
    go_r2 = go_mod and ("r2.cloudflarestorage.com" in source or "R2_ACCOUNT_ID" in source)
    if (has_sdk or go_r2) and has_r2_env:
        return ServiceResult("Cloudflare R2", "pass",
                             "@aws-sdk/client-s3 or R2 HTTP client + env vars detected")
    if has_sdk and not has_r2_env:
        return ServiceResult("Cloudflare R2", "warn",
                             "@aws-sdk/client-s3 found but R2_ACCOUNT_ID missing — may be pointing to AWS S3")
    alt = _has_any(js_deps, _STORAGE_ALT)
    if alt:
        return ServiceResult("Cloudflare R2", "fail", "Wrong storage provider detected",
                             alternative=f"Replace {alt!r} with @aws-sdk/client-s3 + R2 credentials")
    return ServiceResult("Cloudflare R2", "fail", "Not detected — add @aws-sdk/client-s3 with R2 env vars")


def check_posthog(js_deps: set[str], env: str) -> ServiceResult:
    if _has_any(js_deps, _POSTHOG_JS):
        return ServiceResult("PostHog", "pass", "posthog-js or posthog-node detected")
    if _env_has_any(env, _POSTHOG_ENV):
        return ServiceResult("PostHog", "warn", "POSTHOG_KEY in env but posthog-js not in deps")
    alt = _has_any(js_deps, _ANALYTICS_ALT)
    if alt:
        return ServiceResult("PostHog", "fail", "Different analytics provider detected",
                             alternative=f"Consider adding posthog-js alongside {alt!r}")
    return ServiceResult("PostHog", "fail", "Not detected — add posthog-js")


def check_sentry(js_deps: set[str], env: str) -> ServiceResult:
    if _has_any(js_deps, _SENTRY_JS):
        pkg = _has_any(js_deps, _SENTRY_JS)
        return ServiceResult("Sentry", "pass", f"{pkg!r} detected")
    if _env_has_any(env, _SENTRY_ENV):
        return ServiceResult("Sentry", "warn", "SENTRY_DSN in env but Sentry SDK not in deps")
    alt = _has_any(js_deps, _ERROR_ALT)
    if alt:
        return ServiceResult("Sentry", "fail", "Different error tracking provider detected",
                             alternative=f"Consider replacing {alt!r} with @sentry/nextjs or @sentry/react")
    return ServiceResult("Sentry", "fail", "Not detected — add @sentry/nextjs or @sentry/react")


def check_betterstack(env: str) -> ServiceResult:
    if _env_has_any(env, _BETTERSTACK_ENV):
        return ServiceResult("BetterStack", "pass", "BETTERSTACK_SOURCE_TOKEN found in env")
    alt = _env_has_any(env, _LOG_ALT)
    if alt:
        return ServiceResult("BetterStack", "warn",
                             f"Different logging provider detected ({alt})",
                             alternative="Add BETTERSTACK_SOURCE_TOKEN to .env.example")
    return ServiceResult("BetterStack", "fail", "Not detected — add BETTERSTACK_SOURCE_TOKEN to .env.example")


def check_hosting(root: Path, arch: str) -> list[ServiceResult]:
    results = []
    has_vercel = (root / "vercel.json").exists()
    has_wrangler = any(root.rglob("wrangler.toml"))
    has_railway = (root / "railway.toml").exists()

    if arch == "nextjs":
        if has_vercel:
            results.append(ServiceResult("Hosting (Vercel)", "pass", "vercel.json detected"))
        else:
            results.append(ServiceResult("Hosting (Vercel)", "fail",
                                         "vercel.json not found — add it for Next.js deploys"))
        if has_railway:
            results.append(ServiceResult("Hosting", "warn",
                                         "railway.toml found — Next.js apps should deploy to Vercel"))

    elif arch == "go_react":
        if has_wrangler:
            results.append(ServiceResult("Hosting (Cloudflare)", "pass",
                                         "wrangler.toml detected (Pages + Workers)"))
        else:
            results.append(ServiceResult("Hosting (Cloudflare)", "fail",
                                         "wrangler.toml not found — add for Cloudflare Pages + Workers deploy"))
        if has_railway:
            results.append(ServiceResult("Hosting", "warn",
                                         "railway.toml found — migrate to Cloudflare Workers"))
        if has_vercel:
            results.append(ServiceResult("Hosting", "warn",
                                         "vercel.json found — Go+React apps use Cloudflare, not Vercel"))
    else:
        for name, flag in [("Vercel", has_vercel), ("Cloudflare", has_wrangler), ("Railway", has_railway)]:
            if flag:
                results.append(ServiceResult(f"Hosting ({name})", "warn",
                                             f"{name} config detected but architecture is unknown"))

    return results


def check_mobile(root: Path, js_deps: set[str]) -> ServiceResult:
    mobile_dir = root / "mobile"
    if mobile_dir.is_dir():
        if "@clerk/clerk-expo" in js_deps:
            return ServiceResult("Mobile (Expo)", "pass", "mobile/ directory + @clerk/clerk-expo detected")
        return ServiceResult("Mobile (Expo)", "warn",
                             "mobile/ directory found but @clerk/clerk-expo not detected")
    return ServiceResult("Mobile (Expo)", "na", "No mobile/ directory (optional)")


# ──────────────────────────────────────────────────────────────────
# Schema-per-app check
# ──────────────────────────────────────────────────────────────────

def check_schema_isolation(env: str, source: str) -> ServiceResult:
    """Check if Supabase is using schema-per-app isolation."""
    if "search_path" in env or "search_path" in source:
        return ServiceResult("Supabase schema isolation", "pass",
                             "search_path param detected in connection string")
    if "SUPABASE_SCHEMA" in env or "SUPABASE_SCHEMA" in source:
        return ServiceResult("Supabase schema isolation", "pass",
                             "SUPABASE_SCHEMA env var detected")
    # Go REST pattern — schema set via PostgREST Accept-Profile / Content-Profile headers
    if "Accept-Profile" in source or "Content-Profile" in source:
        return ServiceResult("Supabase schema isolation", "pass",
                             "PostgREST Accept-Profile / Content-Profile header isolation detected")
    return ServiceResult("Supabase schema isolation", "warn",
                         "No schema isolation detected — ensure connection string includes "
                         "?search_path=<app_name> (JS) or Accept-Profile header (Go REST) "
                         "so this app is isolated from others in the shared DB")


# ──────────────────────────────────────────────────────────────────
# Report rendering
# ──────────────────────────────────────────────────────────────────

STATUS_ICON = {"pass": "✅", "fail": "❌", "warn": "⚠️ ", "na": "➖"}
ARCH_LABEL = {
    "nextjs": "Next.js → Vercel",
    "go_react": "Go + React → Cloudflare Workers + Pages",
    "unknown": "Unknown (could not determine)",
}


def render_report(report: CheckReport) -> str:
    lines = []
    lines.append(f"\n🔍  Checking: {report.path}")
    lines.append(f"    Architecture: {ARCH_LABEL.get(report.arch, report.arch)}\n")

    # Services table
    col_w = 28
    lines.append(f"  {'Service':<{col_w}} {'Status':<8} Notes")
    lines.append("  " + "─" * 72)

    all_results = report.services + report.hosting
    if report.mobile:
        all_results.append(report.mobile)

    for r in all_results:
        icon = STATUS_ICON.get(r.status, "?")
        lines.append(f"  {r.name:<{col_w}} {icon:<8} {r.message}")
        if r.alternative:
            lines.append(f"  {'':<{col_w}} {'':8} 💡 {r.alternative}")

    lines.append("")

    passed, total = report.score
    pct = int(passed / total * 100) if total else 0
    lines.append(f"  Conformance score: {passed}/{total} ({pct}%)")

    return "\n".join(lines)


def render_migration_prompt(report: CheckReport) -> str:
    failing = [r for r in report.services + report.hosting if r.status == "fail"]
    warning = [r for r in report.services + report.hosting if r.status == "warn"]

    if not failing and not warning:
        return ""

    issues = []
    for r in failing:
        msg = r.name
        if r.alternative:
            msg += f" ({r.alternative})"
        issues.append(f"- {msg}")
    for r in warning:
        issues.append(f"- {r.name}: {r.message}")

    issue_text = "\n".join(issues)

    prompt = f"""
─── 📋 Claude Code Migration Prompt ─────────────────────────────────────────────
Copy and paste the following into Claude Code inside this repo:

\"\"\"
Refactor this project to conform to Rob's canonical tech stack.

Architecture: {ARCH_LABEL.get(report.arch, "unknown")}

The following components need to be added or replaced:
{issue_text}

Target stack:
- Database:   Supabase (@supabase/supabase-js) with schema-per-app isolation
              (connection string must include ?search_path=<schema>)
- Cache:      Upstash Redis (@upstash/redis) — never ioredis or plain redis
- Auth:       Clerk (@clerk/nextjs for Next.js, @clerk/clerk-react for React)
- Email:      Resend (resend package)
- Storage:    Cloudflare R2 via @aws-sdk/client-s3 with R2_ACCOUNT_ID env var
- Analytics:  PostHog (posthog-js client-side, posthog-node server-side)
- Errors:     Sentry (@sentry/nextjs or @sentry/react)
- Logs:       BetterStack (BETTERSTACK_SOURCE_TOKEN env var)
- Hosting:    {"Vercel (vercel.json)" if report.arch == "nextjs" else "Cloudflare Pages + Workers (wrangler.toml)"}

For each missing service:
1. Install the correct package
2. Create src/lib/<service>.ts with a typed, reusable client
3. Add all required env vars to .env.example
4. Wire the client into the app (layout providers, middleware, etc.)

Do not change any business logic — only swap infrastructure clients.
\"\"\"
──────────────────────────────────────────────────────────────────────────────────"""

    return prompt


# ──────────────────────────────────────────────────────────────────
# Main entry
# ──────────────────────────────────────────────────────────────────

def run_check(path: str) -> None:
    root = Path(path).resolve()
    if not root.exists():
        print(f"❌  Path not found: {path}")
        sys.exit(1)

    # ── Load data ────────────────────────────────────────────────
    pkgs = _find_package_jsons(root)
    js_deps = _all_js_deps(pkgs)
    go_mod = _load_go_mod(root)
    env_text = _load_env_examples(root)
    source_text = _load_source_files(root, ("ts", "tsx", "js", "go", "py"))

    # ── Detect architecture ──────────────────────────────────────
    arch = detect_arch(root, js_deps, go_mod)

    report = CheckReport(path=str(root), arch=arch)

    # ── Run checks ───────────────────────────────────────────────
    report.services = [
        check_supabase(js_deps, go_mod, env_text, source_text),
        check_schema_isolation(env_text, source_text),
        check_redis(js_deps, go_mod, env_text, source_text),
        check_clerk(js_deps, go_mod, env_text),
        check_resend(js_deps, go_mod, env_text, source_text),
        check_r2(js_deps, go_mod, env_text, source_text),
        check_posthog(js_deps, env_text),
        check_sentry(js_deps, env_text),
        check_betterstack(env_text),
    ]
    report.hosting = check_hosting(root, arch)
    report.mobile = check_mobile(root, js_deps)

    # ── Render ───────────────────────────────────────────────────
    print(render_report(report))
    migration = render_migration_prompt(report)
    if migration:
        print(migration)


