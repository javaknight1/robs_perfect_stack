"""Tests for pre-flight CLI tool checks (rob_stack/preflight.py)."""

import pytest
from unittest.mock import patch, MagicMock
import subprocess

from rob_stack.preflight import _parse_version, check_tool, run_preflight


class TestParseVersion:
    def test_semver(self):
        assert _parse_version("v20.11.0") == (20, 11, 0)

    def test_go_version(self):
        assert _parse_version("go version go1.23.2 darwin/arm64") == (1, 23, 2)

    def test_two_part(self):
        assert _parse_version("3.2") == (3, 2, 0)

    def test_no_match(self):
        assert _parse_version("no version here") is None

    def test_prefixed(self):
        assert _parse_version("tinygo version 0.32.0") == (0, 32, 0)


class TestCheckTool:
    @patch("rob_stack.preflight._run")
    def test_not_found(self, mock_run):
        mock_run.return_value = None
        err = check_tool("Node.js", ["node", "--version"], (18, 0, 0))
        assert err is not None
        assert "not found" in err

    @patch("rob_stack.preflight._run")
    def test_version_too_low(self, mock_run):
        mock_run.return_value = "v16.0.0"
        err = check_tool("Node.js", ["node", "--version"], (18, 0, 0))
        assert err is not None
        assert "need >= 18.0.0" in err

    @patch("rob_stack.preflight._run")
    def test_version_ok(self, mock_run):
        mock_run.return_value = "v20.11.0"
        err = check_tool("Node.js", ["node", "--version"], (18, 0, 0))
        assert err is None

    @patch("rob_stack.preflight._run")
    def test_no_min_version(self, mock_run):
        mock_run.return_value = "supabase 1.0.0"
        err = check_tool("Supabase CLI", ["supabase", "--version"], None)
        assert err is None

    @patch("rob_stack.preflight._run")
    def test_unparseable_version(self, mock_run):
        mock_run.return_value = "something weird"
        err = check_tool("Tool", ["tool", "--version"], (1, 0, 0))
        assert err is not None
        assert "could not parse" in err


class TestRunPreflight:
    @patch("rob_stack.preflight.check_tool")
    def test_passes_when_all_ok(self, mock_check):
        mock_check.return_value = None
        # Should not raise
        run_preflight(is_nextjs=True, has_mobile=False)

    @patch("rob_stack.preflight.check_tool")
    def test_exits_on_missing_tools(self, mock_check):
        mock_check.return_value = "Node.js — not found"
        with pytest.raises(SystemExit):
            run_preflight(is_nextjs=True, has_mobile=False)

    @patch("rob_stack.preflight.check_tool")
    def test_go_checks_extra_tools(self, mock_check):
        calls = []
        def track(name, cmd, min_ver):
            calls.append(name)
            return None
        mock_check.side_effect = track
        run_preflight(is_nextjs=False, has_mobile=False)
        assert "Go" in calls
        assert "TinyGo" in calls
        assert "Wrangler" in calls

    @patch("rob_stack.preflight.check_tool")
    def test_mobile_checks_expo(self, mock_check):
        calls = []
        def track(name, cmd, min_ver):
            calls.append(name)
            return None
        mock_check.side_effect = track
        run_preflight(is_nextjs=True, has_mobile=True)
        assert "Expo CLI" in calls
