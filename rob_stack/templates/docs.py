"""Documentation templates (CLAUDE.md, CONTRIBUTING.md, ARCHITECTURE.md, DEPLOYMENT.md)."""


def claude_md(ctx: dict, is_nextjs: bool, has_mobile: bool) -> str:
    name = ctx["name"]
    schema = ctx["schema"]

    if is_nextjs:
        arch_line = "Next.js (App Router) on Vercel"
        key_files = """\
| `src/app/layout.tsx` | Root layout (Clerk + PostHog providers) |
| `src/app/api/*/route.ts` | API routes |
| `src/lib/supabase.ts` | Supabase client (admin + RLS) |
| `src/lib/redis.ts` | Upstash Redis helpers |
| `src/lib/resend.ts` | Resend email client |
| `src/lib/r2.ts` | Cloudflare R2 storage |
| `src/lib/posthog.ts` | Server-side PostHog analytics |
| `src/lib/swagger.ts` | OpenAPI spec config |
| `middleware.ts` | Clerk auth middleware |
| `instrumentation.ts` | Sentry instrumentation hook |"""
        commands = """\
| `make dev` | Start Supabase + Next.js dev server |
| `make build` | Production build |
| `make lint` | ESLint + TypeScript checks |
| `make test` | Run tests |
| `make deploy` | Deploy to Vercel |
| `make setup` | Install deps + start Supabase |"""
        ports = """\
| 3000 | Next.js dev server |
| 54321 | Supabase REST API |
| 54322 | Supabase Postgres |
| 54323 | Supabase Studio |
| 54324 | Inbucket (email testing) |"""
        env_file = ".env.local"
        conventions = """\
- API routes live in `src/app/api/` — each folder is an endpoint
- Use `supabaseAdmin` for server-side DB queries (bypasses RLS)
- Use `supabase` (anon client) only when forwarding user context"""
    else:
        arch_line = "Go API (Cloudflare Workers via TinyGo) + React SPA (Cloudflare Pages)"
        key_files = """\
| `api/cmd/worker/main.go` | Worker entry point + router |
| `api/internal/supabase/client.go` | Supabase REST client |
| `api/internal/cache/redis.go` | Upstash Redis HTTP client |
| `api/internal/middleware/clerk.go` | Clerk JWT verification (JWKS) |
| `api/internal/email/resend.go` | Resend email client |
| `api/internal/storage/r2.go` | Cloudflare R2 (S3-compatible signing) |
| `api/internal/analytics/posthog.go` | PostHog event capture |
| `api/internal/logger/betterstack.go` | BetterStack log shipping |
| `api/internal/openapi/spec.go` | OpenAPI spec + Swagger UI |
| `web/src/main.tsx` | React entry (Sentry + PostHog + Clerk) |
| `web/src/App.tsx` | Router with public/protected routes |
| `web/src/lib/api.ts` | Authenticated API client hook |"""
        commands = """\
| `make dev` | Start Supabase + API + web dev servers |
| `make build` | Build Worker WASM (TinyGo) |
| `make lint` | go vet + TypeScript checks |
| `make test` | Run tests |
| `make deploy` | Deploy API + web to Cloudflare |
| `make setup` | Install deps + start Supabase |"""
        ports = """\
| 5173 | Vite React dev server |
| 8787 | Wrangler API dev server |
| 54321 | Supabase REST API |
| 54322 | Supabase Postgres |
| 54323 | Supabase Studio |
| 54324 | Inbucket (email testing) |"""
        env_file = "api/.dev.vars"
        conventions = """\
- API endpoints are registered in `api/cmd/worker/main.go`
- Each service client lives in its own `api/internal/` package
- Use context-based auth: `middleware.UserIDFromContext(r.Context())`"""

    services = """\
| Supabase | Database (Postgres) | `%s` |
| Clerk | Auth (JWT) | `%s` |
| Upstash | Redis cache | `%s` |
| Resend | Transactional email | `%s` |
| R2 | Object storage | `%s` |
| PostHog | Product analytics | `%s` |
| Sentry | Error tracking | `%s` |
| BetterStack | Uptime + logs | `%s` |""" % (
        env_file, env_file, env_file, env_file,
        env_file, env_file, env_file, env_file,
    )

    mobile_section = ""
    if has_mobile:
        mobile_section = """
## Mobile (Expo)

- Source: `mobile/`
- Auth: Clerk (`@clerk/clerk-expo`)
- API calls: `mobile/lib/api.ts` (authenticated fetch hook)
- Config: `mobile/.env` and `mobile/app.json`
"""

    return f"""\
# {name}

## Architecture

{arch_line}
Database schema: `{schema}`

## Commands

| Command | Description |
|---------|-------------|
{commands}

## Local Ports

| Port | Service |
|------|---------|
{ports}

## Key Files

| File | Purpose |
|------|---------|
{key_files}

## Services

| Service | Role | Config |
|---------|------|--------|
{services}

## Conventions

- All app tables go in the `{schema}` Postgres schema (not `public`)
- Migrations: `supabase migration new <name>`, edit SQL, `supabase db reset`
- Auth: Clerk handles all authentication; JWTs are verified server-side
{conventions}
- Environment variables: copy from `.env.example`, fill in service keys
{mobile_section}"""


