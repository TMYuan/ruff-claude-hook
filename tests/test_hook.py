"""Tests for hook.py - PostToolUse hook functionality."""

import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from ruff_claude_hook.hook import main


@pytest.mark.unit
def test_hook_success_on_valid_python_file(
    mock_stdin, sample_python_file, capsys, capture_json_output
):
    """Test successful workflow on valid Python file."""
    # Mock stdin with valid Edit tool output
    input_data = {
        "tool_name": "Edit",
        "parameters": {"file_path": str(sample_python_file)},
    }
    mock_stdin(json.dumps(input_data))

    # Mock all subprocess.run calls to succeed
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stderr="")

        main()

        # Verify all 3 ruff commands were called
        assert mock_run.call_count == 3
        calls = mock_run.call_args_list

        # Phase 1: ruff check --fix
        assert calls[0][0][0] == ["ruff", "check", "--fix", str(sample_python_file)]

        # Phase 2: ruff format
        assert calls[1][0][0] == ["ruff", "format", str(sample_python_file)]

        # Phase 3: ruff check
        assert calls[2][0][0] == ["ruff", "check", str(sample_python_file)]

    # Verify success output
    result = capture_json_output(capsys)
    assert result["continue"] is True
    assert "systemMessage" in result
    assert sample_python_file.name in result["systemMessage"]


@pytest.mark.unit
def test_hook_reports_errors_on_invalid_python(
    mock_stdin, invalid_python_file, capsys, capture_json_output
):
    """Test error reporting when ruff check finds issues."""
    input_data = {
        "tool_name": "Edit",
        "parameters": {"file_path": str(invalid_python_file)},
    }
    mock_stdin(json.dumps(input_data))

    with patch("subprocess.run") as mock_run:
        # Phases 1 & 2 succeed, phase 3 fails with errors
        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[1] == "check" and "--fix" not in cmd:
                # Final check phase - return errors
                error_msg = (
                    f"{invalid_python_file}:5:5: F841 "
                    "Local variable assigned but never used\n"
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

        main()

    # Verify error output
    result = capture_json_output(capsys)
    assert result["continue"] is True
    assert "systemMessage" in result
    assert "❌ Ruff errors" in result["systemMessage"]
    assert "F841" in result["systemMessage"]


@pytest.mark.unit
def test_hook_runs_three_phase_workflow(mock_stdin, sample_python_file):
    """Test that all 3 ruff commands are executed in order."""
    input_data = {
        "tool_name": "Edit",
        "parameters": {"file_path": str(sample_python_file)},
    }
    mock_stdin(json.dumps(input_data))

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stderr="")

        main()

        # Extract command phases
        commands = [call[0][0] for call in mock_run.call_args_list]

        assert len(commands) == 3
        assert commands[0][1:3] == ["check", "--fix"]
        assert commands[1][1] == "format"
        assert commands[2][1] == "check"


@pytest.mark.unit
def test_hook_skips_non_json_input(mock_stdin, capsys):
    """Test that non-JSON input is silently skipped."""
    mock_stdin("not valid json{")

    main()

    captured = capsys.readouterr()
    assert captured.out == ""


@pytest.mark.unit
def test_hook_skips_missing_file_path(mock_stdin, capsys):
    """Test that input without file_path is skipped."""
    input_data = {"tool_name": "Edit", "parameters": {"other_param": "value"}}
    mock_stdin(json.dumps(input_data))

    main()

    captured = capsys.readouterr()
    assert captured.out == ""


@pytest.mark.unit
def test_hook_skips_non_python_files(mock_stdin, tmp_path, capsys):
    """Test that non-.py files are skipped."""
    js_file = tmp_path / "test.js"
    js_file.write_text("console.log('hello');")

    input_data = {"tool_name": "Edit", "parameters": {"file_path": str(js_file)}}
    mock_stdin(json.dumps(input_data))

    with patch("subprocess.run") as mock_run:
        main()

        # subprocess.run should never be called
        mock_run.assert_not_called()

    captured = capsys.readouterr()
    assert captured.out == ""


@pytest.mark.unit
def test_hook_skips_nonexistent_files(mock_stdin, tmp_path, capsys):
    """Test that nonexistent files are skipped."""
    fake_file = tmp_path / "nonexistent.py"

    input_data = {"tool_name": "Edit", "parameters": {"file_path": str(fake_file)}}
    mock_stdin(json.dumps(input_data))

    with patch("subprocess.run") as mock_run:
        main()

        mock_run.assert_not_called()

    captured = capsys.readouterr()
    assert captured.out == ""


