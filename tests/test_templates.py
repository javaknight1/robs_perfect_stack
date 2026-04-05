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

    def test_supabase_uses_postgrest_headers(self):
        from rob_stack.templates.cloudflare import _go_supabase
        code = _go_supabase("github.com/test/app", "my_app")
        assert "Accept-Profile" in code
        assert "Content-Profile" in code
        assert '"my_app"' in code


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

    def test_docker_compose_has_all_services(self):
        from rob_stack.templates.shared import docker_compose
        dc = docker_compose({"name": "test", "schema": "test"}, True)
        assert "postgres" in dc
        assert "redis" in dc
        assert "mailpit" in dc

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

    def test_readme_go_react(self):
        ctx = {"name": "test-app", "title": "Test App", "schema": "test_app", "description": ""}
        from rob_stack.templates.shared import readme
        md = readme(ctx, is_nextjs=False, has_mobile=False)
        assert "Cloudflare" in md
        assert "wrangler" in md

    def test_readme_with_mobile(self):
        ctx = {"name": "test-app", "title": "Test App", "schema": "test_app", "description": ""}
        from rob_stack.templates.shared import readme
        md = readme(ctx, is_nextjs=True, has_mobile=True)
        assert "Expo" in md
        assert "mobile" in md.lower()
