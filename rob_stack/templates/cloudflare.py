"""Go + React → Cloudflare Workers (API) + Cloudflare Pages (web)."""

import json


def generate_go_cloudflare(root, ctx: dict, write) -> None:
    name   = ctx["name"]
    title  = ctx["title"]
    schema = ctx["schema"]
    github_user = ctx.get("github_user", "yourusername")
    module = f"github.com/{github_user}/{name}"

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
    write(root, "api/internal/analytics/posthog.go", _go_posthog(module))
    write(root, "api/internal/logger/betterstack.go", _go_betterstack(module))
    write(root, "api/.env.example",                  _api_env_example(name, schema))
    write(root, "api/.dev.vars.example",             _dev_vars_example(name, schema))
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
\t"strings"

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
\t\tAllowedOrigins: strings.Split(workers.Getenv("ALLOWED_ORIGINS"), ","),
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
\t"net/url"
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
\t}
}

func (c *Client) do(args ...string) ([]byte, error) {
\t// Build path-based URL: e.g. SET/key/value/EX/3600
\tparts := make([]string, len(args))
\tfor i, a := range args {
\t\tparts[i] = url.PathEscape(a)
\t}
\treqURL := c.url + "/" + strings.Join(parts, "/")
\treq, _ := http.NewRequest("GET", reqURL, nil)
\treq.Header.Set("Authorization", "Bearer "+c.token)
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

"""


def _go_clerk(module: str) -> str:
    return """\
// internal/middleware/clerk.go
//
// Validates Clerk JWTs by fetching JWKS and verifying locally.
// No external JWT library needed — uses stdlib crypto/rsa.
package middleware

import (
\t"context"
\t"crypto"
\t"crypto/rsa"
\t"crypto/sha256"
\t"encoding/base64"
\t"encoding/json"
\t"fmt"
\t"io"
\t"math/big"
\t"net/http"
\t"strings"
\t"sync"
\t"time"

\t"github.com/syumai/workers"
)

type contextKey string

const UserIDKey contextKey = "clerkUserID"

// jwksCache caches the JWKS keys fetched from Clerk with a TTL.
var jwksCache struct {
\tkeys      map[string]*rsa.PublicKey
\tmu        sync.RWMutex
\tlastFetch time.Time
}

const jwksTTL = 6 * time.Hour

// RequireAuth validates the Bearer JWT against Clerk's JWKS.
func RequireAuth(next http.Handler) http.Handler {
\treturn http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
\t\ttoken := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
\t\tif token == "" {
\t\t\thttp.Error(w, "unauthorized", http.StatusUnauthorized)
\t\t\treturn
\t\t}

\t\tuserID, err := verifyClerkJWT(token)
\t\tif err != nil {
\t\t\thttp.Error(w, "unauthorized", http.StatusUnauthorized)
\t\t\treturn
\t\t}

\t\tctx := context.WithValue(r.Context(), UserIDKey, userID)
\t\tnext.ServeHTTP(w, r.WithContext(ctx))
\t})
}