@pytest.mark.unit
def test_hook_success_output_format(
    mock_stdin, sample_python_file, capsys, capture_json_output
):
    """Test that success output has correct JSON structure."""
    input_data = {
        "tool_name": "Edit",
        "parameters": {"file_path": str(sample_python_file)},
    }
    mock_stdin(json.dumps(input_data))

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stderr="")
        main()

    result = capture_json_output(capsys)

    # Verify structure
    assert "continue" in result
    assert "systemMessage" in result
    assert "hookSpecificOutput" in result
    assert isinstance(result["continue"], bool)
    assert isinstance(result["systemMessage"], str)
    assert result["continue"] is True


@pytest.mark.unit
def test_hook_error_output_format(
    mock_stdin, invalid_python_file, capsys, capture_json_output
):
    """Test that error output has correct JSON structure."""
    input_data = {
        "tool_name": "Edit",
        "parameters": {"file_path": str(invalid_python_file)},
    }
    mock_stdin(json.dumps(input_data))

    with patch("subprocess.run") as mock_run:

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[1] == "check" and "--fix" not in cmd:
                return Mock(returncode=1, stderr="Error message")
            return Mock(returncode=0, stderr="")

        mock_run.side_effect = run_side_effect
        main()

    result = capture_json_output(capsys)

    # Verify structure
    assert "continue" in result
    assert "systemMessage" in result
    assert "hookSpecificOutput" in result
    assert isinstance(result["continue"], bool)
    assert isinstance(result["systemMessage"], str)
    assert result["continue"] is True


@pytest.mark.unit
def test_hook_handles_subprocess_exception(
    mock_stdin, sample_python_file, capsys, capture_json_output
):
    """Test that subprocess exceptions are handled gracefully."""
    input_data = {
        "tool_name": "Edit",
        "parameters": {"file_path": str(sample_python_file)},
    }
    mock_stdin(json.dumps(input_data))

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "ruff")

        main()

    result = capture_json_output(capsys)
    assert result["continue"] is True
    assert "systemMessage" in result
    assert (
        "Error" in result["systemMessage"] or "error" in result["systemMessage"].lower()
    )


@pytest.mark.unit
def test_hook_skips_non_edit_tool(mock_stdin, sample_python_file, capsys):
    """Test that non-Edit tool calls are skipped."""
    input_data = {
        "tool_name": "Read",
        "parameters": {"file_path": str(sample_python_file)},
    }
    mock_stdin(json.dumps(input_data))

    with patch("subprocess.run") as mock_run:
        main()
        mock_run.assert_not_called()

    captured = capsys.readouterr()
    assert captured.out == ""


@pytest.mark.unit
def test_hook_handles_empty_stdin(mock_stdin, capsys):
    """Test that empty stdin is handled gracefully."""
    mock_stdin("")

    main()

    captured = capsys.readouterr()
    assert captured.out == ""


@pytest.mark.unit
def test_hook_preserves_file_content_on_format(
    mock_stdin, tmp_path, capsys, capture_json_output
):
    """Test that hook doesn't corrupt file content."""
    test_file = tmp_path / "preserve.py"
    original_content = '''def test():
    """Docstring."""
    return 42
'''
    test_file.write_text(original_content)

    input_data = {"tool_name": "Edit", "parameters": {"file_path": str(test_file)}}
    mock_stdin(json.dumps(input_data))

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stderr="")
        main()

    # File content should be unchanged (in real scenario ruff would format it)
    # But we're mocking, so it should stay the same
    content = test_file.read_text()
    assert "def test():" in content
    assert "return 42" in content


@pytest.mark.unit
def test_hook_reports_multiple_errors(
    mock_stdin, invalid_python_file, capsys, capture_json_output
):
    """Test that multiple ruff errors are all reported."""
    input_data = {
        "tool_name": "Edit",
        "parameters": {"file_path": str(invalid_python_file)},
    }
    mock_stdin(json.dumps(input_data))

    error_output = f"""{invalid_python_file}:3:1: F401 'sys' imported but unused
{invalid_python_file}:4:1: F401 'os' imported but unused
{invalid_python_file}:9:5: F841 Local variable 'unused_var' assigned but never used
"""

    with patch("subprocess.run") as mock_run:

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[1] == "check" and "--fix" not in cmd:
                result = Mock(returncode=1)
                result.stdout.strip.return_value = error_output.strip()
                result.stderr.strip.return_value = ""
                return result
            result = Mock(returncode=0)
            result.stdout.strip.return_value = ""
            result.stderr.strip.return_value = ""
            return result

        mock_run.side_effect = run_side_effect
        main()

    result = capture_json_output(capsys)
    assert result["continue"] is True

    # All errors should be in the systemMessage
    message = result["systemMessage"]
    assert "F401" in message
    assert "F841" in message
    assert "sys" in message or "os" in message
