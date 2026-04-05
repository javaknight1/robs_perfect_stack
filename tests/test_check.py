"""Tests for the conformance checker (rob_stack/check.py)."""

import pytest
from rob_stack.check import (
    CheckReport,
    ServiceResult,
    check_betterstack,
    check_clerk,
    check_hosting,
    check_mobile,
    check_posthog,
    check_r2,
    check_redis,
    check_resend,
    check_schema_isolation,
    check_sentry,
    check_supabase,
    detect_arch,
    render_json,
    render_migration_prompt,
    render_report,
)


# ── Architecture detection ────────────────────────────────────────


class TestDetectArch:
    def test_nextjs_detected(self, tmp_path):
        assert detect_arch(tmp_path, {"next", "react"}, "") == "nextjs"

    def test_go_react_with_web_dir(self, tmp_path):
        (tmp_path / "web").mkdir()
        assert detect_arch(tmp_path, {"react"}, "module example.com/foo") == "go_react"

    def test_go_only(self, tmp_path):
        assert detect_arch(tmp_path, set(), "module example.com/foo") == "go_react"

    def test_vite_react_without_go(self, tmp_path):
        assert detect_arch(tmp_path, {"vite", "react"}, "") == "go_react"

    def test_unknown(self, tmp_path):
        assert detect_arch(tmp_path, set(), "") == "unknown"


# ── Supabase ──────────────────────────────────────────────────────


class TestCheckSupabase:
    def test_pass_js(self):
        r = check_supabase({"@supabase/supabase-js"}, "", "")
        assert r.status == "pass"

    def test_pass_go_pgx(self):
        r = check_supabase(set(), "jackc/pgx", "")
        assert r.status == "pass"

    def test_pass_go_rest(self):
        r = check_supabase(set(), "module foo", "SUPABASE_URL=x", "supabase.co")
        assert r.status == "pass"

    def test_warn_env_only(self):
        r = check_supabase(set(), "", "DATABASE_URL=postgres://")
        assert r.status == "warn"

    def test_fail_nothing(self):
        r = check_supabase(set(), "", "")
        assert r.status == "fail"


# ── Schema isolation ──────────────────────────────────────────────


class TestCheckSchemaIsolation:
    def test_pass_search_path_env(self):
        r = check_schema_isolation("?search_path=my_app", "")
        assert r.status == "pass"

    def test_pass_accept_profile(self):
        r = check_schema_isolation("", 'req.Header.Set("Accept-Profile", schema)')
        assert r.status == "pass"

    def test_warn_no_isolation(self):
        r = check_schema_isolation("", "")
        assert r.status == "warn"


# ── Redis ─────────────────────────────────────────────────────────


class TestCheckRedis:
    def test_pass_upstash(self):
        r = check_redis({"@upstash/redis"}, "", "")
        assert r.status == "pass"

    def test_pass_go_rest(self):
        r = check_redis(set(), "module foo", "UPSTASH_REDIS_REST_URL=x", "upstash rest")
        assert r.status == "pass"

    def test_fail_ioredis(self):
        r = check_redis({"ioredis"}, "", "")
        assert r.status == "fail"
        assert r.alternative is not None
        assert "ioredis" in r.alternative

    def test_warn_env_only(self):
        r = check_redis(set(), "", "UPSTASH_REDIS_REST_URL=x")
        assert r.status == "warn"

    def test_fail_nothing(self):
        r = check_redis(set(), "", "")
        assert r.status == "fail"


# ── Clerk ─────────────────────────────────────────────────────────


class TestCheckClerk:
    def test_pass_nextjs(self):
        r = check_clerk({"@clerk/nextjs"}, "", "")
        assert r.status == "pass"

    def test_pass_react(self):
        r = check_clerk({"@clerk/clerk-react"}, "", "")
        assert r.status == "pass"

    def test_fail_next_auth(self):
        r = check_clerk({"next-auth"}, "", "")
        assert r.status == "fail"
        assert r.alternative is not None

    def test_warn_env_only(self):
        r = check_clerk(set(), "", "CLERK_SECRET_KEY=sk_test_")
        assert r.status == "warn"

    def test_fail_nothing(self):
        r = check_clerk(set(), "", "")
        assert r.status == "fail"


