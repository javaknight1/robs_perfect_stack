"""Tests for template content correctness."""

import json
import pytest


class TestNextjsTemplates:
    def test_package_json_valid(self):
        from rob_stack.templates.nextjs import _package_json
        data = json.loads(_package_json("test-app"))
        assert data["name"] == "test-app"
        assert "next" in data["dependencies"]
        assert "@clerk/nextjs" in data["dependencies"]
        assert "@supabase/supabase-js" in data["dependencies"]
        assert "@upstash/redis" in data["dependencies"]
        assert "resend" in data["dependencies"]
        assert "@aws-sdk/client-s3" in data["dependencies"]
        assert "posthog-js" in data["dependencies"]
        assert "@sentry/nextjs" in data["dependencies"]

    def test_env_example_has_all_services(self):
        from rob_stack.templates.nextjs import _env_example
        env = _env_example("test-app", "test_app")
        assert "SUPABASE_URL" in env
        assert "UPSTASH_REDIS_REST_URL" in env
        assert "CLERK_SECRET_KEY" in env
        assert "RESEND_API_KEY" in env
        assert "R2_ACCOUNT_ID" in env
        assert "POSTHOG" in env
        assert "SENTRY_DSN" in env
        assert "BETTERSTACK" in env

    def test_env_local_uses_creds(self):
        from rob_stack.templates.nextjs import _env_local
        creds = {
            "SUPABASE_URL": "http://127.0.0.1:54321",
            "SUPABASE_ANON_KEY": "anon_key_here",
            "SUPABASE_SERVICE_ROLE_KEY": "service_key_here",
            "DATABASE_URL": "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
            "UPSTASH_REDIS_REST_URL": "https://my.upstash.io",
            "CLERK_PUBLISHABLE_KEY": "pk_test_abc",
            "CLERK_SECRET_KEY": "sk_test_xyz",
            "POSTHOG_KEY": "phc_abc",
            "POSTHOG_HOST": "https://us.i.posthog.com",
        }
        env = _env_local("test-app", "test_app", creds)
        assert "http://127.0.0.1:54321" in env
        assert "anon_key_here" in env
        assert "pk_test_abc" in env
        assert "sk_test_xyz" in env
        assert "phc_abc" in env

    def test_env_local_defaults_for_missing(self):
        from rob_stack.templates.nextjs import _env_local
        env = _env_local("test-app", "test_app", {})
        assert "NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in" in env
        assert "R2_BUCKET_NAME=test-app" in env
        assert "NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com" in env

    def test_layout_contains_clerk_provider(self):
        from rob_stack.templates.nextjs import _layout
        layout = _layout("Test App")
        assert "ClerkProvider" in layout
        assert "PostHogProvider" in layout

    def test_middleware_has_public_routes(self):
        from rob_stack.templates.nextjs import _middleware
        mw = _middleware()
        assert "clerkMiddleware" in mw
        assert "/sign-in" in mw
        assert "/sign-up" in mw

    def test_supabase_client_uses_schema(self):
        from rob_stack.templates.nextjs import _lib_supabase
        code = _lib_supabase("my_app")
        assert '"my_app"' in code
        assert "supabaseAdmin" in code
        assert "supabase" in code

    def test_package_json_has_swagger_deps(self):
        from rob_stack.templates.nextjs import _package_json
        data = json.loads(_package_json("test-app"))
        assert "next-swagger-doc" in data["dependencies"]
        assert "swagger-ui-react" in data["dependencies"]
        assert "@types/swagger-ui-react" in data["devDependencies"]

    def test_swagger_config_uses_title(self):
        from rob_stack.templates.nextjs import _swagger_config
        code = _swagger_config("My App")
        assert "createSwaggerSpec" in code
        assert "My App API" in code

    def test_api_doc_page_renders_swagger(self):
        from rob_stack.templates.nextjs import _api_doc_page
        code = _api_doc_page()
        assert "SwaggerUI" in code
        assert '"use client"' in code
        assert "/api/docs" in code

    def test_openapi_route_returns_spec(self):
        from rob_stack.templates.nextjs import _openapi_route
        code = _openapi_route()
        assert "getApiDocs" in code
        assert "NextResponse.json" in code

    def test_health_route_has_swagger_annotation(self):
        from rob_stack.templates.nextjs import _health_route
        code = _health_route()
        assert "@swagger" in code
        assert "/api/health" in code

    def test_middleware_allows_api_docs(self):
        from rob_stack.templates.nextjs import _middleware
        mw = _middleware()
        assert "/api-docs" in mw
        assert "/api/docs" in mw

    def test_makefile_nextjs(self):
        from rob_stack.templates.nextjs import _makefile_nextjs
        mk = _makefile_nextjs()
        assert "dev:" in mk
        assert "build:" in mk
        assert "lint:" in mk
        assert "test:" in mk
        assert "supabase-start:" in mk
        assert "supabase-stop:" in mk
        assert "deploy:" in mk
        assert "setup:" in mk
        assert "supabase start" in mk
        # Should NOT have docker compose
        assert "docker compose" not in mk


