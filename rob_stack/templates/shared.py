"""Shared file templates (gitignore, supabase config, README)."""


def gitignore() -> str:
    return """\
# deps
node_modules/
vendor/

# builds
.next/
dist/
out/
bin/
build/
*.exe
*.wasm

# env
.env
.env.local
.env.*.local
.dev.vars

# misc
.DS_Store
*.log
*.tsbuildinfo
.sentryclirc
.wrangler/
"""


def supabase_config(ctx: dict) -> str:
    name = ctx["name"]
    schema = ctx["schema"]
    return f"""\
# Supabase local development configuration
# Docs: https://supabase.com/docs/guides/cli/config

[project]
id = "{name}"

[db]
port = 54322
major_version = 15

[db.pooler]
enabled = false

[api]
enabled = true
port = 54321
schemas = ["public", "{schema}"]
extra_search_path = ["public", "{schema}"]

[auth]
enabled = true
site_url = "http://127.0.0.1:3000"

[auth.email]
enable_signup = true
enable_confirmations = false

[studio]
enabled = true
port = 54323

[inbucket]
enabled = true
port = 54324
"""


def init_db_sql(schema: str) -> str:
    return f"""\
-- Initialise the app schema and a scoped role.
-- This runs as a Supabase migration on `supabase start` / `supabase db reset`.

CREATE SCHEMA IF NOT EXISTS {schema};

-- Create a role scoped to this schema (password: postgres for local dev)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{schema}_app') THEN
    CREATE ROLE {schema}_app LOGIN PASSWORD 'postgres';
  END IF;
END
$$;

GRANT USAGE  ON SCHEMA {schema} TO {schema}_app;
GRANT ALL    ON ALL TABLES IN SCHEMA {schema} TO {schema}_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA {schema}
  GRANT ALL ON TABLES TO {schema}_app;
"""