# ── Resend ────────────────────────────────────────────────────────


class TestCheckResend:
    def test_pass_js(self):
        r = check_resend({"resend"}, "", "", "")
        assert r.status == "pass"

    def test_pass_go_source(self):
        r = check_resend(set(), "module foo", "", "resend.com/emails")
        assert r.status == "pass"

    def test_fail_nodemailer(self):
        r = check_resend({"nodemailer"}, "", "", "")
        assert r.status == "fail"
        assert "nodemailer" in r.alternative

    def test_warn_env_only(self):
        r = check_resend(set(), "", "RESEND_API_KEY=re_", "")
        assert r.status == "warn"

    def test_fail_nothing(self):
        r = check_resend(set(), "", "", "")
        assert r.status == "fail"


# ── R2 ────────────────────────────────────────────────────────────


class TestCheckR2:
    def test_pass_sdk_plus_env(self):
        r = check_r2({"@aws-sdk/client-s3"}, "", "R2_ACCOUNT_ID=abc")
        assert r.status == "pass"

    def test_pass_go_rest(self):
        r = check_r2(set(), "module foo", "R2_ACCOUNT_ID=abc", "r2.cloudflarestorage.com")
        assert r.status == "pass"

    def test_warn_sdk_no_r2_env(self):
        r = check_r2({"@aws-sdk/client-s3"}, "", "")
        assert r.status == "warn"

    def test_fail_vercel_blob(self):
        r = check_r2({"@vercel/blob"}, "", "")
        assert r.status == "fail"
        assert r.alternative is not None

    def test_fail_nothing(self):
        r = check_r2(set(), "", "")
        assert r.status == "fail"


# ── PostHog ───────────────────────────────────────────────────────


class TestCheckPosthog:
    def test_pass(self):
        r = check_posthog({"posthog-js"}, "", "")
        assert r.status == "pass"

    def test_pass_with_init(self):
        r = check_posthog({"posthog-js"}, "", "posthog.init('phk_123')")
        assert r.status == "pass"

    def test_warn_no_init(self):
        r = check_posthog({"posthog-js"}, "", "import posthog from 'posthog-js'")
        assert r.status == "warn"
        assert "initialization not found" in r.message

    def test_fail_mixpanel(self):
        r = check_posthog({"mixpanel"}, "", "")
        assert r.status == "fail"
        assert r.alternative is not None

    def test_warn_env_only(self):
        r = check_posthog(set(), "NEXT_PUBLIC_POSTHOG_KEY=phc_", "")
        assert r.status == "warn"

    def test_fail_nothing(self):
        r = check_posthog(set(), "", "")
        assert r.status == "fail"


# ── Sentry ────────────────────────────────────────────────────────


class TestCheckSentry:
    def test_pass(self):
        r = check_sentry({"@sentry/nextjs"}, "", "")
        assert r.status == "pass"

    def test_pass_with_init(self):
        r = check_sentry({"@sentry/nextjs"}, "", "Sentry.init({ dsn: '...' })")
        assert r.status == "pass"

    def test_warn_no_init(self):
        r = check_sentry({"@sentry/nextjs"}, "", "import * as Sentry from '@sentry/nextjs'")
        assert r.status == "warn"
        assert "Sentry.init()" in r.message

    def test_fail_bugsnag(self):
        r = check_sentry({"@bugsnag/js"}, "", "")
        assert r.status == "fail"

    def test_warn_env_only(self):
        r = check_sentry(set(), "SENTRY_DSN=https://", "")
        assert r.status == "warn"

    def test_fail_nothing(self):
        r = check_sentry(set(), "", "")
        assert r.status == "fail"


# ── BetterStack ───────────────────────────────────────────────────


class TestCheckBetterStack:
    def test_pass(self):
        r = check_betterstack("BETTERSTACK_SOURCE_TOKEN=abc")
        assert r.status == "pass"

    def test_warn_datadog(self):
        r = check_betterstack("DATADOG_API_KEY=abc")
        assert r.status == "warn"

    def test_fail_nothing(self):
        r = check_betterstack("")
        assert r.status == "fail"


# ── Hosting ───────────────────────────────────────────────────────


