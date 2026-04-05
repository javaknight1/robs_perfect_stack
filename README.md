# rob-stack

A personal CLI for generating and auditing projects built on Rob's canonical tech stack. Two commands: `new` scaffolds a full project in under a minute, `check` audits any existing repo for conformance and generates a Claude Code migration prompt.

---

## Stack

Every generated project is wired to the same set of services:

| Layer | Service |
|---|---|
| Database | Supabase (schema-per-app isolation) |
| Cache | Upstash Redis |
| Auth | Clerk |
| Email | Resend |
| Storage | Cloudflare R2 |
| Analytics | PostHog |
| Error tracking | Sentry |
| Logs / Uptime | BetterStack |

Two architecture options, chosen per project:

| Option | Frontend | Backend | Deploy |
|---|---|---|---|
| **Next.js** | Next.js (App Router) | Next.js API routes / Server Actions | Vercel |
| **Go + React** | React (Vite) | Go (Cloudflare Workers via WASM) | Cloudflare Pages + Workers |

An optional Expo mobile app can be added to either.

---

## Prerequisites

- Python 3.11+
- pip

For **Go + React** projects you generate, you will also need:
- [TinyGo](https://tinygo.org/getting-started/install/) — compiles Go to Cloudflare Workers-compatible WASM
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/) — `npm install -g wrangler`
- A Cloudflare account

