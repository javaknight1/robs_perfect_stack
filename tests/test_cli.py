"""Tests for the CLI dispatcher (rob_stack/cli.py)."""

import sys
from unittest.mock import patch

import pytest


class TestMainHelp:
    def test_no_args_prints_help(self, capsys):
        with patch.object(sys, "argv", ["rob-stack"]):
            from rob_stack.cli import main
            main()
        out = capsys.readouterr().out
        assert "rob-stack new" in out.lower() or "Commands" in out

    def test_help_flag(self, capsys):
        with patch.object(sys, "argv", ["rob-stack", "--help"]):
            from rob_stack.cli import main
            main()
        out = capsys.readouterr().out
        assert "Commands" in out


class TestMainVersion:
    def test_version_command(self, capsys):
        with patch.object(sys, "argv", ["rob-stack", "version"]):
            from rob_stack.cli import main
            main()
        out = capsys.readouterr().out
        assert "rob-stack" in out

    def test_version_flag(self, capsys):
        with patch.object(sys, "argv", ["rob-stack", "--version"]):
            from rob_stack.cli import main
            main()
        out = capsys.readouterr().out
        assert "rob-stack" in out


class TestMainNew:
    def test_new_calls_generate(self):
        with patch.object(sys, "argv", ["rob-stack", "new"]), \
             patch("rob_stack.cli.run_generate") as mock_gen:
            from rob_stack.cli import main
            main()
            mock_gen.assert_called_once_with(dry_run=False)

    def test_new_dry_run(self):
        with patch.object(sys, "argv", ["rob-stack", "new", "--dry-run"]), \
             patch("rob_stack.cli.run_generate") as mock_gen:
            from rob_stack.cli import main
            main()
            mock_gen.assert_called_once_with(dry_run=True)


class TestMainCheck:
    def test_check_default_path(self):
        with patch.object(sys, "argv", ["rob-stack", "check"]), \
             patch("rob_stack.cli.run_check") as mock_check:
            from rob_stack.cli import main
            main()
            mock_check.assert_called_once_with(".", service_filter=None, json_output=False)

    def test_check_with_path(self):
        with patch.object(sys, "argv", ["rob-stack", "check", "/some/path"]), \
             patch("rob_stack.cli.run_check") as mock_check:
            from rob_stack.cli import main
            main()
            mock_check.assert_called_once_with("/some/path", service_filter=None, json_output=False)

    def test_check_with_service_filter(self):
        with patch.object(sys, "argv", ["rob-stack", "check", ".", "--service", "clerk"]), \
             patch("rob_stack.cli.run_check") as mock_check:
            from rob_stack.cli import main
            main()
            mock_check.assert_called_once_with(".", service_filter="clerk", json_output=False)

    def test_check_service_filter_without_path(self):
        with patch.object(sys, "argv", ["rob-stack", "check", "--service", "redis"]), \
             patch("rob_stack.cli.run_check") as mock_check:
            from rob_stack.cli import main
            main()
            mock_check.assert_called_once_with(".", service_filter="redis", json_output=False)

    def test_check_with_json_flag(self):
        with patch.object(sys, "argv", ["rob-stack", "check", ".", "--json"]), \
             patch("rob_stack.cli.run_check") as mock_check:
            from rob_stack.cli import main
            main()
            mock_check.assert_called_once_with(".", service_filter=None, json_output=True)

    def test_check_json_with_service_filter(self):
        with patch.object(sys, "argv", ["rob-stack", "check", "--json", "--service", "clerk"]), \
             patch("rob_stack.cli.run_check") as mock_check:
            from rob_stack.cli import main
            main()
            mock_check.assert_called_once_with(".", service_filter="clerk", json_output=True)


class TestMainUnknown:
    def test_unknown_command_exits(self):
        with patch.object(sys, "argv", ["rob-stack", "bogus"]):
            from rob_stack.cli import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