class TestCheckHosting:
    def test_nextjs_vercel_pass(self, tmp_path):
        (tmp_path / "vercel.json").write_text("{}")
        results = check_hosting(tmp_path, "nextjs")
        assert any(r.status == "pass" and "Vercel" in r.name for r in results)

    def test_nextjs_no_vercel(self, tmp_path):
        results = check_hosting(tmp_path, "nextjs")
        assert any(r.status == "fail" for r in results)

    def test_go_react_wrangler_pass(self, tmp_path):
        (tmp_path / "wrangler.toml").write_text("")
        results = check_hosting(tmp_path, "go_react")
        assert any(r.status == "pass" and "Cloudflare" in r.name for r in results)

    def test_go_react_with_vercel_warns(self, tmp_path):
        (tmp_path / "wrangler.toml").write_text("")
        (tmp_path / "vercel.json").write_text("{}")
        results = check_hosting(tmp_path, "go_react")
        assert any(r.status == "warn" and "Vercel" in r.message for r in results)


# ── Mobile ────────────────────────────────────────────────────────


class TestCheckMobile:
    def test_pass_with_clerk_expo(self, tmp_path):
        (tmp_path / "mobile").mkdir()
        r = check_mobile(tmp_path, {"@clerk/clerk-expo"})
        assert r.status == "pass"

    def test_warn_no_clerk_expo(self, tmp_path):
        (tmp_path / "mobile").mkdir()
        r = check_mobile(tmp_path, set())
        assert r.status == "warn"

    def test_na_no_mobile_dir(self, tmp_path):
        r = check_mobile(tmp_path, set())
        assert r.status == "na"


# ── Report rendering ──────────────────────────────────────────────


class TestRenderReport:
    def test_output_contains_score(self):
        report = CheckReport(
            path="/test",
            arch="nextjs",
            services=[ServiceResult("Clerk", "pass", "detected")],
            hosting=[ServiceResult("Hosting (Vercel)", "pass", "vercel.json")],
        )
        output = render_report(report)
        assert "Conformance score: 2/2" in output
        assert "100%" in output

    def test_output_contains_alternative(self):
        report = CheckReport(
            path="/test",
            arch="nextjs",
            services=[ServiceResult("Redis", "fail", "wrong", alternative="Use @upstash/redis")],
        )
        output = render_report(report)
        assert "Use @upstash/redis" in output


class TestRenderMigrationPrompt:
    def test_no_prompt_when_all_pass(self):
        report = CheckReport(
            path="/test",
            arch="nextjs",
            services=[ServiceResult("Clerk", "pass", "ok")],
            hosting=[ServiceResult("Hosting", "pass", "ok")],
        )
        assert render_migration_prompt(report) == ""

    def test_prompt_generated_for_failures(self):
        report = CheckReport(
            path="/test",
            arch="nextjs",
            services=[ServiceResult("Clerk", "fail", "not detected")],
        )
        prompt = render_migration_prompt(report)
        assert "Claude Code Migration Prompt" in prompt
        assert "Clerk" in prompt

    def test_go_react_prompt_uses_go_path(self):
        report = CheckReport(
            path="/test",
            arch="go_react",
            services=[ServiceResult("Resend", "fail", "not detected")],
        )
        prompt = render_migration_prompt(report)
        assert "api/internal/" in prompt

    def test_nextjs_prompt_uses_ts_path(self):
        report = CheckReport(
            path="/test",
            arch="nextjs",
            services=[ServiceResult("Resend", "fail", "not detected")],
        )
        prompt = render_migration_prompt(report)
        assert "src/lib/" in prompt


# ── Score calculation ─────────────────────────────────────────────


class TestCheckReportScore:
    def test_score_counts_passes(self):
        report = CheckReport(
            path="/test",
            arch="nextjs",
            services=[
                ServiceResult("A", "pass", ""),
                ServiceResult("B", "fail", ""),
                ServiceResult("C", "pass", ""),
            ],
            hosting=[ServiceResult("D", "pass", "")],
        )
        assert report.score == (3, 4)

    def test_score_includes_mobile(self):
        report = CheckReport(
            path="/test",
            arch="nextjs",
            services=[ServiceResult("A", "pass", "")],
            hosting=[],
            mobile=ServiceResult("Mobile", "pass", ""),
        )
        assert report.score == (2, 2)