class TestCloudflareTemplates:
    def test_go_mod_uses_module(self):
        from rob_stack.templates.cloudflare import _go_mod
        mod = _go_mod("github.com/rob/myapp")
        assert "module github.com/rob/myapp" in mod
        assert "go 1.23" in mod
        assert "syumai/workers" in mod

    def test_web_package_json_valid(self):
        from rob_stack.templates.cloudflare import _web_package_json
        data = json.loads(_web_package_json("test-app"))
        assert data["name"] == "test-app-web"
        assert "react" in data["dependencies"]
        assert "@clerk/clerk-react" in data["dependencies"]
        assert "posthog-js" in data["dependencies"]
        assert "@sentry/react" in data["dependencies"]

    def test_clerk_middleware_uses_context(self):
        from rob_stack.templates.cloudflare import _go_clerk
        code = _go_clerk("github.com/test/app")
        assert "context.WithValue" in code
        assert "UserIDKey" in code
        assert "r.WithContext" in code
        # Should NOT use header-based user ID passing
        assert 'Header.Set("X-User-ID"' not in code

    def test_r2_has_sigv4(self):
        from rob_stack.templates.cloudflare import _go_r2
        code = _go_r2("github.com/test/app")
        assert "AWS4-HMAC-SHA256" in code
        assert "hmacSHA256" in code
        assert "credentialScope" in code

    def test_clerk_uses_jwks(self):
        from rob_stack.templates.cloudflare import _go_clerk
        code = _go_clerk("github.com/test/app")
        assert "JWKS" in code or "jwks" in code
        assert "CLERK_JWKS_URL" in code
        assert "rsa.VerifyPKCS1v15" in code

    def test_api_env_has_clerk_jwks(self):
        from rob_stack.templates.cloudflare import _api_env_example
        env = _api_env_example("test-app", "test_app")
        assert "CLERK_JWKS_URL" in env

    def test_dev_vars_example_exists(self):
        from rob_stack.templates.cloudflare import _dev_vars_example
        content = _dev_vars_example("test-app", "test_app")
        assert ".dev.vars" in content
        assert "SUPABASE_URL" in content

    def test_api_dev_vars_uses_creds(self):
        from rob_stack.templates.cloudflare import _api_dev_vars
        creds = {
            "SUPABASE_URL": "http://127.0.0.1:54321",
            "SUPABASE_SERVICE_ROLE_KEY": "service_key",
            "CLERK_SECRET_KEY": "sk_test_abc",
            "CLERK_JWKS_URL": "https://clerk.jwks",
            "UPSTASH_REDIS_REST_URL": "https://upstash.io",
            "POSTHOG_KEY": "phc_xyz",
        }
        content = _api_dev_vars("test-app", "test_app", creds)
        assert "http://127.0.0.1:54321" in content
        assert "sk_test_abc" in content
        assert "phc_xyz" in content

    def test_web_env_uses_creds(self):
        from rob_stack.templates.cloudflare import _web_env
        creds = {
            "CLERK_PUBLISHABLE_KEY": "pk_test_123",
            "POSTHOG_KEY": "phc_abc",
            "SENTRY_DSN": "https://sentry.dsn",
            "VITE_API_URL": "http://localhost:8787/api",
        }
        content = _web_env(creds)
        assert "pk_test_123" in content
        assert "phc_abc" in content
        assert "https://sentry.dsn" in content

    def test_supabase_uses_postgrest_headers(self):
        from rob_stack.templates.cloudflare import _go_supabase
        code = _go_supabase("github.com/test/app", "my_app")
        assert "Accept-Profile" in code
        assert "Content-Profile" in code
        assert '"my_app"' in code

    def test_go_openapi_spec(self):
        from rob_stack.templates.cloudflare import _go_openapi
        code = _go_openapi("github.com/test/app")
        assert "BuildSpec" in code
        assert "ServeSpec" in code
        assert "ServeSwaggerUI" in code
        assert "/health" in code
        assert "openapi" in code
        assert "3.0.0" in code

    def test_go_main_has_openapi_routes(self):
        from rob_stack.templates.cloudflare import _go_main
        code = _go_main("github.com/test/app", "test_app")
        assert "openapi.ServeSwaggerUI" in code
        assert "openapi.ServeSpec" in code
        assert "/api/docs" in code

    def test_makefile_has_all_targets(self):
        from rob_stack.templates.cloudflare import _makefile
        mk = _makefile()
        assert "dev:" in mk
        assert "dev-api:" in mk
        assert "dev-web:" in mk
        assert "build:" in mk
        assert "deploy:" in mk
        assert "lint:" in mk
        assert "test:" in mk
        assert "supabase-start:" in mk
        assert "supabase-stop:" in mk
        assert "setup:" in mk
        assert "supabase start" in mk
        # Should NOT have docker compose
        assert "docker compose" not in mk


