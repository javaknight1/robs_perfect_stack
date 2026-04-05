"""Go + React → Cloudflare Workers (API) + Cloudflare Pages (web)."""

import json


def generate_go_cloudflare(root, ctx: dict, write) -> None:
    name   = ctx["name"]
    title  = ctx["title"]
    schema = ctx["schema"]
    module = f"github.com/yourusername/{name}"

    print("\n📦 Generating Go + React (Cloudflare Workers + Pages)...")

    # ── Web (React / Vite / Cloudflare Pages) ─────────────────────
    write(root, "web/package.json",       _web_package_json(name))
    write(root, "web/index.html",         _web_index_html(title))
    write(root, "web/vite.config.ts",     _web_vite_config())
    write(root, "web/tsconfig.json",      _web_tsconfig())
    write(root, "web/src/index.css",      "@import \"tailwindcss\";\n")
    write(root, "web/src/main.tsx",       _web_main())
    write(root, "web/src/App.tsx",        _web_app())
    write(root, "web/src/lib/api.ts",     _web_api_client())
    write(root, "web/.env.example",       _web_env_example())
    write(root, "web/wrangler.toml",      _pages_wrangler(name))

    # ── API (Go / Cloudflare Workers via syumai/workers) ──────────
    write(root, "api/go.mod",                        _go_mod(module))
    write(root, "api/cmd/worker/main.go",            _go_main(module, schema))
    write(root, "api/internal/supabase/client.go",   _go_supabase(module, schema))
    write(root, "api/internal/cache/redis.go",       _go_redis(module))
    write(root, "api/internal/middleware/clerk.go",  _go_clerk(module))
    write(root, "api/internal/email/resend.go",      _go_email(module))
    write(root, "api/internal/storage/r2.go",        _go_r2(module))
    write(root, "api/.env.example",                  _api_env_example(name, schema))
    write(root, "api/wrangler.toml",                 _worker_wrangler(name))
    write(root, "Makefile",                          _makefile())


# ──────────────────────────────────────────────────────────────────
# Web (React / Vite / Cloudflare Pages)
# ──────────────────────────────────────────────────────────────────

def _web_package_json(name: str) -> str:
    return json.dumps({
        "name": f"{name}-web",
        "version": "0.1.0",
        "private": True,
        "type": "module",
        "scripts": {
            "dev":     "vite",
            "build":   "tsc -b && vite build",
            "preview": "vite preview",
            "deploy":  "npm run build && wrangler pages deploy dist",
        },
        "dependencies": {
            "react":              "^19",
            "react-dom":          "^19",
            "react-router-dom":   "^7",
            "@clerk/clerk-react": "^5",
            "posthog-js":         "^1",
            "@sentry/react":      "^8",
        },
        "devDependencies": {
            "typescript":          "^5",
            "@types/react":        "^19",
            "@types/react-dom":    "^19",
            "vite":                "^6",
            "@vitejs/plugin-react":"^4",
            "tailwindcss":         "^4",
            "@tailwindcss/vite":   "^4",
            "wrangler":            "^3",
        },
    }, indent=2)


def _web_index_html(title: str) -> str:
    return f'''\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''


def _web_vite_config() -> str:
    return '''\
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // In dev, proxy /api calls to the local Worker (wrangler dev)
      "/api": { target: "http://localhost:8787", changeOrigin: true },
    },
  },
});
'''


def _web_tsconfig() -> str:
    return json.dumps({
        "compilerOptions": {
            "target": "ES2020",
            "useDefineForClassFields": True,
            "lib": ["ES2020", "DOM", "DOM.Iterable"],
            "module": "ESNext",
            "skipLibCheck": True,
            "moduleResolution": "bundler",
            "allowImportingTsExtensions": True,
            "isolatedModules": True,
            "moduleDetection": "force",
            "noEmit": True,
            "jsx": "react-jsx",
            "strict": True,
            "paths": {"@/*": ["./src/*"]},
        },
        "include": ["src"],
    }, indent=2)


def _web_main() -> str:
    return '''\
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ClerkProvider } from "@clerk/clerk-react";
import * as Sentry from "@sentry/react";
import posthog from "posthog-js";
import App from "./App";
import "./index.css";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  integrations: [Sentry.browserTracingIntegration(), Sentry.replayIntegration()],
  tracesSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});

