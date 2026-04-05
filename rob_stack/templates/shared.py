"""Shared file templates (gitignore, docker-compose, README)."""


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


def docker_compose(ctx: dict, is_nextjs: bool) -> str:
    return f"""\
# docker-compose.yml — local development infrastructure
#
# Start:   docker compose up -d
# Stop:    docker compose down
# Reset:   docker compose down -v  (deletes volumes)

services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  mailpit:
    image: axllent/mailpit:latest
    restart: unless-stopped
    ports:
      - "1025:1025"   # SMTP
      - "8025:8025"   # Web UI — http://localhost:8025
    environment:
      MP_SMTP_AUTH_ACCEPT_ANY: 1
      MP_SMTP_AUTH_ALLOW_INSECURE: 1

volumes:
  postgres_data:
"""


def init_db_sql(schema: str) -> str:
    return f"""\
-- Initialise the app schema and a scoped role.
-- This runs automatically when the postgres container starts for the first time.

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
    env_file = ".env.local" if is_nextjs else ".env"

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
{mobile_tree}├── docker-compose.yml       # Local Postgres, Redis, Mailpit
├── scripts/
│   └── init-db.sql          # DB schema bootstrap (runs on first docker compose up)
├── supabase/
│   └── migrations/
│       └── 001_init.sql     # Initial schema migration
├── .env.example             # All required environment variables
├── Makefile                 # Dev/build/deploy targets
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── postcss.config.mjs
├── eslint.config.mjs
├── tsconfig.json
├── vercel.json
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
{mobile_tree}├── docker-compose.yml           # Local Postgres, Redis, Mailpit
├── scripts/
│   └── init-db.sql              # DB schema bootstrap
├── supabase/
│   └── migrations/
│       └── 001_init.sql         # Initial schema migration
├── Makefile                     # Dev/build/deploy targets
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
| **Docker Compose** | >= 2 | Included with Docker Desktop |
| **Git** | >= 2 | `brew install git` or [git-scm.com](https://git-scm.com) |"""
    else:
        prereqs = """\
| Tool | Version | Install |
|------|---------|---------|
| **Node.js** | >= 18 | [nodejs.org](https://nodejs.org) or `brew install node` |
| **Go** | >= 1.23 | [go.dev](https://go.dev/dl/) or `brew install go` |
| **TinyGo** | >= 0.32 | [tinygo.org](https://tinygo.org/getting-started/install/) or `brew install tinygo` |
| **Docker** | >= 24 | [docker.com](https://www.docker.com/products/docker-desktop/) |
| **Docker Compose** | >= 2 | Included with Docker Desktop |
| **Wrangler** | >= 3 | `npm install -g wrangler` |
| **Git** | >= 2 | `brew install git` or [git-scm.com](https://git-scm.com) |"""

    if has_mobile:
        prereqs += """
| **Expo CLI** | latest | `npm install -g expo-cli` |
| **Xcode** | >= 15 | Mac App Store (iOS development) |
| **Android Studio** | latest | [developer.android.com](https://developer.android.com/studio) (Android development) |"""

    # ── Run locally ───────────────────────────────────────────────
    if is_nextjs:
        run_locally = f"""\
### 1. Start infrastructure

```bash
docker compose up -d
```

This starts:
- **PostgreSQL** on `localhost:5432` (user: `postgres`, password: `postgres`)
- **Redis** on `localhost:6379`
- **Mailpit** on `localhost:8025` (web UI) / `localhost:1025` (SMTP)

The `scripts/init-db.sql` file automatically creates the `{schema}` schema and
a scoped database role on first startup.

### 2. Configure environment

```bash
cp .env.example {env_file}
```

For local development with docker-compose, use these values:

| Variable | Local value |
|----------|-------------|
| `DATABASE_URL` | `postgresql://{schema}_app:postgres@localhost:5432/postgres?search_path={schema}` |
| `SUPABASE_URL` | Your Supabase project URL (or skip for DB-only local dev) |

Fill in the remaining service keys from each provider's dashboard (see Service
Checklist below).

### 3. Install dependencies and start

```bash
npm install
npm run dev
```

The app is now running at **http://localhost:3000**."""
    else:
        run_locally = f"""\
### 1. Start infrastructure

```bash
docker compose up -d
```

This starts:
- **PostgreSQL** on `localhost:5432` (user: `postgres`, password: `postgres`)
- **Redis** on `localhost:6379`
- **Mailpit** on `localhost:8025` (web UI) / `localhost:1025` (SMTP)

The `scripts/init-db.sql` file automatically creates the `{schema}` schema and
a scoped database role on first startup.

### 2. Configure environment

```bash
cp api/.env.example api/.env
cp web/.env.example web/.env
```

For local development with docker-compose, point the API at the local Postgres
and Redis instances (see the `.env.example` files for guidance).

### 3. Start the API (terminal 1)

```bash
cd api
go mod tidy
wrangler dev
```

The API worker is now running at **http://localhost:8787**.

### 4. Start the web frontend (terminal 2)

```bash
cd web
npm install
npm run dev
```

The web app is now running at **http://localhost:5173**.
Vite automatically proxies `/api` requests to the Worker at `localhost:8787`."""

    mobile_section = ""
    if has_mobile:
        mobile_section = f"""
### {"5" if not is_nextjs else "4"}. Start the mobile app (optional)

```bash
cd mobile
npm install
npx expo start
```

Press `i` for iOS simulator or `a` for Android emulator.
Set `EXPO_PUBLIC_API_URL` in `mobile/.env` to point at your local API
(`http://localhost:{"3000" if is_nextjs else "8787"}/api`).
"""

    # ── Testing locally ───────────────────────────────────────────
    testing = """\
### Verify everything works

1. **Database** — connect to Postgres and confirm the schema exists:
   ```bash
   docker compose exec postgres psql -U postgres -c '\\dn'
   ```

2. **Redis** — check the Redis connection:
   ```bash
   docker compose exec redis redis-cli ping
   # → PONG
   ```

3. **Email** — send a test email via your app and check Mailpit:
   Open **http://localhost:8025** to see captured emails.

4. **API health** — hit the health endpoint:
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

### Clone and enter the project

```bash
cd {name}
```

{run_locally}
{mobile_section}
## Testing Locally

{testing}

## Common Commands

This project includes a `Makefile` for frequently used operations:

| Command | Description |
|---------|-------------|
| `make dev` | {"Start the Next.js dev server" if is_nextjs else "Run API and web in separate terminals (`make dev-api` / `make dev-web`)"} |
| `make build` | {"Build for production" if is_nextjs else "Build the Worker WASM (requires TinyGo)"} |
| `make lint` | {"Run ESLint and TypeScript checks" if is_nextjs else "Run TypeScript and Go vet checks"} |
| `make test` | Run tests |
| `make db` | Start local Postgres, Redis, and Mailpit |
| `make db-stop` | Stop local infrastructure |
| `make deploy` | {"Deploy to Vercel" if is_nextjs else "Deploy API and web to Cloudflare"} |
| `make setup` | Install all dependencies |

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

- [ ] **Supabase** — create project, run schema SQL above, copy URL + keys
- [ ] **Clerk** — create application, copy publishable + secret keys
- [ ] **Upstash** — create Redis database, copy REST URL + token
- [ ] **Resend** — verify domain, copy API key
- [ ] **Cloudflare R2** — create bucket, generate API token, copy credentials
- [ ] **PostHog** — create project, copy project key
- [ ] **Sentry** — create project, copy DSN
- [ ] **BetterStack** — create source, copy ingestion token

## Deploy

{deploy}

## rob-stack CLI

This project was generated with [rob-stack](https://github.com/yourusername/rob-stack).

Useful commands:
- `rob-stack check .` — audit this repo for conformance to the canonical stack
- `rob-stack check . --service clerk` — check a single service
- `rob-stack new --dry-run` — preview files without writing
"""