def contributing_md(ctx: dict, is_nextjs: bool, has_mobile: bool) -> str:
    name = ctx["name"]

    if is_nextjs:
        code_standards = """\
- **Linting**: ESLint (`npm run lint` or `make lint`)
- **Type checking**: TypeScript strict mode (`npx tsc --noEmit`)
- **Formatting**: Prettier (configure as needed)
- **Imports**: Use `@/` path alias for `src/` imports"""
        add_endpoint = """\
1. Create a new folder under `src/app/api/` (e.g. `src/app/api/widgets/`)
2. Add `route.ts` with exported HTTP method handlers (`GET`, `POST`, etc.)
3. Add `@swagger` JSDoc annotations for OpenAPI documentation
4. Use `auth()` from `@clerk/nextjs/server` for protected routes
5. Access the database via `supabaseAdmin` from `src/lib/supabase.ts`"""
        add_service = """\
1. Create a new file in `src/lib/` (e.g. `src/lib/my-service.ts`)
2. Read config from `process.env` and add variables to `.env.example`
3. Export an initialized client or helper functions"""
        testing = """\
```bash
make test          # Run all tests
npm run lint       # Lint check
npx tsc --noEmit   # Type check
```"""
    else:
        code_standards = """\
- **Go**: `go vet ./...` and `gofmt -s -w .` (run from `api/`)
- **TypeScript**: ESLint for the web app (`cd web && npm run lint`)
- **Formatting**: `gofmt` for Go, Prettier for TypeScript"""
        add_endpoint = """\
1. Define your handler function in a new or existing `api/internal/` package
2. Register the route in `api/cmd/worker/main.go`
3. Add the endpoint to the OpenAPI spec in `api/internal/openapi/spec.go`
4. For protected routes, wrap with `middleware.RequireAuth(handler)`
5. Access user ID via `middleware.UserIDFromContext(r.Context())`"""
        add_service = """\
1. Create a new package under `api/internal/` (e.g. `api/internal/myservice/`)
2. Read config from environment variables via `os.Getenv()`
3. Add variables to `api/.env.example` and `api/.dev.vars.example`
4. Import and use in `main.go` or other handlers"""
        testing = """\
```bash
make test           # Run all tests
make lint           # Go vet + TypeScript lint
cd api && go test ./...   # Go tests only
cd web && npm test        # Web tests only
```"""

    mobile_section = ""
    if has_mobile:
        mobile_section = """
## Mobile Development

- Run `cd mobile && npx expo start` to launch the dev server
- Use `mobile/lib/api.ts` for authenticated API calls
- Add screens under `mobile/app/`
"""

    return f"""\
# Contributing to {name}

## Getting Started

```bash
make setup    # Install dependencies + start Supabase
make dev      # Start all dev servers
```

## Branch Workflow

- `main` — production-ready code
- `feature/<name>` — new features
- `fix/<name>` — bug fixes

Create a branch from `main`, make your changes, open a PR.

## Code Standards

{code_standards}

## Adding API Endpoints

{add_endpoint}

## Adding Service Clients

{add_service}

## Database Changes

1. Create a migration: `supabase migration new <descriptive_name>`
2. Edit the generated SQL file in `supabase/migrations/`
3. Apply locally: `supabase db reset`
4. Commit the migration file

All tables should be created in the `{ctx["schema"]}` schema.

## Testing

{testing}
{mobile_section}
## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation only
- `refactor:` code change that neither fixes a bug nor adds a feature
- `test:` adding or updating tests
- `chore:` maintenance tasks

## CI Pipeline

Every PR triggers:
1. Lint + type check
2. Tests
3. Build verification

Merges to `main` trigger automatic deployment.
"""