def readme(ctx: dict, is_nextjs: bool, has_mobile: bool) -> str:
    name = ctx["name"]
    title = ctx["title"]
    schema = ctx["schema"]
    description = ctx.get("description", "")
    arch = "Next.js -> Vercel" if is_nextjs else "Go + React -> Cloudflare Workers (API) + Cloudflare Pages (web)"
    env_file = ".env.local" if is_nextjs else "api/.dev.vars"

    desc_line = f"\n{description}\n" if description else ""

    # ── Repo structure ────────────────────────────────────────────
    mobile_tree = ""
    if has_mobile:
        mobile_tree = """\
├── mobile/                      # Expo (React Native) app
│   ├── app/
│   │   ├── _layout.tsx          # Root layout (Clerk provider)
│   │   ├── index.tsx            # Home screen
│   │   └── (auth)/sign-in.tsx   # Sign-in screen
│   ├── lib/api.ts               # Authenticated API client hook
│   ├── app.json
│   ├── .env.example
│   └── package.json
"""

    if is_nextjs:
        structure = f"""\
```
{name}/
├── src/
│   ├── app/                # Next.js App Router pages & layouts
│   │   ├── layout.tsx      # Root layout (Clerk + PostHog providers)
│   │   ├── page.tsx        # Home page
│   │   ├── globals.css     # Tailwind CSS entry
│   │   ├── dashboard/
│   │   │   └── page.tsx    # Protected dashboard page
│   │   ├── (auth)/
│   │   │   ├── layout.tsx  # Centered auth layout
│   │   │   ├── sign-in/[[...sign-in]]/page.tsx
│   │   │   └── sign-up/[[...sign-up]]/page.tsx
│   │   ├── api-docs/
│   │   │   └── page.tsx   # Swagger UI page
│   │   └── api/
│   │       ├── health/route.ts  # Health endpoint
│   │       └── docs/route.ts    # OpenAPI JSON spec endpoint
│   ├── components/
│   │   └── providers.tsx   # Client-side provider wrappers
│   ├── emails/
│   │   └── welcome.tsx     # React Email template
│   └── lib/
│       ├── supabase.ts     # Supabase client (admin + RLS)
│       ├── redis.ts        # Upstash Redis helpers
│       ├── resend.ts       # Email via Resend
│       ├── r2.ts           # Cloudflare R2 storage (S3 SDK)
│       ├── posthog.ts      # Server-side analytics
│       └── swagger.ts      # OpenAPI spec config
├── middleware.ts            # Clerk auth middleware
├── instrumentation.ts       # Sentry instrumentation hook
{mobile_tree}├── supabase/
│   ├── config.toml          # Supabase local dev config
│   └── migrations/
│       └── 001_init.sql     # Initial schema migration
├── scripts/
│   └── init-db.sql          # DB schema bootstrap (reference)
├── .env.example             # All required environment variables
├── Makefile                 # Dev/build/deploy targets
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── postcss.config.mjs
├── eslint.config.mjs
├── tsconfig.json
├── vercel.json
├── CLAUDE.md
├── CONTRIBUTING.md
├── ARCHITECTURE.md
├── DEPLOYMENT.md
└── README.md
```"""
    else:
        structure = f"""\
```
{name}/
├── api/                         # Go backend (Cloudflare Workers via TinyGo)
│   ├── cmd/worker/main.go       # Worker entry point + router
│   ├── internal/
│   │   ├── supabase/client.go   # Supabase REST client
│   │   ├── cache/redis.go       # Upstash Redis HTTP client
│   │   ├── middleware/clerk.go  # Clerk JWT verification
│   │   ├── email/resend.go      # Resend email client
│   │   ├── storage/r2.go        # Cloudflare R2 storage
│   │   ├── analytics/posthog.go # PostHog event capture
│   │   ├── logger/betterstack.go # BetterStack log shipping
│   │   └── openapi/spec.go     # OpenAPI 3.0 spec + Swagger UI
│   ├── .env.example
│   ├── .dev.vars.example        # Local secrets for wrangler dev
│   ├── go.mod
│   └── wrangler.toml
├── web/                         # React frontend (Cloudflare Pages)
│   ├── src/
│   │   ├── main.tsx             # App entry (Sentry + PostHog + Clerk)
│   │   ├── App.tsx              # Router with public/protected routes
│   │   ├── lib/api.ts           # Authenticated API client hook
│   │   └── index.css            # Tailwind CSS entry
│   ├── index.html
│   ├── vite.config.ts
│   ├── .env.example
│   └── wrangler.toml
{mobile_tree}├── supabase/
│   ├── config.toml              # Supabase local dev config
│   └── migrations/
│       └── 001_init.sql         # Initial schema migration
├── scripts/
│   └── init-db.sql              # DB schema bootstrap (reference)
├── Makefile                     # Dev/build/deploy targets
├── CLAUDE.md
├── CONTRIBUTING.md
├── ARCHITECTURE.md
├── DEPLOYMENT.md
└── README.md
```"""

    # ── Prerequisites ─────────────────────────────────────────────
    if is_nextjs:
        prereqs = """\
| Tool | Version | Install |
|------|---------|---------|
| **Node.js** | >= 18 | [nodejs.org](https://nodejs.org) or `brew install node` |
| **npm** | >= 9 | Comes with Node.js |
| **Docker** | >= 24 | [docker.com](https://www.docker.com/products/docker-desktop/) |
| **Supabase CLI** | latest | `brew install supabase/tap/supabase` or [docs](https://supabase.com/docs/guides/cli/getting-started) |
| **Git** | >= 2 | `brew install git` or [git-scm.com](https://git-scm.com) |"""
    else:
        prereqs = """\
| Tool | Version | Install |
|------|---------|---------|
| **Node.js** | >= 18 | [nodejs.org](https://nodejs.org) or `brew install node` |
| **Go** | >= 1.23 | [go.dev](https://go.dev/dl/) or `brew install go` |
| **TinyGo** | >= 0.32 | [tinygo.org](https://tinygo.org/getting-started/install/) or `brew install tinygo` |
| **Docker** | >= 24 | [docker.com](https://www.docker.com/products/docker-desktop/) |
| **Supabase CLI** | latest | `brew install supabase/tap/supabase` or [docs](https://supabase.com/docs/guides/cli/getting-started) |
| **Wrangler** | >= 3 | `npm install -g wrangler` |
| **Git** | >= 2 | `brew install git` or [git-scm.com](https://git-scm.com) |"""

    if has_mobile:
        prereqs += """
| **Expo CLI** | latest | `npm install -g expo-cli` |
| **Xcode** | >= 15 | Mac App Store (iOS development) |
| **Android Studio** | latest | [developer.android.com](https://developer.android.com/studio) (Android development) |"""

    # ── Run locally ───────────────────────────────────────────────
    port = "3000" if is_nextjs else "5173"
    if is_nextjs:
        run_locally = f"""\
### Quick start

```bash
make dev
```

This single command:
1. Installs npm dependencies (if needed)
2. Starts **Supabase** locally (Postgres, REST API, Studio, Inbucket)
3. Starts the Next.js dev server

Once running:
- **App** at [http://localhost:3000](http://localhost:3000)
- **Supabase Studio** at [http://localhost:54323](http://localhost:54323)
- **Inbucket** (email testing) at [http://localhost:54324](http://localhost:54324)

### Manual setup

```bash
make setup    # npm install + supabase start
npm run dev
```

Fill in any empty API keys in `.env.local` (see Service Checklist below)."""
    else:
        run_locally = f"""\
### Quick start

```bash
make dev
```

This single command:
1. Installs npm + Go dependencies (if needed)
2. Starts **Supabase** locally (Postgres, REST API, Studio, Inbucket)
3. Starts the Go API worker and React dev server concurrently

Once running:
- **Web app** at [http://localhost:5173](http://localhost:5173)
- **API** at [http://localhost:8787](http://localhost:8787)
- **Supabase Studio** at [http://localhost:54323](http://localhost:54323)
- **Inbucket** (email testing) at [http://localhost:54324](http://localhost:54324)

### Manual setup

```bash
make setup    # npm install + go mod tidy + supabase start
npm run dev
```

Fill in any empty API keys in `api/.dev.vars` and `web/.env` (see Service Checklist below)."""

    mobile_section = ""
    if has_mobile:
        mobile_section = f"""
### Start the mobile app (optional)

```bash
cd mobile
npm install
npx expo start
```

Press `i` for iOS simulator or `a` for Android emulator.
Set `EXPO_PUBLIC_API_URL` in `mobile/.env` to point at your local API
(`http://localhost:{port}/api`).
"""

    # ── Testing locally ───────────────────────────────────────────
    testing = """\
### Verify everything works

1. **Database** — open Supabase Studio at [http://localhost:54323](http://localhost:54323)
   and confirm the schema exists.

2. **Email** — send a test email via your app and check Inbucket:
   Open **http://localhost:54324** to see captured emails.

3. **API health** — hit the health endpoint:
   ```bash
   curl http://localhost:%s/health
   # → ok
   ```""" % ("3000" if is_nextjs else "8787")

    # ── Deploy ────────────────────────────────────────────────────
    if is_nextjs:
        deploy = """\
1. Push to GitHub.
2. Connect the repo to [Vercel](https://vercel.com).
3. Set all environment variables in the Vercel dashboard.
4. Vercel auto-deploys on every push to `main`."""
    else:
        deploy = """\
**API (Cloudflare Workers):**
```bash
cd api
wrangler deploy
```

**Web (Cloudflare Pages):**
```bash
cd web
npm run deploy
```

Set secrets via `wrangler secret put SECRET_NAME` for the API worker.
Configure environment variables in the Cloudflare Pages dashboard for the web app."""

    return f"""\
# {title}
{desc_line}
## Stack

| Layer | Technology |
|-------|-----------|
| **Architecture** | {arch} |
| **Database** | [Supabase](https://supabase.com) (schema: `{schema}`) |
| **Cache** | [Upstash Redis](https://upstash.com) |
| **Auth** | [Clerk](https://clerk.com) |
| **Email** | [Resend](https://resend.com) |
| **Storage** | [Cloudflare R2](https://www.cloudflare.com/developer-platform/r2/) |
| **Analytics** | [PostHog](https://posthog.com) |
| **Errors** | [Sentry](https://sentry.io) |
| **Uptime / Logs** | [BetterStack](https://betterstack.com) |
{"| **Mobile** | [Expo](https://expo.dev) (React Native) |" if has_mobile else ""}

## Repository Structure

{structure}

## Prerequisites

{prereqs}

## Getting Started

{run_locally}
{mobile_section}
## Testing Locally

{testing}

## Common Commands

This project includes a `Makefile` for frequently used operations:

| Command | Description |
|---------|-------------|
| `make dev` | {"Start Supabase + Next.js dev server" if is_nextjs else "Start Supabase + API + web dev servers"} |
| `make build` | {"Build for production" if is_nextjs else "Build the Worker WASM (requires TinyGo)"} |
| `make lint` | {"Run ESLint and TypeScript checks" if is_nextjs else "Run TypeScript and Go vet checks"} |
| `make test` | Run tests |
| `make supabase-start` | Start local Supabase (Postgres, REST API, Studio) |
| `make supabase-stop` | Stop local Supabase |
| `make deploy` | {"Deploy to Vercel" if is_nextjs else "Deploy API and web to Cloudflare"} |
| `make setup` | Install all dependencies + start Supabase |

## API Documentation

Interactive API docs are available at {"[/api-docs](http://localhost:3000/api-docs)" if is_nextjs else "[/api/docs](http://localhost:8787/api/docs)"} when the app is running.

The OpenAPI spec is served at {"`/api/docs`" if is_nextjs else "`/api/docs/openapi.json`"} as JSON. Add `@swagger` JSDoc
annotations to your {"API route handlers" if is_nextjs else "endpoint definitions"} to document new endpoints.

## Supabase Schema Setup (Production)

When you're ready for production, run this in the Supabase SQL editor:

```sql
CREATE SCHEMA {schema};
CREATE ROLE {schema}_app LOGIN PASSWORD 'YOUR_STRONG_PASSWORD';
GRANT USAGE ON SCHEMA {schema} TO {schema}_app;
GRANT ALL ON ALL TABLES IN SCHEMA {schema} TO {schema}_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA {schema}
  GRANT ALL ON TABLES TO {schema}_app;
```

## Service Checklist

Set up each service and copy the credentials into your `{env_file}`:

- [ ] **Clerk** — create application, copy publishable + secret keys
- [ ] **Upstash** — create Redis database, copy REST URL + token
- [ ] **Resend** — verify domain, copy API key
- [ ] **Cloudflare R2** — create bucket, generate API token, copy credentials
- [ ] **PostHog** — create project, copy project key
- [ ] **Sentry** — create project, copy DSN
- [ ] **BetterStack** — create source, copy ingestion token

> Supabase runs locally via the CLI — no cloud account needed for development.

## Deploy

{deploy}

## rob-stack CLI

This project was generated with [rob-stack](https://github.com/yourusername/rob-stack).

Useful commands:
- `rob-stack check .` — audit this repo for conformance to the canonical stack
- `rob-stack check . --service clerk` — check a single service
- `rob-stack new --dry-run` — preview files without writing
"""
