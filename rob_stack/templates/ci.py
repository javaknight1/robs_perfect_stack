"""CI/CD and development workflow templates."""


def github_ci_nextjs() -> str:
    return """\
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  lint-and-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npx tsc --noEmit
      - run: npm audit --audit-level=high
"""


def github_ci_go() -> str:
    return """\
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  lint-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: web/package-lock.json
      - run: cd web && npm ci
      - run: cd web && npx tsc --noEmit
      - run: cd web && npm audit --audit-level=high

  build-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: "1.23"
      - uses: acifani/setup-tinygo@v2
        with:
          tinygo-version: "0.32.0"
      - run: cd api && go mod tidy && go vet ./...
      - run: cd api && tinygo build -o /dev/null -target wasm ./cmd/worker
      - name: Check for Go vulnerabilities
        run: |
          go install golang.org/x/vuln/cmd/govulncheck@latest
          cd api && govulncheck ./...
"""


def github_deploy_nextjs() -> str:
    return """\
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run build
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: --prod
"""


def github_deploy_go() -> str:
    return """\
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: "1.23"
      - uses: acifani/setup-tinygo@v2
        with:
          tinygo-version: "0.32.0"
      - run: cd api && tinygo build -o build/worker.wasm -target wasm ./cmd/worker
      - uses: cloudflare/wrangler-action@v3
        with:
          workingDirectory: api
          apiToken: ${{ secrets.CF_API_TOKEN }}

  deploy-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: web/package-lock.json
      - run: cd web && npm ci && npm run build
      - uses: cloudflare/wrangler-action@v3
        with:
          workingDirectory: web
          apiToken: ${{ secrets.CF_API_TOKEN }}
          command: pages deploy dist
"""


def concurrent_dev_package_json(name: str) -> str:
    """Root package.json for Go+React projects with concurrent dev script."""
    import json
    return json.dumps({
        "name": name,
        "private": True,
        "scripts": {
            "dev": "concurrently --names api,web --prefix-colors blue,green \"cd api && wrangler dev\" \"cd web && npm run dev\"",
            "dev:api": "cd api && wrangler dev",
            "dev:web": "cd web && npm run dev",
        },
        "devDependencies": {
            "concurrently": "^9",
        },
    }, indent=2)