def architecture_md(ctx: dict, is_nextjs: bool, has_mobile: bool) -> str:
    name = ctx["name"]
    schema = ctx["schema"]

    if is_nextjs:
        stack_table = """\
| Frontend | Next.js (App Router) | SSR + React Server Components |
| Backend | Next.js API Routes | Serverless API endpoints |
| Hosting | Vercel | Automatic deployments from `main` |"""
        request_flow = """\
### Unauthenticated Request
```
Browser → Vercel Edge → Next.js → API Route → Response
```

### Authenticated Request
```
Browser → Vercel Edge → Clerk Middleware (JWT check)
  → Next.js → API Route → auth() → Supabase/Redis/etc → Response
```"""
        data_flow = """\
```
Client ──→ Next.js (Vercel)
             ├──→ Clerk (auth)
             ├──→ Supabase (database)
             ├──→ Upstash Redis (cache)
             ├──→ Resend (email)
             ├──→ R2 (storage)
             ├──→ PostHog (analytics)
             └──→ Sentry (errors)
```"""
        deploy_topology = """\
```
GitHub ──push──→ GitHub Actions (CI)
                   └──→ Vercel (deploy)
                          ├── Next.js app
                          └── Serverless functions
```"""
        design_decisions = """\
| Clerk | Managed auth with JWT — no session tables, works at the edge |
| Upstash Redis | HTTP-based Redis — works in serverless without TCP connections |
| Cloudflare R2 | S3-compatible storage with no egress fees |
| Schema isolation | App tables in `{schema}` schema — clean separation from Supabase internals |
| Supabase | Managed Postgres with instant REST API, local dev via CLI |""".format(schema=schema)
    else:
        stack_table = """\
| Frontend | React (Vite) | SPA with client-side routing |
| Backend | Go (TinyGo → WASM) | Cloudflare Workers API |
| API Hosting | Cloudflare Workers | Edge-deployed Go API |
| Web Hosting | Cloudflare Pages | Static site hosting |"""
        request_flow = """\
### Unauthenticated Request
```
Browser → Cloudflare Pages (static)
Browser → Cloudflare Workers → Go handler → Response
```

### Authenticated Request
```
Browser → Cloudflare Workers → Clerk Middleware (JWKS verification)
  → Go handler → Supabase/Redis/etc → Response
```"""
        data_flow = """\
```
React SPA (Cloudflare Pages)
  └──→ Go API (Cloudflare Workers)
         ├──→ Clerk (JWKS auth)
         ├──→ Supabase (database)
         ├──→ Upstash Redis (cache)
         ├──→ Resend (email)
         ├──→ R2 (storage)
         ├──→ PostHog (analytics)
         ├──→ BetterStack (logs)
         └──→ Sentry (errors)
```"""
        deploy_topology = """\
```
GitHub ──push──→ GitHub Actions (CI)
                   ├──→ Cloudflare Workers (API deploy)
                   └──→ Cloudflare Pages (web deploy)
```"""
        design_decisions = """\
| Clerk | Managed auth — JWKS verification at the edge, no session storage |
| Upstash Redis | HTTP-based Redis — works in Workers without TCP |
| Cloudflare R2 | S3-compatible storage, same network as Workers |
| TinyGo + WASM | Compiles Go to WASM for Cloudflare Workers runtime |
| Schema isolation | App tables in `{schema}` schema — clean separation from Supabase internals |
| Supabase | Managed Postgres with REST API — accessed via HTTP from Workers |""".format(schema=schema)

    mobile_section = ""
    if has_mobile:
        mobile_section = """
## Mobile Architecture

The Expo (React Native) app shares auth with the web via Clerk:

```
Expo App
  ├── Clerk (auth via @clerk/clerk-expo)
  ├── API calls (authenticated fetch → same backend)
  ├── PostHog (mobile analytics)
  └── Sentry (mobile error tracking)
```

The mobile app communicates with the same backend API.
"""

    return f"""\
# Architecture — {name}

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
{stack_table}
| Database | Supabase (Postgres) | App data in `{schema}` schema |
| Cache | Upstash Redis | Rate limiting, sessions, ephemeral data |
| Auth | Clerk | User authentication + JWT tokens |
| Email | Resend | Transactional email delivery |
| Storage | Cloudflare R2 | File/object storage (S3-compatible) |
| Analytics | PostHog | Product analytics + feature flags |
| Errors | Sentry | Error tracking + performance monitoring |
| Logs | BetterStack | Uptime monitoring + log aggregation |

## Request Flow

{request_flow}

## Data Flow

{data_flow}

## Database Schema Isolation

All application tables live in the `{schema}` Postgres schema, **not** `public`.
This keeps app data cleanly separated from Supabase internal tables (`auth`, `storage`, etc.).

```sql
CREATE SCHEMA {schema};
-- All app tables: {schema}.users, {schema}.orders, etc.
```

A dedicated `{schema}_app` database role is scoped to this schema.

## Deployment Topology

{deploy_topology}

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
{design_decisions}
{mobile_section}"""


