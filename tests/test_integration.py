"""Integration tests for ruff-claude-hook - End-to-end workflows."""

import json
import sys
from unittest.mock import Mock, patch

import pytest

from ruff_claude_hook.cli import main as cli_main
from ruff_claude_hook.hook import main as hook_main
from ruff_claude_hook.init import init_project


@pytest.mark.integration
def test_full_init_and_hook_workflow(tmp_project, monkeypatch):
    """Test complete user journey: init -> edit file -> hook runs."""
    monkeypatch.chdir(tmp_project)

    # Step 1: Initialize project
    result = init_project()
    assert result == 0

    # Verify .claude structure exists
    assert (tmp_project / ".claude" / "settings.json").exists()
    assert (tmp_project / ".claude" / "settings.local.json").exists()
    assert (tmp_project / ".claude" / "CLAUDE.md").exists()

    # Step 2: Create a Python file
    test_file = tmp_project / "test.py"
    test_file.write_text("def hello():\n    return 'world'\n")

    # Step 3: Simulate hook running after Edit
    input_data = {"tool_name": "Edit", "parameters": {"file_path": str(test_file)}}

    with patch("sys.stdin.read", return_value=json.dumps(input_data)):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stderr="")

            hook_main()

            # Verify all 3 ruff commands were called
            assert mock_run.call_count == 3


@pytest.mark.integration
def test_init_twice_is_idempotent(tmp_project, monkeypatch, capsys):
    """Test that running init multiple times is safe."""
    monkeypatch.chdir(tmp_project)

    # First init
    result1 = init_project()
    assert result1 == 0

    # Get file contents after first init
    settings_file = tmp_project / ".claude" / "settings.json"
    with open(settings_file) as f:
        config1 = json.load(f)

    claude_md = tmp_project / ".claude" / "CLAUDE.md"
    content1 = claude_md.read_text()
    len1 = len(content1.split("\n"))

    # Second init
    result2 = init_project()
    assert result2 == 0

    # Verify no duplicates
    with open(settings_file) as f:
        config2 = json.load(f)

    # Same number of hooks
    assert len(config2["hooks"]["PostToolUse"]) == len(config1["hooks"]["PostToolUse"])

    # CLAUDE.md should be same length (no growth)
    content2 = claude_md.read_text()
    len2 = len(content2.split("\n"))
    assert len2 == len1

    # Still only one marker pair
    assert content2.count("<!-- ruff-claude-hook-start -->") == 1
    assert content2.count("<!-- ruff-claude-hook-end -->") == 1


@pytest.mark.integration
def test_cli_check_after_init(tmp_project, monkeypatch):
    """Test that 'check' command works after installation."""
    monkeypatch.chdir(tmp_project)

    # Initialize first
    init_project()

    # Mock the which commands to simulate installed tools
    with patch("shutil.which") as mock_which:
        mock_which.return_value = "/usr/local/bin/ruff"

        monkeypatch.setattr(sys, "argv", ["ruff-claude-hook", "check"])
        result = cli_main()

        assert result == 0


@pytest.mark.integration
def test_hook_with_real_python_file_workflow(tmp_project, monkeypatch):
    """Test hook processing a real Python file through all phases."""
    monkeypatch.chdir(tmp_project)

    # Create a Python file with minor formatting issues
    test_file = tmp_project / "example.py"
    test_file.write_text('''def greet(name):
    """Greet someone."""
    return f"Hello, {name}!"


def add(a, b):
    """Add two numbers."""
    return a + b
''')

    # Simulate Edit tool input
    input_data = {"tool_name": "Edit", "parameters": {"file_path": str(test_file)}}

    with patch("sys.stdin.read", return_value=json.dumps(input_data)):
        with patch("subprocess.run") as mock_run:
            # Mock successful ruff execution
            mock_run.return_value = Mock(returncode=0, stderr="")

            hook_main()

            # Verify 3-phase workflow
            calls = mock_run.call_args_list
            assert len(calls) == 3

            # Phase 1: check --fix
            assert "check" in calls[0][0][0]
            assert "--fix" in calls[0][0][0]

            # Phase 2: format
            assert "format" in calls[1][0][0]

            # Phase 3: check
            assert "check" in calls[2][0][0]