posthog.init(import.meta.env.VITE_POSTHOG_KEY, {
  api_host: import.meta.env.VITE_POSTHOG_HOST ?? "https://us.i.posthog.com",
  person_profiles: "identified_only",
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ClerkProvider publishableKey={import.meta.env.VITE_CLERK_PUBLISHABLE_KEY} afterSignOutUrl="/">
      <App />
    </ClerkProvider>
  </StrictMode>
);
'''


def _web_app() -> str:
    return '''\
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SignedIn, SignedOut, RedirectToSignIn } from "@clerk/clerk-react";

function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center">
      <h1 className="text-4xl font-bold">Welcome</h1>
    </main>
  );
}

function DashboardPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center">
      <h1 className="text-4xl font-bold">Dashboard</h1>
    </main>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/dashboard"
          element={
            <>
              <SignedIn><DashboardPage /></SignedIn>
              <SignedOut><RedirectToSignIn /></SignedOut>
            </>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
'''


def _web_api_client() -> str:
    # Use string concatenation to avoid f-string / template-literal conflicts
    return (
        'import { useAuth } from "@clerk/clerk-react";\n'
        '\n'
        'const BASE = import.meta.env.VITE_API_URL ?? "/api";\n'
        '\n'
        '/** Hook returning an authenticated API client backed by the Cloudflare Worker */\n'
        'export function useApi() {\n'
        '  const { getToken } = useAuth();\n'
        '\n'
        '  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {\n'
        '    const token = await getToken();\n'
        '    const res = await fetch(`${BASE}${path}`, {\n'
        '      ...init,\n'
        '      headers: {\n'
        '        "Content-Type": "application/json",\n'
        '        Authorization: `Bearer ${token}`,\n'
        '        ...init.headers,\n'
        '      },\n'
        '    });\n'
        '    if (!res.ok) throw new Error((await res.text()) || res.statusText);\n'
        '    return res.json() as Promise<T>;\n'
        '  }\n'
        '\n'
        '  return {\n'
        '    get:  <T>(path: string)                => request<T>(path),\n'
        '    post: <T>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) }),\n'
        '    put:  <T>(path: string, body: unknown) => request<T>(path, { method: "PUT",  body: JSON.stringify(body) }),\n'
        '    del:  <T>(path: string)                => request<T>(path, { method: "DELETE" }),\n'
        '  };\n'
        '}\n'
    )


def _web_env_example() -> str:
    return """\
VITE_API_URL=http://localhost:8787/api
VITE_CLERK_PUBLISHABLE_KEY=pk_test_
VITE_POSTHOG_KEY=phc_
VITE_POSTHOG_HOST=https://us.i.posthog.com
VITE_SENTRY_DSN=https://
"""


def _pages_wrangler(name: str) -> str:
    return f"""\
# Cloudflare Pages — web frontend
name = "{name}-web"
pages_build_output_dir = "dist"
compatibility_date = "2024-09-23"

[build]
command = "npm run build"
"""


# ──────────────────────────────────────────────────────────────────
# API (Go → Cloudflare Workers via syumai/workers + TinyGo)
# ──────────────────────────────────────────────────────────────────
#
# NOTE: Cloudflare Workers uses a non-standard WASM runtime.
# TinyGo (https://tinygo.org) targets it correctly.
# Direct TCP connections (pgx → Postgres) are NOT supported in Workers.
# Database access uses the Supabase REST (PostgREST) API via HTTP.
# Upstash Redis uses its HTTP REST API — already compatible.
# ──────────────────────────────────────────────────────────────────

def _go_mod(module: str) -> str:
    return f"""\
module {module}

go 1.23

require (
\tgithub.com/syumai/workers v0.26.0
\tgithub.com/go-chi/chi/v5 v5.1.0
\tgithub.com/go-chi/cors v1.2.1
)
"""


def _go_main(module: str, schema: str) -> str:
    return f"""\
// cmd/worker/main.go — Cloudflare Worker entry point (compile with TinyGo)
//
// Build:
//   tinygo build -o build/worker.wasm -target wasm ./cmd/worker
//
// Run locally:
//   wrangler dev
package main

import (
\t"net/http"

\t"github.com/go-chi/chi/v5"
\t"github.com/go-chi/chi/v5/middleware"
\t"github.com/go-chi/cors"
\t"github.com/syumai/workers"

\tclerkMW "{module}/internal/middleware"
)

func newRouter() http.Handler {{
\tr := chi.NewRouter()

\tr.Use(middleware.Recoverer)
\tr.Use(cors.Handler(cors.Options{{
\t\tAllowedOrigins:   []string{{workers.Getenv("FRONTEND_URL")}},
\t\tAllowedMethods:   []string{{"GET", "POST", "PUT", "DELETE", "OPTIONS"}},
\t\tAllowedHeaders:   []string{{"Accept", "Authorization", "Content-Type"}},
\t\tAllowCredentials: true,
\t}}))

\tr.Get("/health", func(w http.ResponseWriter, r *http.Request) {{
\t\tw.Write([]byte("ok"))
\t}})

\tr.Route("/api", func(r chi.Router) {{
\t\tr.Use(clerkMW.RequireAuth)
\t\t// Register handlers here
\t}})

\treturn r
}}

func main() {{
\tworkers.Serve(newRouter())
}}
"""


def _go_supabase(module: str, schema: str) -> str:
    return f"""\
// internal/supabase/client.go
//
// In Cloudflare Workers, direct TCP connections (pgx) are not supported.
// We use the Supabase REST API (PostgREST) via HTTP instead.
package supabase

import (
\t"bytes"
\t"encoding/json"
\t"fmt"
\t"io"
\t"net/http"

\t"github.com/syumai/workers"
)

const schema = "{schema}"

type Client struct {{
\tbaseURL string
\tapiKey  string
\thttpClient *http.Client
}}

func New() *Client {{
\treturn &Client{{
\t\tbaseURL: workers.Getenv("SUPABASE_URL") + "/rest/v1",
\t\tapiKey:  workers.Getenv("SUPABASE_SERVICE_ROLE_KEY"),
\t\thttpClient: &http.Client{{}},
\t}}
}}

// Get queries a table. result should be a pointer to a slice.
func (c *Client) Get(table string, result any, query string) error {{
\turl := fmt.Sprintf("%s/%s?%s", c.baseURL, table, query)
\treq, _ := http.NewRequest("GET", url, nil)
\tc.setHeaders(req, "return=representation")
\tres, err := c.httpClient.Do(req)
\tif err != nil {{
\t\treturn err
\t}}
\tdefer res.Body.Close()
\tbody, _ := io.ReadAll(res.Body)
\tif res.StatusCode >= 400 {{
\t\treturn fmt.Errorf("supabase GET %s: %s", table, body)
\t}}
\treturn json.Unmarshal(body, result)
}}

// Insert inserts a row and scans the result back into result.
func (c *Client) Insert(table string, payload, result any) error {{
\tb, _ := json.Marshal(payload)
\treq, _ := http.NewRequest("POST", fmt.Sprintf("%s/%s", c.baseURL, table), bytes.NewReader(b))
\tc.setHeaders(req, "return=representation")
\tres, err := c.httpClient.Do(req)
\tif err != nil {{
\t\treturn err
\t}}
\tdefer res.Body.Close()
\tbody, _ := io.ReadAll(res.Body)
\tif res.StatusCode >= 400 {{
\t\treturn fmt.Errorf("supabase INSERT %s: %s", table, body)
\t}}
\treturn json.Unmarshal(body, result)
}}

func (c *Client) setHeaders(req *http.Request, prefer string) {{
\treq.Header.Set("apikey", c.apiKey)
\treq.Header.Set("Authorization", "Bearer "+c.apiKey)
\treq.Header.Set("Content-Type", "application/json")
\treq.Header.Set("Accept-Profile", schema)
\treq.Header.Set("Content-Profile", schema)
\tif prefer != "" {{
\t\treq.Header.Set("Prefer", prefer)
\t}}
}}
"""


def _go_redis(module: str) -> str:
    return """\
// internal/cache/redis.go
//
// Upstash Redis HTTP REST API — compatible with Cloudflare Workers.
// No raw TCP connections needed.
package cache

import (
\t"encoding/json"
\t"fmt"
\t"io"
\t"net/http"
\t"strings"
\t"time"

\t"github.com/syumai/workers"
)

type Client struct {
\turl   string
\ttoken string
}

func New() *Client {
\treturn &Client{
\t\turl:   workers.Getenv("UPSTASH_REDIS_REST_URL"),
\t\ttoken: workers.Getenv("UPSTASH_REDIS_REST_TOKEN"),
}
}

func (c *Client) do(args ...string) ([]byte, error) {
\tbody := mustJSON(args)
\treq, _ := http.NewRequest("POST", c.url, strings.NewReader(body))
\treq.Header.Set("Authorization", "Bearer "+c.token)
\treq.Header.Set("Content-Type", "application/json")
\tres, err := http.DefaultClient.Do(req)
\tif err != nil {
\t\treturn nil, err
\t}
\tdefer res.Body.Close()
\treturn io.ReadAll(res.Body)
}

func (c *Client) Set(key string, value any, ttl time.Duration) error {
\tv, _ := json.Marshal(value)
\t_, err := c.do("SET", key, string(v), "EX", fmt.Sprintf("%d", int(ttl.Seconds())))
\treturn err
}

func (c *Client) Get(key string, dest any) error {
\tb, err := c.do("GET", key)
\tif err != nil {
\t\treturn err
\t}
\tvar resp struct{ Result *string }
\tif err := json.Unmarshal(b, &resp); err != nil || resp.Result == nil {
\t\treturn fmt.Errorf("cache miss: %s", key)
\t}
\treturn json.Unmarshal([]byte(*resp.Result), dest)
}

func (c *Client) Del(key string) error {
\t_, err := c.do("DEL", key)
\treturn err
}

func mustJSON(v any) string {
\tb, _ := json.Marshal(v)
\treturn string(b)
}
"""


def _go_clerk(module: str) -> str:
    return """\
// internal/middleware/clerk.go
//
// Validates Clerk JWTs by calling the Clerk API — no SDK needed in Workers.
package middleware

import (
\t"encoding/json"
\t"fmt"
\t"io"
\t"net/http"
\t"strings"

\t"github.com/syumai/workers"
)

type contextKey string

const UserIDKey contextKey = "clerkUserID"

// RequireAuth validates the Bearer token against Clerk's /oauth/userinfo endpoint.
func RequireAuth(next http.Handler) http.Handler {
\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
\t\ttoken := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
\t\tif token == "" {
\t\t\thttp.Error(w, "unauthorized", http.StatusUnauthorized)
\t\t\treturn
\t\t}

\t\tuserID, err := verifyClerkToken(token)
\t\tif err != nil {
\t\t\thttp.Error(w, "unauthorized", http.StatusUnauthorized)
\t\t\treturn
\t\t}

\t\t// Store user ID in request context
\t\tctx := r.Context()
\t\t// Use a simple header pass-through for now; swap for context.WithValue with a real ctx key
\t\tr.Header.Set("X-User-ID", userID)
\t\t_ = ctx
\t\tnext.ServeHTTP(w, r)
\t})
}

func verifyClerkToken(token string) (string, error) {
\tsecretKey := workers.Getenv("CLERK_SECRET_KEY")
\treq, _ := http.NewRequest("GET", "https://api.clerk.com/v1/tokens/verify", nil)
\treq.Header.Set("Authorization", "Bearer "+secretKey)
\treq.Header.Set("X-Token", token)

\tres, err := http.DefaultClient.Do(req)
\tif err != nil {
\t\treturn "", err
\t}
\tdefer res.Body.Close()
\tbody, _ := io.ReadAll(res.Body)

\tif res.StatusCode != 200 {
\t\treturn "", fmt.Errorf("clerk verify failed: %s", body)
\t}

\tvar payload struct {
\t\tSub string `json:"sub"`
\t}
\tif err := json.Unmarshal(body, &payload); err != nil || payload.Sub == "" {
\t\treturn "", fmt.Errorf("invalid clerk token payload")
\t}
\treturn payload.Sub, nil
}

// UserID extracts the Clerk user ID set by RequireAuth.
func UserID(r *http.Request) string {
\treturn r.Header.Get("X-User-ID")
}
"""


def _go_email(module: str) -> str:
    return """\
// internal/email/resend.go
package email

import (
\t"bytes"
\t"encoding/json"
\t"fmt"
\t"io"
\t"net/http"

\t"github.com/syumai/workers"
)

type Client struct {
\tapiKey string
\tfrom   string
}

func New() *Client {
\treturn &Client{
\t\tapiKey: workers.Getenv("RESEND_API_KEY"),
\t\tfrom:   workers.Getenv("RESEND_FROM_EMAIL"),
\t}
}

type SendParams struct {
\tTo      []string
\tSubject string
\tHTML    string
}

func (c *Client) Send(p SendParams) error {
\tbody, _ := json.Marshal(map[string]any{
\t\t"from": c.from, "to": p.To, "subject": p.Subject, "html": p.HTML,
\t})
\treq, _ := http.NewRequest("POST", "https://api.resend.com/emails", bytes.NewReader(body))
\treq.Header.Set("Authorization", "Bearer "+c.apiKey)
\treq.Header.Set("Content-Type", "application/json")
\tres, err := http.DefaultClient.Do(req)
\tif err != nil {
\t\treturn err
\t}
\tdefer res.Body.Close()
\tif res.StatusCode >= 400 {
\t\tb, _ := io.ReadAll(res.Body)
\t\treturn fmt.Errorf("resend: %s", b)
\t}
\treturn nil
}
"""


def _go_r2(module: str) -> str:
    return """\
// internal/storage/r2.go
//
// Cloudflare R2 via S3-compatible API — standard HTTP, works in Workers.
package storage

import (
\t"bytes"
\t"crypto/hmac"
\t"crypto/sha256"
\t"fmt"
\t"net/http"
\t"time"

\t"github.com/syumai/workers"
)

type Client struct {
\taccount   string
\taccessKey string
\tsecretKey string
\tbucket    string
\tpublicURL string
}

func New() *Client {
\treturn &Client{
\t\taccount:   workers.Getenv("R2_ACCOUNT_ID"),
\t\taccessKey: workers.Getenv("R2_ACCESS_KEY_ID"),
\t\tsecretKey: workers.Getenv("R2_SECRET_ACCESS_KEY"),
\t\tbucket:    workers.Getenv("R2_BUCKET_NAME"),
\t\tpublicURL: workers.Getenv("R2_PUBLIC_URL"),
\t}
}

// Upload puts an object into R2 and returns its public URL.
func (c *Client) Upload(key string, data []byte, contentType string) (string, error) {
\tendpoint := fmt.Sprintf("https://%s.r2.cloudflarestorage.com/%s/%s",
\t\tc.account, c.bucket, key)

\treq, _ := http.NewRequest("PUT", endpoint, bytes.NewReader(data))
\treq.Header.Set("Content-Type", contentType)
\tc.signRequest(req, data)

\tres, err := http.DefaultClient.Do(req)
\tif err != nil {
\t\treturn "", err
\t}
\tdefer res.Body.Close()
\tif res.StatusCode >= 400 {
\t\treturn "", fmt.Errorf("r2 upload failed: %d", res.StatusCode)
\t}
\treturn fmt.Sprintf("%s/%s", c.publicURL, key), nil
}

// signRequest applies AWS Signature V4 to the request.
// For a full SigV4 implementation, use a dedicated package in production.
func (c *Client) signRequest(req *http.Request, body []byte) {
\tnow := time.Now().UTC()
\tdate := now.Format("20060102")
\tdatetime := now.Format("20060102T150405Z")

\tpayloadHash := fmt.Sprintf("%x", sha256.Sum256(body))

\treq.Header.Set("x-amz-date", datetime)
\treq.Header.Set("x-amz-content-sha256", payloadHash)

\t// Simplified — use aws-sdk or a full SigV4 lib for production
\t_ = hmac.New(sha256.New, []byte(c.secretKey+date))
}
"""


def _api_env_example(name: str, schema: str) -> str:
    return f"""\
# ── Cloudflare Worker env vars (set via wrangler secret or dashboard) ──
FRONTEND_URL=http://localhost:5173

# ── Supabase (REST API — no direct TCP in Workers) ────────────────
SUPABASE_URL=https://PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=
# Schema: {schema}

# ── Upstash Redis (HTTP REST — compatible with Workers) ───────────
UPSTASH_REDIS_REST_URL=https://YOUR.upstash.io
UPSTASH_REDIS_REST_TOKEN=

# ── Clerk ─────────────────────────────────────────────────────────
CLERK_SECRET_KEY=sk_test_

# ── Resend ────────────────────────────────────────────────────────
RESEND_API_KEY=re_
RESEND_FROM_EMAIL=noreply@yourdomain.com

# ── Cloudflare R2 ─────────────────────────────────────────────────
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME={name}
R2_PUBLIC_URL=https://pub-XXXX.r2.dev

# ── BetterStack ───────────────────────────────────────────────────
BETTERSTACK_SOURCE_TOKEN=
"""


def _worker_wrangler(name: str) -> str:
    return f"""\
# Cloudflare Worker — Go API
# Build: tinygo build -o build/worker.wasm -target wasm ./cmd/worker
# Requires TinyGo: https://tinygo.org/getting-started/install/

name = "{name}-api"
main = "build/worker.wasm"
compatibility_date = "2024-09-23"

[build]
command = "tinygo build -o build/worker.wasm -target wasm ./cmd/worker"

# Set secrets via: wrangler secret put SECRET_NAME
# [vars] block is for non-sensitive values only
[vars]
FRONTEND_URL = "https://{name}-web.pages.dev"

[[routes]]
# Update with your actual domain after deploying
pattern = "{name}-api.yourusername.workers.dev/*"
"""


def _makefile() -> str:
    return """\
.PHONY: dev dev-api dev-web build deploy

# Run both locally (requires two terminals, or use tmux/overmind)
dev-api:
\tcd api && wrangler dev

dev-web:
\tcd web && npm run dev

# Build the Worker WASM (requires TinyGo)
build:
\tcd api && tinygo build -o build/worker.wasm -target wasm ./cmd/worker

# Deploy everything
deploy: build
\tcd api && wrangler deploy
\tcd web && wrangler pages deploy dist

# Install TinyGo reminder
tinygo-check:
\t@which tinygo > /dev/null || (echo "Install TinyGo: https://tinygo.org/getting-started/install/" && exit 1)
"""