def deployment_md(ctx: dict, is_nextjs: bool, has_mobile: bool) -> str:
    name = ctx["name"]
    schema = ctx["schema"]

    if is_nextjs:
        env_table = """\
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | Supabase dashboard → Settings → API |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key | Supabase dashboard → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Supabase dashboard → Settings → API |
| `DATABASE_URL` | Postgres connection string | Supabase dashboard → Settings → Database |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key | Clerk dashboard → API Keys |
| `CLERK_SECRET_KEY` | Clerk secret key | Clerk dashboard → API Keys |
| `UPSTASH_REDIS_REST_URL` | Upstash Redis URL | Upstash console → Database details |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash Redis token | Upstash console → Database details |
| `RESEND_API_KEY` | Resend API key | Resend dashboard → API Keys |
| `R2_ACCOUNT_ID` | Cloudflare account ID | Cloudflare dashboard → Overview |
| `R2_ACCESS_KEY_ID` | R2 access key | Cloudflare dashboard → R2 → API Tokens |
| `R2_SECRET_ACCESS_KEY` | R2 secret key | Cloudflare dashboard → R2 → API Tokens |
| `R2_BUCKET_NAME` | R2 bucket name | You choose when creating the bucket |
| `NEXT_PUBLIC_POSTHOG_KEY` | PostHog project key | PostHog → Project Settings |
| `NEXT_PUBLIC_POSTHOG_HOST` | PostHog ingest host | Usually `https://us.i.posthog.com` |
| `SENTRY_DSN` | Sentry DSN | Sentry → Project Settings → Client Keys |
| `BETTERSTACK_SOURCE_TOKEN` | BetterStack token | BetterStack → Sources |"""
        deploy_steps = """\
## Deploy to Vercel

1. Push your repo to GitHub
2. Go to [vercel.com](https://vercel.com) and import the repository
3. Set **Framework Preset** to "Next.js"
4. Add all environment variables from the table above
5. Click **Deploy**

Vercel automatically deploys on every push to `main`.

### Custom Domain

1. Vercel dashboard → Project → Settings → Domains
2. Add your domain and configure DNS as instructed
3. Update `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` if using a production Clerk instance"""
    else:
        env_table = """\
| `SUPABASE_URL` | Supabase project URL | Supabase dashboard → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Supabase dashboard → Settings → API |
| `CLERK_SECRET_KEY` | Clerk secret key | Clerk dashboard → API Keys |
| `CLERK_JWKS_URL` | Clerk JWKS endpoint | Clerk dashboard → API Keys → Advanced |
| `UPSTASH_REDIS_REST_URL` | Upstash Redis URL | Upstash console → Database details |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash Redis token | Upstash console → Database details |
| `RESEND_API_KEY` | Resend API key | Resend dashboard → API Keys |
| `R2_ACCOUNT_ID` | Cloudflare account ID | Cloudflare dashboard → Overview |
| `R2_ACCESS_KEY_ID` | R2 access key | Cloudflare dashboard → R2 → API Tokens |
| `R2_SECRET_ACCESS_KEY` | R2 secret key | Cloudflare dashboard → R2 → API Tokens |
| `R2_BUCKET_NAME` | R2 bucket name | You choose when creating the bucket |
| `POSTHOG_KEY` | PostHog project key | PostHog → Project Settings |
| `SENTRY_DSN` | Sentry DSN | Sentry → Project Settings → Client Keys |
| `BETTERSTACK_SOURCE_TOKEN` | BetterStack token | BetterStack → Sources |
| `VITE_CLERK_PUBLISHABLE_KEY` | Clerk publishable key | Clerk dashboard → API Keys |
| `VITE_API_URL` | Production API URL | Your Workers URL (e.g. `https://api.example.com`) |
| `VITE_POSTHOG_KEY` | PostHog project key | PostHog → Project Settings |
| `VITE_SENTRY_DSN` | Sentry DSN (web) | Sentry → Project Settings → Client Keys |"""
        deploy_steps = """\
## Deploy API (Cloudflare Workers)

1. Install Wrangler: `npm install -g wrangler`
2. Authenticate: `wrangler login`
3. Set secrets:
   ```bash
   cd api
   wrangler secret put SUPABASE_URL
   wrangler secret put SUPABASE_SERVICE_ROLE_KEY
   wrangler secret put CLERK_SECRET_KEY
   wrangler secret put CLERK_JWKS_URL
   wrangler secret put UPSTASH_REDIS_REST_URL
   wrangler secret put UPSTASH_REDIS_REST_TOKEN
   wrangler secret put RESEND_API_KEY
   wrangler secret put POSTHOG_KEY
   wrangler secret put BETTERSTACK_SOURCE_TOKEN
   ```
4. Deploy: `wrangler deploy`

## Deploy Web (Cloudflare Pages)

1. Go to [Cloudflare Pages](https://pages.cloudflare.com)
2. Connect your GitHub repo
3. Set build command: `cd web && npm run build`
4. Set output directory: `web/dist`
5. Add environment variables (`VITE_*` prefixed)
6. Deploy"""

    db_setup = f"""\
## Database (Production)

Run in the Supabase SQL editor:

```sql
CREATE SCHEMA {schema};
CREATE ROLE {schema}_app LOGIN PASSWORD 'YOUR_STRONG_PASSWORD';
GRANT USAGE ON SCHEMA {schema} TO {schema}_app;
GRANT ALL ON ALL TABLES IN SCHEMA {schema} TO {schema}_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA {schema}
  GRANT ALL ON TABLES TO {schema}_app;
```

Then apply migrations:
```bash
supabase link --project-ref YOUR_PROJECT_REF
supabase db push
```"""

    gh_secrets = """\
## GitHub Actions Secrets

Set these in your repo's Settings → Secrets and variables → Actions:

| Secret | Description |
|--------|-------------|"""
    if is_nextjs:
        gh_secrets += """
| `VERCEL_TOKEN` | Vercel API token |
| `VERCEL_ORG_ID` | Vercel org/team ID |
| `VERCEL_PROJECT_ID` | Vercel project ID |"""
    else:
        gh_secrets += """
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token (Workers + Pages) |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account ID |"""

    verification = """\
## Verification Checklist

After deploying, verify each service:

- [ ] **Health endpoint**: `curl https://YOUR_DOMAIN%s` returns `ok`
- [ ] **Auth**: Sign up and sign in works via Clerk
- [ ] **Database**: App can read/write to Supabase
- [ ] **Sentry**: Trigger a test error and check Sentry dashboard
- [ ] **PostHog**: Visit the app and check PostHog for events
- [ ] **BetterStack**: Verify logs appear in BetterStack console""" % (
        "/api/health" if is_nextjs else "/health"
    )

    mobile_section = ""
    if has_mobile:
        mobile_section = """
## Mobile Deployment (Expo / EAS)

1. Install EAS CLI: `npm install -g eas-cli`
2. Configure: `cd mobile && eas build:configure`
3. Set environment variables in `mobile/.env`:
   - `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - `EXPO_PUBLIC_API_URL` (production API URL)
   - `EXPO_PUBLIC_POSTHOG_KEY`
   - `EXPO_PUBLIC_SENTRY_DSN`
4. Build:
   ```bash
   eas build --platform ios
   eas build --platform android
   ```
5. Submit:
   ```bash
   eas submit --platform ios
   eas submit --platform android
   ```
"""

    return f"""\
# Deployment — {name}

## Environment Variables

| Variable | Description | Where to find |
|----------|-------------|---------------|
{env_table}

{db_setup}

{deploy_steps}

{gh_secrets}

{verification}
{mobile_section}"""
