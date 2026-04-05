"""Shared file templates (gitignore, README)."""


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

# misc
.DS_Store
*.log
*.tsbuildinfo
.sentry-clack-store
.wrangler/
"""


def readme(ctx: dict, is_nextjs: bool, has_mobile: bool) -> str:
    name = ctx["name"]
    title = ctx["title"]
    schema = ctx["schema"]
    arch = "Next.js → Vercel" if is_nextjs else "Go + React → Cloudflare Workers (API) + Cloudflare Pages (web)"
    env_file = ".env.local" if is_nextjs else ".env"
    run_cmd = "npm install && npm run dev" if is_nextjs else "cd api && go mod tidy\ncd web && npm install && npm run dev"
    deploy_txt = (
        "Push to GitHub → Vercel auto-deploys."
        if is_nextjs else
        "- **API**: `wrangler deploy` from api/\n- **Web**: `wrangler pages deploy ./web/dist`"
    )
    mobile_section = ""
    if has_mobile:
        mobile_section = """
## Mobile
```bash
cd mobile && npm install && npx expo start
```
"""

    return f"""\
# {title}

## Stack
- **Architecture**: {arch}
- **Database**: Supabase (schema: `{schema}`)
- **Cache**: Upstash Redis
- **Auth**: Clerk
- **Email**: Resend
- **Storage**: Cloudflare R2
- **Analytics**: PostHog
- **Errors**: Sentry
- **Uptime/Logs**: BetterStack
{"- **Mobile**: Expo (React Native)" if has_mobile else ""}

## 1. Supabase Schema Setup
Run once in the Supabase SQL editor:
```sql
CREATE SCHEMA {schema};
CREATE ROLE {schema}_app LOGIN PASSWORD 'YOUR_STRONG_PASSWORD';
GRANT USAGE ON SCHEMA {schema} TO {schema}_app;
GRANT ALL ON ALL TABLES IN SCHEMA {schema} TO {schema}_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA {schema}
  GRANT ALL ON TABLES TO {schema}_app;
```

## 2. Environment Variables
```bash
cp .env.example {env_file}
# Fill in all values
```

## 3. Service Checklist
- [ ] Supabase — create schema (SQL above), copy connection string
- [ ] Clerk — create new application, copy publishable + secret key
- [ ] Upstash — create Redis DB, copy REST URL + token
- [ ] Resend — add domain, copy API key
- [ ] Cloudflare R2 — create bucket, copy account ID + credentials
- [ ] PostHog — create project, copy key
- [ ] Sentry — create project, copy DSN
- [ ] BetterStack — create source, copy token

## 4. Run Locally
```bash
{run_cmd}
```
{mobile_section}
## Deploy
{deploy_txt}
"""
