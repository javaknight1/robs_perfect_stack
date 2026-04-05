"""Tests for the project generator (rob_stack/generate.py)."""

import pytest
from rob_stack.generate import title_case, schema_name


class TestTitleCase:
    def test_single_word(self):
        assert title_case("hello") == "Hello"

    def test_kebab_case(self):
        assert title_case("my-cool-app") == "My Cool App"

    def test_already_capitalized(self):
        assert title_case("My-App") == "My App"


class TestSchemaName:
    def test_replaces_hyphens(self):
        assert schema_name("my-cool-app") == "my_cool_app"

    def test_no_hyphens(self):
        assert schema_name("myapp") == "myapp"


class TestDryRun:
    """Smoke test: dry run should not create any files."""

    def test_nextjs_dry_run(self, tmp_path, monkeypatch):
        # Simulate inputs: name, description, arch=1 (Next.js), mobile=n
        inputs = iter(["test-app", "A test app", "1", "n"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.chdir(tmp_path)

        from rob_stack.generate import run_generate
        run_generate(dry_run=True)

        # Dry run should NOT have created the project directory
        assert not (tmp_path / "test-app").exists()

    def test_go_dry_run(self, tmp_path, monkeypatch):
        # Simulate inputs: name, description, arch=2 (Go), mobile=n, github user
        inputs = iter(["test-app", "A test app", "2", "n", "testuser"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.chdir(tmp_path)

        from rob_stack.generate import run_generate
        run_generate(dry_run=True)

        assert not (tmp_path / "test-app").exists()


class TestGenerate:
    """Smoke test: generation creates expected files."""

    def test_nextjs_generates_expected_files(self, tmp_path, monkeypatch):
        inputs = iter(["test-app", "A test app", "1", "n"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.chdir(tmp_path)
        # Prevent git init from running
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: None)

        from rob_stack.generate import run_generate
        run_generate(dry_run=False)

        root = tmp_path / "test-app"
        assert root.is_dir()
        assert (root / "package.json").exists()
        assert (root / "next.config.ts").exists()
        assert (root / "tsconfig.json").exists()
        assert (root / "middleware.ts").exists()
        assert (root / "vercel.json").exists()
        assert (root / ".env.example").exists()
        assert (root / "src/app/layout.tsx").exists()
        assert (root / "src/app/page.tsx").exists()
        assert (root / "src/lib/supabase.ts").exists()
        assert (root / "src/lib/redis.ts").exists()
        assert (root / "src/lib/resend.ts").exists()
        assert (root / "src/lib/r2.ts").exists()
        assert (root / "src/lib/posthog.ts").exists()
        assert (root / "src/components/providers.tsx").exists()
        assert (root / "src/app/(auth)/sign-in/[[...sign-in]]/page.tsx").exists()
        assert (root / "src/app/(auth)/sign-up/[[...sign-up]]/page.tsx").exists()
        assert (root / "src/app/(auth)/layout.tsx").exists()
        assert (root / "instrumentation.ts").exists()
        assert (root / "src/app/dashboard/page.tsx").exists()
        assert (root / "postcss.config.mjs").exists()
        assert (root / ".gitignore").exists()
        assert (root / "docker-compose.yml").exists()
        assert (root / "scripts/init-db.sql").exists()
        assert (root / "supabase/migrations/001_init.sql").exists()
        assert (root / "README.md").exists()

    def test_go_generates_expected_files(self, tmp_path, monkeypatch):
        inputs = iter(["test-app", "A test app", "2", "n", "testuser"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: None)

        from rob_stack.generate import run_generate
        run_generate(dry_run=False)

        root = tmp_path / "test-app"
        assert root.is_dir()
        # Web
        assert (root / "web/package.json").exists()
        assert (root / "web/index.html").exists()
        assert (root / "web/vite.config.ts").exists()
        assert (root / "web/src/main.tsx").exists()
        assert (root / "web/src/App.tsx").exists()
        assert (root / "web/src/lib/api.ts").exists()
        assert (root / "web/wrangler.toml").exists()
        # API
        assert (root / "api/go.mod").exists()
        assert (root / "api/cmd/worker/main.go").exists()
        assert (root / "api/internal/supabase/client.go").exists()
        assert (root / "api/internal/cache/redis.go").exists()
        assert (root / "api/internal/middleware/clerk.go").exists()
        assert (root / "api/internal/email/resend.go").exists()
        assert (root / "api/internal/storage/r2.go").exists()
        assert (root / "api/.env.example").exists()
        assert (root / "api/.dev.vars.example").exists()
        assert (root / "api/wrangler.toml").exists()
        assert (root / "Makefile").exists()
        # Shared
        assert (root / ".gitignore").exists()
        assert (root / "docker-compose.yml").exists()
        assert (root / "README.md").exists()

    def test_mobile_generates_expected_files(self, tmp_path, monkeypatch):
        inputs = iter(["test-app", "A test app", "1", "y"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: None)

        from rob_stack.generate import run_generate
        run_generate(dry_run=False)

        root = tmp_path / "test-app"
        assert (root / "mobile/package.json").exists()
        assert (root / "mobile/app.json").exists()
        assert (root / "mobile/app/_layout.tsx").exists()
        assert (root / "mobile/app/index.tsx").exists()
        assert (root / "mobile/app/(auth)/sign-in.tsx").exists()
        assert (root / "mobile/lib/api.ts").exists()

    def test_go_module_path_uses_github_user(self, tmp_path, monkeypatch):
        inputs = iter(["test-app", "", "2", "n", "robavery"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: None)

        from rob_stack.generate import run_generate
        run_generate(dry_run=False)

        go_mod = (tmp_path / "test-app/api/go.mod").read_text()
        assert "github.com/robavery/test-app" in go_mod

    def test_directory_exists_aborts(self, tmp_path, monkeypatch):
        (tmp_path / "test-app").mkdir()
        inputs = iter(["test-app", "", "1", "n"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        monkeypatch.chdir(tmp_path)

        from rob_stack.generate import run_generate
        with pytest.raises(SystemExit):
            run_generate(dry_run=False)
