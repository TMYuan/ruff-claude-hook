"""Tests for cli.py - Command-line interface."""

import sys
from unittest.mock import patch

import pytest

from ruff_claude_hook.cli import check_installation, main


@pytest.mark.unit
def test_check_installation_success(capsys):
    """Test successful installation check when both ruff and hook are found."""
    with patch("shutil.which") as mock_which:
        # Both ruff and ruff-claude-hook are found
        mock_which.return_value = "/usr/local/bin/ruff"

        result = check_installation()

        assert result == 0

        captured = capsys.readouterr()
        assert "✅" in captured.out
        assert "ruff" in captured.out.lower()


@pytest.mark.unit
def test_check_installation_ruff_not_found(capsys):
    """Test installation check when ruff is not found."""
    with patch("shutil.which") as mock_which:

        def which_side_effect(cmd):
            if cmd == "ruff":
                return None
            return "/usr/local/bin/ruff-claude-hook"

        mock_which.side_effect = which_side_effect

        result = check_installation()

        assert result == 1

        captured = capsys.readouterr()
        assert "❌" in captured.out
        assert "ruff" in captured.out.lower()


@pytest.mark.unit
def test_check_installation_hook_not_found(capsys):
    """Test installation check when hook is not in PATH."""
    with patch("shutil.which") as mock_which:

        def which_side_effect(cmd):
            if cmd == "ruff":
                return "/usr/local/bin/ruff"
            return None

        mock_which.side_effect = which_side_effect

        result = check_installation()

        assert result == 1

        captured = capsys.readouterr()
        assert "⚠️" in captured.out
        assert "ruff-claude-hook" in captured.out


@pytest.mark.unit
def test_check_installation_both_missing(capsys):
    """Test installation check when both are missing."""
    with patch("shutil.which") as mock_which:
        mock_which.return_value = None

        result = check_installation()

        assert result == 1

        captured = capsys.readouterr()
        output = captured.out
        assert output.count("❌") >= 1


@pytest.mark.unit
def test_main_init_command(monkeypatch):
    """Test that 'init' command routes to init_project()."""
    monkeypatch.setattr(sys, "argv", ["ruff-claude-hook", "init"])

    with patch("ruff_claude_hook.cli.init_project") as mock_init:
        mock_init.return_value = 0

        result = main()

        mock_init.assert_called_once_with(force=False)
        assert result == 0


@pytest.mark.unit
def test_main_init_with_force_flag(monkeypatch):
    """Test that '--force' flag is passed to init_project()."""
    monkeypatch.setattr(sys, "argv", ["ruff-claude-hook", "init", "--force"])

    with patch("ruff_claude_hook.cli.init_project") as mock_init:
        mock_init.return_value = 0

        result = main()

        mock_init.assert_called_once_with(force=True)
        assert result == 0


@pytest.mark.unit
def test_main_check_command(monkeypatch):
    """Test that 'check' command routes to check_installation()."""
    monkeypatch.setattr(sys, "argv", ["ruff-claude-hook", "check"])

    with patch("ruff_claude_hook.cli.check_installation") as mock_check:
        mock_check.return_value = 0

        result = main()

        mock_check.assert_called_once()
        assert result == 0


@pytest.mark.unit
def test_main_version_flag(monkeypatch, capsys):
    """Test that '--version' displays version and exits."""
    monkeypatch.setattr(sys, "argv", ["ruff-claude-hook", "--version"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "0.1.0" in captured.out


@pytest.mark.unit
def test_main_version_flag_short(monkeypatch, capsys):
    """Test that '-v' displays version and exits."""
    monkeypatch.setattr(sys, "argv", ["ruff-claude-hook", "-v"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "0.1.0" in captured.out


@pytest.mark.unit
def test_main_no_command_runs_hook(monkeypatch):
    """Test that no command triggers hook mode."""
    monkeypatch.setattr(sys, "argv", ["ruff-claude-hook"])

    with patch("ruff_claude_hook.cli.hook_main") as mock_hook:
        main()

        mock_hook.assert_called_once()


@pytest.mark.unit
def test_main_help_flag(monkeypatch, capsys):
    """Test that '--help' displays help message."""
    monkeypatch.setattr(sys, "argv", ["ruff-claude-hook", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "usage" in captured.out.lower() or "ruff-claude-hook" in captured.out


@pytest.mark.unit
def test_main_init_returns_error_code(monkeypatch):
    """Test that init errors are propagated."""
    monkeypatch.setattr(sys, "argv", ["ruff-claude-hook", "init"])

    with patch("ruff_claude_hook.cli.init_project") as mock_init:
        mock_init.return_value = 1  # Error

        result = main()

        assert result == 1


@pytest.mark.unit
def test_main_check_returns_error_code(monkeypatch):
    """Test that check errors are propagated."""
    monkeypatch.setattr(sys, "argv", ["ruff-claude-hook", "check"])

    with patch("ruff_claude_hook.cli.check_installation") as mock_check:
        mock_check.return_value = 1  # Error

        result = main()

        assert result == 1