class TestMobileTemplates:
    def test_package_json_valid(self):
        from rob_stack.templates.mobile import _package_json
        data = json.loads(_package_json("test-app"))
        assert data["name"] == "test-app-mobile"
        assert "@clerk/clerk-expo" in data["dependencies"]
        assert "expo" in data["dependencies"]

    def test_sign_in_imports_usestate_from_react(self):
        from rob_stack.templates.mobile import _sign_in
        code = _sign_in()
        # useState must come from "react", not "react-native"
        assert 'import { useState } from "react"' in code
        # Ensure useState is NOT in the react-native import line
        for line in code.splitlines():
            if "react-native" in line and "import" in line:
                assert "useState" not in line


class TestSharedTemplates:
    def test_gitignore_has_dev_vars(self):
        from rob_stack.templates.shared import gitignore
        gi = gitignore()
        assert ".dev.vars" in gi

    def test_supabase_config_has_project_id(self):
        from rob_stack.templates.shared import supabase_config
        ctx = {"name": "test-app", "schema": "test_app"}
        config = supabase_config(ctx)
        assert 'id = "test-app"' in config
        assert "test_app" in config
        assert "54321" in config
        assert "54322" in config
        assert "54323" in config

    def test_supabase_config_has_schema(self):
        from rob_stack.templates.shared import supabase_config
        ctx = {"name": "my-app", "schema": "my_app"}
        config = supabase_config(ctx)
        assert "my_app" in config

    def test_init_db_sql_uses_schema(self):
        from rob_stack.templates.shared import init_db_sql
        sql = init_db_sql("my_app")
        assert "CREATE SCHEMA IF NOT EXISTS my_app" in sql
        assert "my_app_app" in sql

    def test_readme_nextjs(self):
        ctx = {"name": "test-app", "title": "Test App", "schema": "test_app", "description": "A test"}
        from rob_stack.templates.shared import readme
        md = readme(ctx, is_nextjs=True, has_mobile=False)
        assert "Test App" in md
        assert "Vercel" in md
        assert "Supabase" in md
        assert "make dev" in md
        assert "supabase" in md.lower()
        # Should NOT reference docker-compose
        assert "docker compose up" not in md
        assert "docker-compose" not in md

    def test_readme_go_react(self):
        ctx = {"name": "test-app", "title": "Test App", "schema": "test_app", "description": ""}
        from rob_stack.templates.shared import readme
        md = readme(ctx, is_nextjs=False, has_mobile=False)
        assert "Cloudflare" in md
        assert "wrangler" in md
        assert "make dev" in md
        assert "supabase" in md.lower()

    def test_readme_with_mobile(self):
        ctx = {"name": "test-app", "title": "Test App", "schema": "test_app", "description": ""}
        from rob_stack.templates.shared import readme
        md = readme(ctx, is_nextjs=True, has_mobile=True)
        assert "Expo" in md
        assert "mobile" in md.lower()

    def test_readme_has_supabase_cli_prereq(self):
        ctx = {"name": "test-app", "title": "Test App", "schema": "test_app", "description": ""}
        from rob_stack.templates.shared import readme
        md = readme(ctx, is_nextjs=True, has_mobile=False)
        assert "Supabase CLI" in md

    def test_readme_has_supabase_make_targets(self):
        ctx = {"name": "test-app", "title": "Test App", "schema": "test_app", "description": ""}
        from rob_stack.templates.shared import readme
        md = readme(ctx, is_nextjs=True, has_mobile=False)
        assert "supabase-start" in md
        assert "supabase-stop" in md

    def test_readme_nextjs_tree_has_doc_files(self):
        ctx = {"name": "test-app", "title": "Test App", "schema": "test_app", "description": ""}
        from rob_stack.templates.shared import readme
        md = readme(ctx, is_nextjs=True, has_mobile=False)
        assert "CLAUDE.md" in md
        assert "CONTRIBUTING.md" in md
        assert "ARCHITECTURE.md" in md
        assert "DEPLOYMENT.md" in md

    def test_readme_go_tree_has_doc_files(self):
        ctx = {"name": "test-app", "title": "Test App", "schema": "test_app", "description": ""}
        from rob_stack.templates.shared import readme
        md = readme(ctx, is_nextjs=False, has_mobile=False)
        assert "CLAUDE.md" in md
        assert "CONTRIBUTING.md" in md
        assert "ARCHITECTURE.md" in md
        assert "DEPLOYMENT.md" in md