For **Next.js** projects:
- [Vercel CLI](https://vercel.com/docs/cli) (optional) — `npm install -g vercel`

---

## Installation

Clone the repo and install it as an editable local Python package. This adds `rob-stack` to your PATH permanently.

```bash
git clone https://github.com/yourusername/rob-stack.git
cd rob-stack
pip install -e .
```

Verify:

```bash
rob-stack --help
```

To update after pulling new changes:

```bash
cd rob-stack
git pull
# No reinstall needed — editable install picks up changes automatically
```

---

## Commands

### `rob-stack new`

Interactively scaffolds a new project. Run it from the directory where you want the project folder created.

```bash
cd ~/projects
rob-stack new
```

You will be asked four questions:

```
Project name (kebab-case): my-app

Description (one-liner for README / package.json): A web app for tracking leagues

Architecture:
  1. Next.js  ──▶  Vercel
  2. Go + React ──▶  Cloudflare Workers (API) + Cloudflare Pages (web)
Choose [1/2]: 1

Include Expo mobile app? [y/n]: n
```

A new directory `my-app/` is created with the full boilerplate. After generation:

**1. Create your Supabase schema** (run once in the Supabase SQL editor):
```sql
CREATE SCHEMA my_app;
CREATE ROLE my_app_app LOGIN PASSWORD 'YOUR_STRONG_PASSWORD';
GRANT USAGE ON SCHEMA my_app TO my_app_app;
GRANT ALL ON ALL TABLES IN SCHEMA my_app TO my_app_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA my_app
  GRANT ALL ON TABLES TO my_app_app;
```

**2. Fill in your environment variables:**
```bash
cd my-app
cp .env.example .env.local     # Next.js
# or
cp api/.env.example api/.env   # Go + React
cp web/.env.example web/.env
```

**3. Provision each service** (see service checklist below).

**4. Run locally:**
```bash
# Next.js
npm install && npm run dev

# Go + React (two terminals)
cd api && wrangler dev        # Worker runs at localhost:8787
cd web && npm run dev         # Vite runs at localhost:5173
```

#### What gets generated

**Next.js:**
```
my-app/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # ClerkProvider + PostHog wired
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   └── providers.tsx       # PostHog client provider
│   └── lib/
│       ├── supabase.ts         # Admin + anon clients, schema-scoped
│       ├── redis.ts            # Upstash Redis with typed helpers
│       ├── resend.ts           # sendEmail() wrapper
│       ├── r2.ts               # upload, delete, presign helpers
│       └── posthog.ts          # Server-side captureEvent()
├── middleware.ts               # Clerk JWT auth on all non-public routes
├── .env.example                # All required env vars listed
├── vercel.json
├── next.config.ts              # Sentry integrated
├── tailwind.config.ts
├── tsconfig.json
├── docker-compose.yml          # Local dev services
├── scripts/init-db.sql         # Supabase schema setup SQL
├── README.md                   # Project README with setup instructions
└── .gitignore
```

**Go + React:**
```
my-app/
├── web/                        # React (Vite) → Cloudflare Pages
│   ├── src/
│   │   ├── main.tsx            # Clerk + Sentry + PostHog initialized
│   │   ├── App.tsx
│   │   └── lib/api.ts          # Authenticated API client hook
│   ├── wrangler.toml           # Cloudflare Pages config
│   └── .env.example
├── api/                        # Go → Cloudflare Worker (WASM)
│   ├── cmd/worker/main.go      # Worker entry point (chi router)
│   ├── internal/
│   │   ├── supabase/client.go  # PostgREST HTTP client (schema-isolated)
│   │   ├── cache/redis.go      # Upstash HTTP REST client
│   │   ├── middleware/clerk.go # JWT verification middleware
│   │   ├── email/resend.go     # Resend HTTP client
│   │   └── storage/r2.go      # R2 S3-compatible upload client
│   ├── wrangler.toml           # Cloudflare Worker config
│   └── .env.example
├── Makefile                    # build, deploy, dev targets
├── docker-compose.yml          # Local dev services
├── scripts/init-db.sql         # Supabase schema setup SQL
├── README.md                   # Project README with setup instructions
└── .gitignore
```

**Mobile (Expo, optional):**
```
my-app/mobile/
├── app/
│   ├── _layout.tsx             # ClerkProvider with SecureStore token cache
│   ├── index.tsx               # Home screen with auth state
│   └── (auth)/sign-in.tsx      # Sign-in screen
├── lib/api.ts                  # Authenticated API client hook (same pattern as web)
└── .env.example
```

---

### `rob-stack check [path]`

Audits a repo for conformance to the stack. Defaults to the current directory.

```bash
rob-stack check .
rob-stack check ~/projects/league-looper
rob-stack check ../pagebound
```

#### Example output

```
🔍  Checking: /Users/rob/projects/league-looper
    Architecture: Go + React → Cloudflare Workers + Pages

  Service                      Status   Notes
  ────────────────────────────────────────────────────────────────────────
  Supabase                     ✅        @supabase/supabase-js or pgx detected
  Supabase schema isolation    ❌        No schema isolation detected
  Upstash Redis                ❌        Wrong client: 'ioredis' found
                                        💡 Replace 'ioredis' with @upstash/redis
  Clerk                        ✅        '@clerk/clerk-react' detected
  Resend                       ❌        Wrong email provider: 'nodemailer' found
                                        💡 Replace 'nodemailer' with 'resend'
  Cloudflare R2                ⚠️        @aws-sdk/client-s3 found but R2_ACCOUNT_ID missing
  PostHog                      ✅        posthog-js detected
  Sentry                       ❌        Not detected
  BetterStack                  ❌        Not detected
  Hosting (Cloudflare)         ✅        wrangler.toml detected
  Mobile (Expo)                ➖        No mobile/ directory (optional)

  Conformance score: 4/10 (40%)
```

#### Status icons

| Icon | Meaning |
|---|---|
| ✅ | Service detected and correctly configured |
| ⚠️ | Partially detected — likely a misconfiguration |
| ❌ | Missing or wrong provider found |
| ➖ | Optional — not required |

#### Claude Code migration prompt

When gaps are detected, the checker automatically generates a prompt you can paste directly into Claude Code inside the repo:

```
─── 📋 Claude Code Migration Prompt ────────────────────────────────
Copy and paste the following into Claude Code inside this repo:

"""
Refactor this project to conform to Rob's canonical tech stack.

Architecture: Go + React → Cloudflare Workers + Pages

The following components need to be added or replaced:
- Replace 'ioredis' with @upstash/redis
- Replace 'nodemailer' with 'resend'
- Add Sentry (@sentry/react)
- Add BetterStack (BETTERSTACK_SOURCE_TOKEN env var)
- Add Supabase schema isolation (search_path or Accept-Profile header)
...
"""
────────────────────────────────────────────────────────────────────
```

---

## Service Checklist

When starting a new project, create accounts / projects for each service once:

| Service | Action | Where to get keys |
|---|---|---|
| Supabase | Create project, run schema SQL | Settings → Database |
| Clerk | Create application | Dashboard → API Keys |
| Upstash | Create Redis database | Console → REST API |
| Resend | Add domain, verify DNS | API Keys |
| Cloudflare R2 | Create bucket, create API token | R2 → Manage R2 API tokens |
| PostHog | Create project | Project Settings |
| Sentry | Create project (Next.js or React) | Settings → Client Keys |
| BetterStack | Create log source | Sources → Connect source |

---

## Architecture Guide

### When to pick Next.js

- Shipping fast — one repo, one deploy
- SEO matters (marketing pages + app in one)
- Mostly CRUD with straightforward data flows
- No mobile app planned initially

### When to pick Go + React

- A mobile app is part of the plan (Go API serves both web and mobile)
- You want a clearly separated, independently scalable API
- High-throughput backend expected
- You prefer Go's performance and type system for the API layer

### Go + Cloudflare Workers constraints

Cloudflare Workers run on a non-standard WASM runtime. Two things to know:

**No raw TCP connections.** This means `pgx` (direct Postgres) doesn't work. The generated code uses Supabase's PostgREST HTTP API instead, with `Accept-Profile` / `Content-Profile` headers for schema isolation. This is functionally equivalent at low-to-medium scale.

**TinyGo required.** Standard Go's WASM output targets browser environments and is not compatible with the Cloudflare Workers WASM runtime. TinyGo targets it correctly. The Makefile handles this: `tinygo build -o build/worker.wasm -target wasm ./cmd/worker`.

---

## Supabase Schema Isolation

All apps share one Supabase project but each gets its own Postgres schema. This gives full data isolation without paying for multiple projects.

The generated SQL creates a dedicated role that can only access its own schema:

```sql
-- Each app gets this once
CREATE SCHEMA my_app;
CREATE ROLE my_app_app LOGIN PASSWORD '...';
GRANT USAGE ON SCHEMA my_app TO my_app_app;
GRANT ALL ON ALL TABLES IN SCHEMA my_app TO my_app_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA my_app
  GRANT ALL ON TABLES TO my_app_app;
```

**Next.js** — isolation enforced via connection string:
```
DATABASE_URL=postgresql://my_app_app:PASSWORD@...?search_path=my_app
```

**Go + React** — isolation enforced via PostgREST headers:
```go
req.Header.Set("Accept-Profile",  "my_app")
req.Header.Set("Content-Profile", "my_app")
```

---

## Extending the Templates

All file templates live in `rob_stack/templates/`:

| File | Contains |
|---|---|
| `nextjs.py` | All Next.js file templates |
| `cloudflare.py` | All Go + CF Workers + Pages templates |
| `mobile.py` | All Expo templates |
| `shared.py` | `.gitignore`, `docker-compose.yml`, `init-db.sql`, `README.md` |

To add a new file to every generated project, add a template function and call `write()` inside the relevant `generate_*` function. To add a new service to the conformance checker, add a `check_<service>()` function in `check.py` and register it in `run_check()`.

---

## Repo Structure

```
rob-stack/
├── pyproject.toml                  # Package config; defines `rob-stack` CLI entry point
├── TODO.md                         # Project roadmap and planned features
└── rob_stack/
    ├── cli.py                      # Entry point: routes new | check | --help
    ├── generate.py                 # Interactive prompts + file writing logic
    ├── check.py                    # Conformance checker + migration prompt generator
    └── templates/
        ├── shared.py               # Shared templates (.gitignore, docker-compose, init-db, README)
        ├── nextjs.py               # Next.js file templates
        ├── cloudflare.py           # Go + Cloudflare templates
        └── mobile.py               # Expo mobile templates
```
