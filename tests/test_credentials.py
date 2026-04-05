"""Tests for credential prompts (rob_stack/credentials.py)."""

from unittest.mock import patch

from rob_stack.credentials import (
    prompt_credentials,
    SUPABASE_LOCAL_URL,
    SUPABASE_LOCAL_ANON_KEY,
    SUPABASE_LOCAL_SERVICE_ROLE_KEY,
)


class TestPromptCredentials:
    @patch("rob_stack.credentials._ask_optional", return_value="")
    def test_returns_dict_with_expected_keys_nextjs(self, mock_ask):
        creds = prompt_credentials("test-app", "test_app", is_nextjs=True)
        assert isinstance(creds, dict)
        # User-prompted keys
        assert "CLERK_PUBLISHABLE_KEY" in creds
        assert "CLERK_SECRET_KEY" in creds
        assert "UPSTASH_REDIS_REST_URL" in creds
        assert "UPSTASH_REDIS_REST_TOKEN" in creds
        assert "RESEND_API_KEY" in creds
        assert "R2_ACCOUNT_ID" in creds
        assert "R2_ACCESS_KEY_ID" in creds
        assert "R2_SECRET_ACCESS_KEY" in creds
        assert "POSTHOG_KEY" in creds
        assert "SENTRY_DSN" in creds
        assert "BETTERSTACK_SOURCE_TOKEN" in creds

    @patch("rob_stack.credentials._ask_optional", return_value="")
    def test_returns_dict_with_expected_keys_go(self, mock_ask):
        creds = prompt_credentials("test-app", "test_app", is_nextjs=False)
        # Go-specific
        assert "CLERK_JWKS_URL" in creds
        assert "ALLOWED_ORIGINS" in creds
        assert "VITE_API_URL" in creds

    @patch("rob_stack.credentials._ask_optional", return_value="")
    def test_auto_populated_supabase_defaults(self, mock_ask):
        creds = prompt_credentials("test-app", "test_app", is_nextjs=True)
        assert creds["SUPABASE_URL"] == SUPABASE_LOCAL_URL
        assert creds["SUPABASE_ANON_KEY"] == SUPABASE_LOCAL_ANON_KEY
        assert creds["SUPABASE_SERVICE_ROLE_KEY"] == SUPABASE_LOCAL_SERVICE_ROLE_KEY

    @patch("rob_stack.credentials._ask_optional", return_value="")
    def test_auto_populated_database_url(self, mock_ask):
        creds = prompt_credentials("test-app", "test_app", is_nextjs=True)
        assert "test_app" in creds["DATABASE_URL"]
        assert "54322" in creds["DATABASE_URL"]

    @patch("rob_stack.credentials._ask_optional", return_value="")
    def test_auto_populated_r2_bucket(self, mock_ask):
        creds = prompt_credentials("my-app", "my_app", is_nextjs=True)
        assert creds["R2_BUCKET_NAME"] == "my-app"

    @patch("rob_stack.credentials._ask_optional", return_value="")
    def test_nextjs_clerk_redirect_paths(self, mock_ask):
        creds = prompt_credentials("test-app", "test_app", is_nextjs=True)
        assert creds["CLERK_SIGN_IN_URL"] == "/sign-in"
        assert creds["CLERK_SIGN_UP_URL"] == "/sign-up"
        assert creds["CLERK_AFTER_SIGN_IN_URL"] == "/dashboard"

    @patch("rob_stack.credentials._ask_optional", return_value="")
    def test_go_no_clerk_redirect_paths(self, mock_ask):
        creds = prompt_credentials("test-app", "test_app", is_nextjs=False)
        assert "CLERK_SIGN_IN_URL" not in creds

    @patch("rob_stack.credentials._ask_optional")
    def test_user_values_are_stored(self, mock_ask):
        mock_ask.side_effect = [
            "pk_test_abc",   # clerk publishable
            "sk_test_xyz",   # clerk secret
            "https://my.upstash.io",  # upstash url
            "upstash_token",  # upstash token
            "re_mykey",      # resend
            "cf_account",    # r2 account
            "cf_key",        # r2 access key
            "cf_secret",     # r2 secret
            "phc_abc",       # posthog
            "https://sentry.dsn",  # sentry
            "bt_token",      # betterstack
        ]
        creds = prompt_credentials("test-app", "test_app", is_nextjs=True)
        assert creds["CLERK_PUBLISHABLE_KEY"] == "pk_test_abc"
        assert creds["CLERK_SECRET_KEY"] == "sk_test_xyz"
        assert creds["UPSTASH_REDIS_REST_URL"] == "https://my.upstash.io"
        assert creds["POSTHOG_KEY"] == "phc_abc"