@pytest.mark.integration
def test_init_preserves_complex_existing_config(tmp_project, monkeypatch):
    """Test that complex existing configurations are fully preserved."""
    monkeypatch.chdir(tmp_project)

    # Create .claude with complex existing config
    claude_dir = tmp_project / ".claude"
    claude_dir.mkdir()

    complex_config = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "Read",
                    "hooks": [{"type": "command", "command": "echo 'read'"}],
                },
                {
                    "matcher": "Write",
                    "hooks": [{"type": "command", "command": "echo 'write'"}],
                },
            ],
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": "echo 'pre-bash'"}],
                }
            ],
        },
        "customSettings": {"nested": {"deeply": {"value": "preserved"}}},
        "arrayOption": [1, 2, 3],
    }

    settings_file = claude_dir / "settings.json"
    with open(settings_file, "w") as f:
        json.dump(complex_config, f, indent=2)

    # Run init
    init_project()

    # Verify all original content preserved
    with open(settings_file) as f:
        result = json.load(f)

    # Original hooks preserved
    assert len(result["hooks"]["PostToolUse"]) == 3  # 2 original + 1 ruff
    assert "PreToolUse" in result["hooks"]

    # Custom settings preserved
    assert result["customSettings"]["nested"]["deeply"]["value"] == "preserved"
    assert result["arrayOption"] == [1, 2, 3]

    # Ruff hook added
    assert any(
        "ruff-claude-hook" in str(hook) for hook in result["hooks"]["PostToolUse"]
    )


@pytest.mark.integration
def test_cli_init_via_command_line(tmp_project, monkeypatch):
    """Test init command through CLI main function."""
    monkeypatch.chdir(tmp_project)
    monkeypatch.setattr(sys, "argv", ["ruff-claude-hook", "init"])

    result = cli_main()

    assert result == 0

    # Verify files created
    assert (tmp_project / ".claude" / "settings.json").exists()
    assert (tmp_project / ".claude" / "CLAUDE.md").exists()


@pytest.mark.integration
def test_hook_error_recovery(tmp_project, monkeypatch, capsys):
    """Test that hook gracefully handles and reports errors."""
    test_file = tmp_project / "broken.py"
    test_file.write_text("import unused_module\n")

    input_data = {"tool_name": "Edit", "parameters": {"file_path": str(test_file)}}

    with patch("sys.stdin.read", return_value=json.dumps(input_data)):
        with patch("subprocess.run") as mock_run:
            # Simulate ruff finding errors on final check
            def run_side_effect(*args, **kwargs):
                cmd = args[0]
                if cmd[1] == "check" and "--fix" not in cmd:
                    error_msg = (
                        f"{test_file}:1:1: F401 'unused_module' imported but unused\n"
                    )
                    result = Mock(returncode=1)
                    result.stdout.strip.return_value = error_msg.strip()
                    result.stderr.strip.return_value = ""
                    return result
                result = Mock(returncode=0)
                result.stdout.strip.return_value = ""
                result.stderr.strip.return_value = ""
                return result

            mock_run.side_effect = run_side_effect

            hook_main()

    captured = capsys.readouterr()
    output = captured.out

    # Should have JSON output
    result = json.loads(output.strip())
    assert result["continue"] is True
    assert "systemMessage" in result
    assert "F401" in result["systemMessage"]
    assert "unused_module" in result["systemMessage"]


@pytest.mark.integration
def test_complete_workflow_with_force_reinit(tmp_project, monkeypatch):
    """Test full workflow including force re-initialization."""
    monkeypatch.chdir(tmp_project)

    # Initial setup
    init_project()

    # Make manual changes to config
    settings = tmp_project / ".claude" / "settings.json"
    with open(settings) as f:
        config = json.load(f)

    config["userModification"] = "important"

    with open(settings, "w") as f:
        json.dump(config, f)

    # Force reinit
    init_project(force=True)

    # Backup should exist
    backup = tmp_project / ".claude" / "settings.json.backup"
    assert backup.exists()

    # Backup should contain user modification
    with open(backup) as f:
        backup_config = json.load(f)
    assert backup_config["userModification"] == "important"

    # New file should be from template (no user modification)
    with open(settings) as f:
        new_config = json.load(f)
    assert "userModification" not in new_config
    assert "hooks" in new_config