// verifyClerkJWT decodes the JWT, fetches Clerk's JWKS, and verifies the signature.
func verifyClerkJWT(token string) (string, error) {
\tparts := strings.Split(token, ".")
\tif len(parts) != 3 {
\t\treturn "", fmt.Errorf("invalid JWT format")
\t}

\t// Decode header to get key ID
\theaderBytes, err := base64URLDecode(parts[0])
\tif err != nil {
\t\treturn "", fmt.Errorf("decode header: %w", err)
\t}
\tvar header struct {
\t\tKid string `json:"kid"`
\t\tAlg string `json:"alg"`
\t}
\tif err := json.Unmarshal(headerBytes, &header); err != nil {
\t\treturn "", fmt.Errorf("parse header: %w", err)
\t}

\t// Decode payload
\tpayloadBytes, err := base64URLDecode(parts[1])
\tif err != nil {
\t\treturn "", fmt.Errorf("decode payload: %w", err)
\t}
\tvar claims struct {
\t\tSub string `json:"sub"`
\t\tExp int64  `json:"exp"`
\t\tNbf int64  `json:"nbf"`
\t}
\tif err := json.Unmarshal(payloadBytes, &claims); err != nil {
\t\treturn "", fmt.Errorf("parse claims: %w", err)
\t}

\t// Check expiry
\tnow := time.Now().Unix()
\tif claims.Exp > 0 && now > claims.Exp {
\t\treturn "", fmt.Errorf("token expired")
\t}
\tif claims.Nbf > 0 && now < claims.Nbf {
\t\treturn "", fmt.Errorf("token not yet valid")
\t}
\tif claims.Sub == "" {
\t\treturn "", fmt.Errorf("missing sub claim")
\t}

\t// Fetch and cache JWKS
\tkeys, err := getJWKS()
\tif err != nil {
\t\treturn "", fmt.Errorf("fetch JWKS: %w", err)
\t}

\tpubKey, ok := keys[header.Kid]
\tif !ok {
\t\treturn "", fmt.Errorf("unknown key ID: %s", header.Kid)
\t}

\t// Verify RSA signature
\tsigned := []byte(parts[0] + "." + parts[1])
\tsigBytes, err := base64URLDecode(parts[2])
\tif err != nil {
\t\treturn "", fmt.Errorf("decode signature: %w", err)
\t}

\thash := sha256.Sum256(signed)
\tif err := rsa.VerifyPKCS1v15(pubKey, crypto.SHA256, hash[:], sigBytes); err != nil {
\t\treturn "", fmt.Errorf("invalid signature: %w", err)
\t}

\treturn claims.Sub, nil
}

func getJWKS() (map[string]*rsa.PublicKey, error) {
\tjwksCache.mu.RLock()
\tif jwksCache.keys != nil && time.Since(jwksCache.lastFetch) < jwksTTL {
\t\tdefer jwksCache.mu.RUnlock()
\t\treturn jwksCache.keys, nil
\t}
\tjwksCache.mu.RUnlock()

\tjwksCache.mu.Lock()
\tdefer jwksCache.mu.Unlock()

\t// Double-check after acquiring write lock
\tif jwksCache.keys != nil && time.Since(jwksCache.lastFetch) < jwksTTL {
\t\treturn jwksCache.keys, nil
\t}

\tjwksURL := workers.Getenv("CLERK_JWKS_URL")
\tres, err := http.Get(jwksURL)
\tif err != nil {
\t\treturn nil, err
\t}
\tdefer res.Body.Close()
\tbody, _ := io.ReadAll(res.Body)

\tvar jwks struct {
\t\tKeys []struct {
\t\t\tKid string `json:"kid"`
\t\t\tN   string `json:"n"`
\t\t\tE   string `json:"e"`
\t\t} `json:"keys"`
\t}
\tif err := json.Unmarshal(body, &jwks); err != nil {
\t\treturn nil, err
\t}

\tkeys := make(map[string]*rsa.PublicKey, len(jwks.Keys))
\tfor _, k := range jwks.Keys {
\t\tnBytes, _ := base64URLDecode(k.N)
\t\teBytes, _ := base64URLDecode(k.E)
\t\te := 0
\t\tfor _, b := range eBytes {
\t\t\te = e<<8 + int(b)
\t\t}
\t\tkeys[k.Kid] = &rsa.PublicKey{
\t\t\tN: new(big.Int).SetBytes(nBytes),
\t\t\tE: e,
\t\t}
\t}

\tjwksCache.keys = keys
\tjwksCache.lastFetch = time.Now()
\treturn jwksCache.keys, nil
}

func base64URLDecode(s string) ([]byte, error) {
\t// Add padding if needed
\tswitch len(s) % 4 {
\tcase 2:
\t\ts += "=="
\tcase 3:
\t\ts += "="
\t}
\treturn base64.URLEncoding.DecodeString(s)
}