class TestDocsTemplates:
    """Tests for documentation templates (CLAUDE.md, CONTRIBUTING.md, etc.)."""

    CTX = {"name": "test-app", "title": "Test App", "schema": "test_app",
           "description": "A test", "github_user": "testuser"}

    # ── CLAUDE.md ──────────────────────────────────────────────

    def test_claude_md_nextjs_sections(self):
        from rob_stack.templates.docs import claude_md
        md = claude_md(self.CTX, is_nextjs=True, has_mobile=False)
        assert "## Architecture" in md
        assert "## Commands" in md
        assert "## Local Ports" in md
        assert "## Key Files" in md
        assert "## Services" in md
        assert "## Conventions" in md

    def test_claude_md_nextjs_content(self):
        from rob_stack.templates.docs import claude_md
        md = claude_md(self.CTX, is_nextjs=True, has_mobile=False)
        assert "Next.js" in md
        assert "Vercel" in md
        assert "test_app" in md
        assert "make dev" in md
        assert "3000" in md
        assert ".env.local" in md

    def test_claude_md_go_content(self):
        from rob_stack.templates.docs import claude_md
        md = claude_md(self.CTX, is_nextjs=False, has_mobile=False)
        assert "Cloudflare Workers" in md
        assert "TinyGo" in md
        assert "5173" in md
        assert "8787" in md
        assert "api/.dev.vars" in md
        assert "api/cmd/worker/main.go" in md

    def test_claude_md_mobile_section(self):
        from rob_stack.templates.docs import claude_md
        md = claude_md(self.CTX, is_nextjs=True, has_mobile=True)
        assert "## Mobile (Expo)" in md
        assert "mobile/lib/api.ts" in md

    def test_claude_md_no_mobile_section(self):
        from rob_stack.templates.docs import claude_md
        md = claude_md(self.CTX, is_nextjs=True, has_mobile=False)
        assert "## Mobile" not in md

    # ── CONTRIBUTING.md ────────────────────────────────────────

    def test_contributing_md_sections(self):
        from rob_stack.templates.docs import contributing_md
        md = contributing_md(self.CTX, is_nextjs=True, has_mobile=False)
        assert "## Getting Started" in md
        assert "## Branch Workflow" in md
        assert "## Code Standards" in md
        assert "## Adding API Endpoints" in md
        assert "## Database Changes" in md
        assert "## Commit Messages" in md
        assert "## CI Pipeline" in md

    def test_contributing_md_nextjs_standards(self):
        from rob_stack.templates.docs import contributing_md
        md = contributing_md(self.CTX, is_nextjs=True, has_mobile=False)
        assert "ESLint" in md
        assert "TypeScript" in md

    def test_contributing_md_go_standards(self):
        from rob_stack.templates.docs import contributing_md
        md = contributing_md(self.CTX, is_nextjs=False, has_mobile=False)
        assert "go vet" in md
        assert "gofmt" in md

    def test_contributing_md_mobile_section(self):
        from rob_stack.templates.docs import contributing_md
        md = contributing_md(self.CTX, is_nextjs=True, has_mobile=True)
        assert "## Mobile Development" in md

    # ── ARCHITECTURE.md ────────────────────────────────────────

    def test_architecture_md_sections(self):
        from rob_stack.templates.docs import architecture_md
        md = architecture_md(self.CTX, is_nextjs=True, has_mobile=False)
        assert "## Tech Stack" in md
        assert "## Request Flow" in md
        assert "## Data Flow" in md
        assert "## Database Schema Isolation" in md
        assert "## Deployment Topology" in md
        assert "## Key Design Decisions" in md

    def test_architecture_md_nextjs_content(self):
        from rob_stack.templates.docs import architecture_md
        md = architecture_md(self.CTX, is_nextjs=True, has_mobile=False)
        assert "Next.js" in md
        assert "Vercel" in md
        assert "test_app" in md

    def test_architecture_md_go_content(self):
        from rob_stack.templates.docs import architecture_md
        md = architecture_md(self.CTX, is_nextjs=False, has_mobile=False)
        assert "Cloudflare Workers" in md
        assert "TinyGo" in md
        assert "WASM" in md

    def test_architecture_md_schema_isolation(self):
        from rob_stack.templates.docs import architecture_md
        md = architecture_md(self.CTX, is_nextjs=True, has_mobile=False)
        assert "test_app" in md
        assert "CREATE SCHEMA" in md
        assert "test_app_app" in md

    def test_architecture_md_mobile_section(self):
        from rob_stack.templates.docs import architecture_md
        md = architecture_md(self.CTX, is_nextjs=True, has_mobile=True)
        assert "## Mobile Architecture" in md
        assert "@clerk/clerk-expo" in md

    # ── DEPLOYMENT.md ──────────────────────────────────────────

    def test_deployment_md_sections(self):
        from rob_stack.templates.docs import deployment_md
        md = deployment_md(self.CTX, is_nextjs=True, has_mobile=False)
        assert "## Environment Variables" in md
        assert "## Database (Production)" in md
        assert "## GitHub Actions Secrets" in md
        assert "## Verification Checklist" in md

    def test_deployment_md_nextjs_env_vars(self):
        from rob_stack.templates.docs import deployment_md
        md = deployment_md(self.CTX, is_nextjs=True, has_mobile=False)
        assert "NEXT_PUBLIC_SUPABASE_URL" in md
        assert "CLERK_SECRET_KEY" in md
        assert "VERCEL_TOKEN" in md
        assert "Deploy to Vercel" in md

    def test_deployment_md_go_env_vars(self):
        from rob_stack.templates.docs import deployment_md
        md = deployment_md(self.CTX, is_nextjs=False, has_mobile=False)
        assert "SUPABASE_URL" in md
        assert "CLERK_JWKS_URL" in md
        assert "CLOUDFLARE_API_TOKEN" in md
        assert "wrangler deploy" in md

    def test_deployment_md_db_setup(self):
        from rob_stack.templates.docs import deployment_md
        md = deployment_md(self.CTX, is_nextjs=True, has_mobile=False)
        assert "CREATE SCHEMA test_app" in md
        assert "test_app_app" in md

    def test_deployment_md_mobile_section(self):
        from rob_stack.templates.docs import deployment_md
        md = deployment_md(self.CTX, is_nextjs=True, has_mobile=True)
        assert "## Mobile Deployment" in md
        assert "eas build" in md
