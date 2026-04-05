# TODO

Tasks are organized by priority. Items marked **[BROKEN]** are bugs in currently generated code and should be fixed first.

---

## 🔴 Critical — Broken Generated Code

These are bugs in the templates that produce non-functional code.

- [ ] **[BROKEN] Go R2 upload signing is a stub**
  `api/internal/storage/r2.go` — `signRequest()` sets the date headers but the HMAC computation is discarded (`_ = hmac.New(...)`). Uploads will fail R2 authentication. Fix: implement full AWS Signature V4, or switch to using a [CF R2 binding](https://developers.cloudflare.com/r2/api/workers/workers-api-usage/) directly from the Worker (no signing needed when accessed via binding).

- [ ] **[BROKEN] Go Clerk JWT verification calls a wrong endpoint**
  `api/internal/middleware/clerk.go` — `/v1/tokens/verify` with an `X-Token` header does not exist in Clerk's API. Fix: fetch Clerk's JWKS from `https://<your-clerk-domain>/.well-known/jwks.json`, cache it, and verify the JWT locally using a Go JWT library (`golang-jwt/jwt`). The `CLERK_JWKS_URL` env var should be added to `.env.example`.

- [ ] **[BROKEN] Go user ID stored in request header instead of context**
  `api/internal/middleware/clerk.go` — user ID is passed downstream via `r.Header.Set("X-User-ID", ...)` rather than `context.WithValue`. This is non-idiomatic and could be overridden by a client. Fix: define a typed context key and store user ID with `context.WithValue`.

---

## 🟠 Missing Generated Files

Files that should be scaffolded but aren't.

- [ ] **Next.js: Auth pages not generated**
  Clerk middleware redirects unauthenticated users to `/sign-in` and `/sign-up` but those pages are never created. Generate:
  - `src/app/(auth)/sign-in/[[...sign-in]]/page.tsx` — Clerk `<SignIn />` component
  - `src/app/(auth)/sign-up/[[...sign-up]]/page.tsx` — Clerk `<SignUp />` component
  - `src/app/(auth)/layout.tsx` — centered layout wrapper

- [ ] **Next.js: `instrumentation.ts` not generated**
  `next.config.ts` enables `instrumentationHook: true` for Sentry but the required `instrumentation.ts` file is never created. Generate it with Sentry's `onRequestError` hook wired up.

- [ ] **Next.js: Dashboard page not generated**
  `.env.example` sets `AFTER_SIGN_IN_URL=/dashboard` but `src/app/dashboard/page.tsx` doesn't exist.

- [ ] **Go: `.dev.vars` file not generated**
  Cloudflare Workers uses `.dev.vars` (not `.env`) for local secrets when running `wrangler dev`. The Go template generates `api/.env.example` but doesn't produce `api/.dev.vars.example`. Wrangler will ignore a regular `.env` file.

- [ ] **Go: `go.sum` not generated**
  A `go.sum` file is required for reproducible Go builds. Currently the user must run `go mod tidy` manually (which also requires network access to download deps). Either generate a placeholder with instructions or add a `make tidy` step prominently to the post-generate output.

- [ ] **Go: GitHub module path is hardcoded**
  `go.mod` is generated with `module github.com/yourusername/<name>`. The `new` command should prompt for a GitHub username (or full module path) so this is correct from the start.

- [ ] **Supabase migrations directory not generated**
  Generate a `supabase/migrations/` directory with an initial `001_init.sql` containing the `CREATE SCHEMA` + `GRANT` SQL so it's version controlled and not just in the README.

- [ ] **GitHub Actions CI/CD not generated**
  Generate `.github/workflows/`:
  - `ci.yml` — lint + type-check on PR (both Next.js and Go)
  - `deploy.yml` — deploy on push to `main` (Vercel CLI for Next.js, Wrangler for Go)

- [ ] **No concurrent dev script for Go + React**
  Running the Go Worker (`wrangler dev`) and Vite (`npm run dev`) simultaneously requires two terminals. Add a root-level `package.json` with a `dev` script using `concurrently` to start both with one command.

---

## 🟡 CLI Improvements

- [ ] **`rob-stack version` command**
  Print the installed version from `pyproject.toml`. Useful for debugging and confirming updates.

- [ ] **`--dry-run` flag for `new`**
  Print the list of files that would be generated without writing anything. Useful for previewing before committing.

- [ ] **`rob-stack check` migration prompt uses wrong path for Go**
  The generated Claude Code prompt references `src/lib/<service>.ts` as the target for new client files. For Go projects it should reference `api/internal/<service>/`.

- [ ] **`rob-stack check` should detect more alternative providers**
  Current detection of alternatives is incomplete. Add:
  - Auth: `supabase` (as auth provider, not DB), `firebase`
  - Storage: `@vercel/blob`, `uploadthing`
  - Analytics: `@vercel/analytics`, Google Analytics (`gtag`)
  - Hosting: `fly.toml` (Fly.io), `Procfile` (Heroku), `Dockerfile` without wrangler

- [ ] **`rob-stack check` should verify SDK initialization, not just package presence**
  Currently passing requires only that the package appears in `package.json` or `go.mod`. A more useful check would scan source files to confirm the client is actually instantiated (e.g., `posthog.init(` exists, `Sentry.init(` exists, `ClerkProvider` is in the layout).

- [ ] **`rob-stack check --service <name>` for targeted checks**
  Allow checking a single service in isolation: `rob-stack check . --service clerk`

---

## 🟢 Template Quality Improvements

- [ ] **TinyGo stdlib compatibility audit**
  Not all Go standard library packages work in TinyGo. The generated Go code uses `crypto/hmac`, `crypto/sha256`, `encoding/json`, `net/http`, `fmt`, `io`, `bytes` — these need to be verified against TinyGo's [supported packages list](https://tinygo.org/docs/reference/lang-support/stdlib/). `net/http` client support in TinyGo targets wasm is limited and may require `github.com/syumai/workers`'s fetch wrapper instead.

- [ ] **Go PostHog client not generated**
  The Next.js template generates `src/lib/posthog.ts` (server-side). The Go template has no PostHog HTTP client. Generate `api/internal/analytics/posthog.go` that POSTs capture events to `https://us.i.posthog.com/capture/`.

- [ ] **Go BetterStack logging not generated**
  Neither arch generates actual BetterStack log shipping code. Generate a simple logging wrapper that ships to BetterStack's HTTP ingest endpoint. For Next.js, wire it into `instrumentation.ts`. For Go, create `api/internal/logger/betterstack.go`.

- [ ] **Next.js: PostHog pageview tracking not implemented**
  `providers.tsx` initializes PostHog with `capture_pageview: false` but no pageview tracking is added. Generate a `usePathname`-based pageview hook and call it from the layout.

- [ ] **Resend: No email templates generated**
  `sendEmail()` accepts raw HTML. Generate at least one React Email template (e.g., a welcome email) in `src/emails/welcome.tsx` so there's a real example to build from.

- [ ] **Go: CORS config only supports single origin**
  `FRONTEND_URL` allows one origin. For apps with both a web and mobile client hitting the same Worker, the CORS config needs to accept a list. Update the template to parse `ALLOWED_ORIGINS` as a comma-separated list.

---

## ⚪ Nice to Have

- [ ] **Tests for the Python package**
  No tests exist. At minimum: unit tests for each `check_*` function in `check.py` with fixtures representing conforming and non-conforming repos, and smoke tests for `generate_nextjs` and `generate_go_cloudflare` verifying the expected file set is written.

- [ ] **`rob-stack upgrade` command**
  For an existing project generated by an older version of the tool, apply diffs to bring it up to the current template (e.g., add a missing `instrumentation.ts`, update a `wrangler.toml` field). Hard to implement correctly but high value over time.

- [ ] **Interactive service account setup**
  After generating a project, optionally open browser tabs to each service's new-project page (Supabase, Clerk, Upstash, etc.) in sequence.

- [ ] **`rob-stack check` JSON output mode**
  `rob-stack check . --json` for machine-readable output, useful for piping into other scripts or CI.

- [ ] **Config file support**
  Support a `.rob-stack.toml` at repo root that stores project metadata (name, architecture, services enabled) so `check` doesn't have to infer everything from the file tree.