// UserID extracts the Clerk user ID set by RequireAuth.
func UserID(r *http.Request) string {
\tif v, ok := r.Context().Value(UserIDKey).(string); ok {
\t\treturn v
\t}
\treturn ""
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
// Cloudflare R2 via S3-compatible API with AWS Signature V4.
package storage

import (
\t"bytes"
\t"crypto/hmac"
\t"crypto/sha256"
\t"fmt"
\t"net/http"
\t"sort"
\t"strings"
\t"time"

\t"github.com/syumai/workers"
)

const (
\tregion  = "auto"
\tservice = "s3"
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
func (c *Client) signRequest(req *http.Request, body []byte) {
\tnow := time.Now().UTC()
\tdate := now.Format("20060102")
\tdatetime := now.Format("20060102T150405Z")

\tpayloadHash := fmt.Sprintf("%x", sha256.Sum256(body))
\treq.Header.Set("x-amz-date", datetime)
\treq.Header.Set("x-amz-content-sha256", payloadHash)
\treq.Header.Set("Host", req.URL.Host)

\t// Canonical request
\tsignedHeaders, canonicalHeaders := buildCanonicalHeaders(req)
\tcanonicalURI := req.URL.Path
\tif canonicalURI == "" {
\t\tcanonicalURI = "/"
\t}
\tcanonicalQuery := req.URL.Query().Encode()

\tcanonicalRequest := strings.Join([]string{
\t\treq.Method,
\t\tcanonicalURI,
\t\tcanonicalQuery,
\t\tcanonicalHeaders,
\t\tsignedHeaders,
\t\tpayloadHash,
\t}, "\\n")

\t// String to sign
\tcredentialScope := fmt.Sprintf("%s/%s/%s/aws4_request", date, region, service)
\tcanonicalHash := fmt.Sprintf("%x", sha256.Sum256([]byte(canonicalRequest)))
\tstringToSign := fmt.Sprintf("AWS4-HMAC-SHA256\\n%s\\n%s\\n%s",
\t\tdatetime, credentialScope, canonicalHash)

\t// Signing key
\tkDate := hmacSHA256([]byte("AWS4"+c.secretKey), []byte(date))
\tkRegion := hmacSHA256(kDate, []byte(region))
\tkService := hmacSHA256(kRegion, []byte(service))
\tkSigning := hmacSHA256(kService, []byte("aws4_request"))

\tsignature := fmt.Sprintf("%x", hmacSHA256(kSigning, []byte(stringToSign)))

\treq.Header.Set("Authorization", fmt.Sprintf(
\t\t"AWS4-HMAC-SHA256 Credential=%s/%s, SignedHeaders=%s, Signature=%s",
\t\tc.accessKey, credentialScope, signedHeaders, signature))
}

func buildCanonicalHeaders(req *http.Request) (string, string) {
\theaders := make(map[string]string)
\tfor key := range req.Header {
\t\tlk := strings.ToLower(key)
\t\tif lk == "host" || lk == "content-type" || strings.HasPrefix(lk, "x-amz-") {
\t\t\theaders[lk] = strings.TrimSpace(req.Header.Get(key))
\t\t}
\t}
\tkeys := make([]string, 0, len(headers))
\tfor k := range headers {
\t\tkeys = append(keys, k)
\t}
\tsort.Strings(keys)

\tvar canonical, signed []string
\tfor _, k := range keys {
\t\tcanonical = append(canonical, k+":"+headers[k])
\t\tsigned = append(signed, k)
\t}
\treturn strings.Join(signed, ";"), strings.Join(canonical, "\\n") + "\\n"
}

func hmacSHA256(key, data []byte) []byte {
\th := hmac.New(sha256.New, key)
\th.Write(data)
\treturn h.Sum(nil)
}
"""


def _go_posthog(module: str) -> str:
    return """\
// internal/analytics/posthog.go
package analytics

import (
\t"bytes"
\t"encoding/json"
\t"net/http"

\t"github.com/syumai/workers"
)

type Client struct {
\tapiKey string
\thost   string
}

func New() *Client {
\thost := workers.Getenv("POSTHOG_HOST")
\tif host == "" {
\t\thost = "https://us.i.posthog.com"
\t}
\treturn &Client{
\t\tapiKey: workers.Getenv("POSTHOG_KEY"),
\t\thost:   host,
\t}
}

// Capture sends an event to PostHog.
func (c *Client) Capture(distinctID, event string, properties map[string]any) error {
\tpayload, _ := json.Marshal(map[string]any{
\t\t"api_key":     c.apiKey,
\t\t"distinct_id": distinctID,
\t\t"event":       event,
\t\t"properties":  properties,
\t})
\treq, _ := http.NewRequest("POST", c.host+"/capture/", bytes.NewReader(payload))
\treq.Header.Set("Content-Type", "application/json")
\tres, err := http.DefaultClient.Do(req)
\tif err != nil {
\t\treturn err
\t}
\tdefer res.Body.Close()
\treturn nil
}
"""


def _go_betterstack(module: str) -> str:
    return """\
// internal/logger/betterstack.go
package logger

import (
\t"bytes"
\t"encoding/json"
\t"net/http"

\t"github.com/syumai/workers"
)

type Client struct {
\tsourceToken string
\thttpClient  *http.Client
}

func New() *Client {
\treturn &Client{
\t\tsourceToken: workers.Getenv("BETTERSTACK_SOURCE_TOKEN"),
\t\thttpClient:  &http.Client{},
\t}
}

// Log sends a structured log entry to BetterStack.
func (c *Client) Log(level, message string, fields map[string]any) error {
\tpayload := map[string]any{
\t\t"level":   level,
\t\t"message": message,
\t}
\tfor k, v := range fields {
\t\tpayload[k] = v
\t}
\tbody, _ := json.Marshal(payload)
\treq, _ := http.NewRequest("POST", "https://in.logs.betterstack.com", bytes.NewReader(body))
\treq.Header.Set("Content-Type", "application/json")
\treq.Header.Set("Authorization", "Bearer "+c.sourceToken)
\tres, err := c.httpClient.Do(req)
\tif err != nil {
\t\treturn err
\t}
\tdefer res.Body.Close()
\treturn nil
}

// Info logs at info level.
func (c *Client) Info(msg string, fields ...map[string]any) {
\tf := map[string]any{}
\tif len(fields) > 0 {
\t\tf = fields[0]
\t}
\tc.Log("info", msg, f)
}

// Error logs at error level.
func (c *Client) Error(msg string, fields ...map[string]any) {
\tf := map[string]any{}
\tif len(fields) > 0 {
\t\tf = fields[0]
\t}
\tc.Log("error", msg, f)
}
"""


def _api_env_example(name: str, schema: str) -> str:
    return f"""\
# ── Cloudflare Worker env vars (set via wrangler secret or dashboard) ──
ALLOWED_ORIGINS=http://localhost:5173

# ── Supabase (REST API — no direct TCP in Workers) ────────────────
SUPABASE_URL=https://PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=
# Schema: {schema}

# ── Upstash Redis (HTTP REST — compatible with Workers) ───────────
UPSTASH_REDIS_REST_URL=https://YOUR.upstash.io
UPSTASH_REDIS_REST_TOKEN=

# ── Clerk ─────────────────────────────────────────────────────────
CLERK_SECRET_KEY=sk_test_
CLERK_JWKS_URL=https://YOUR_CLERK_DOMAIN.clerk.accounts.dev/.well-known/jwks.json

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


def _dev_vars_example(name: str, schema: str) -> str:
    return f"""\
# .dev.vars — local secrets for wrangler dev (NOT committed to git)
# Copy to api/.dev.vars and fill in values
ALLOWED_ORIGINS=http://localhost:5173
SUPABASE_URL=https://PROJECT.supabase.co  # Replace with your Supabase project URL (REST API, not direct Postgres)
SUPABASE_SERVICE_ROLE_KEY=
CLERK_SECRET_KEY=sk_test_
CLERK_JWKS_URL=https://YOUR_CLERK_DOMAIN.clerk.accounts.dev/.well-known/jwks.json
RESEND_API_KEY=re_
RESEND_FROM_EMAIL=noreply@yourdomain.com
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME={name}
R2_PUBLIC_URL=https://pub-XXXX.r2.dev
UPSTASH_REDIS_REST_URL=http://localhost:6379
UPSTASH_REDIS_REST_TOKEN=
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
ALLOWED_ORIGINS = "https://{name}-web.pages.dev"

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
