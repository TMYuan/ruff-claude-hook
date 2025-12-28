"""Shared test fixtures for ruff-claude-hook tests."""

import json
from typing import Any
from unittest.mock import Mock

import pytest


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory.

    Args:
        tmp_path: pytest's built-in temporary directory fixture

    Returns:
        Path to temporary project directory
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def sample_python_file(tmp_path):
    """Create a valid Python file for testing.

    Returns:
        Path to sample Python file
    """
    file_path = tmp_path / "sample.py"
    file_path.write_text(
        '''"""Sample module for testing."""


def greet(name):
    """Greet someone by name.

    Args:
        name: Name to greet

    Returns:
        Greeting message
    """
    return f"Hello, {name}!"


def add(a, b):
    """Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b
'''
    )
    return file_path


@pytest.fixture
def invalid_python_file(tmp_path):
    """Create a Python file with ruff violations.

    Returns:
        Path to invalid Python file
    """
    file_path = tmp_path / "invalid.py"
    file_path.write_text(
        """import sys
import os

def bad_function():
    unused_var = 42
    return None
"""
    )
    return file_path


@pytest.fixture
def mock_stdin(monkeypatch):
    """Helper fixture to mock sys.stdin.read().

    Usage:
        def test_something(mock_stdin):
            mock_stdin('{"file_path": "test.py"}')
            # Your test code here

    Args:
        monkeypatch: pytest's monkeypatch fixture

    Returns:
        Function to set stdin content
    """

    def _mock_stdin(content: str):
        mock = Mock(return_value=content)
        monkeypatch.setattr("sys.stdin.read", mock)
        return mock

    return _mock_stdin


@pytest.fixture
def claude_project_setup(tmp_project):
    """Create .claude/ directory structure.

    Returns:
        Dictionary with paths:
        - project_dir: Root project directory
        - claude_dir: .claude/ directory
        - settings_file: settings.json path
        - local_settings_file: settings.local.json path
        - claude_md_file: CLAUDE.md path
    """
    claude_dir = tmp_project / ".claude"
    claude_dir.mkdir()

    settings_file = claude_dir / "settings.json"
    local_settings_file = claude_dir / "settings.local.json"
    claude_md_file = claude_dir / "CLAUDE.md"

    return {
        "project_dir": tmp_project,
        "claude_dir": claude_dir,
        "settings_file": settings_file,
        "local_settings_file": local_settings_file,
        "claude_md_file": claude_md_file,
    }


@pytest.fixture
def capture_json_output():
    """Helper to parse JSON output from captured stdout.

    Usage:
        def test_something(capsys, capture_json_output):
            # Code that prints JSON
            result = capture_json_output(capsys)
            assert result["success"] is True

    Returns:
        Function to capture and parse JSON from capsys
    """

    def _capture(capsys) -> dict[str, Any]:
        captured = capsys.readouterr()
        output = captured.out.strip()
        if not output:
            return {}
        return json.loads(output)

    return _capture


@pytest.fixture
def sample_settings():
    """Sample Claude Code settings.json configuration.

    Returns:
        Dictionary with sample settings
    """
    return {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "Read",
                    "hooks": [{"type": "command", "command": "echo 'Read hook'"}],
                }
            ]
        },
        "customOption": "preserved",
    }


@pytest.fixture
def sample_local_settings():
    """Sample Claude Code settings.local.json configuration.

    Returns:
        Dictionary with sample local settings
    """
    return {"permissions": {"allow": ["Bash(git:*)"]}, "localCustomOption": "preserved"}


@pytest.fixture
def sample_claude_md():
    """Sample CLAUDE.md content without ruff section.

    Returns:
        String with sample markdown content
    """
    return """# My Project

## Custom Instructions

This is my project's custom Claude instructions.

## Workflow

- Do this
- Do that
"""


@pytest.fixture
def sample_claude_md_with_ruff():
    """Sample CLAUDE.md content with existing ruff section.

    Returns:
        String with markdown including ruff section
    """
    return """# My Project

## Custom Instructions

This is my project's custom Claude instructions.

<!-- ruff-claude-hook-start -->

# Old Ruff Instructions

This will be replaced.

<!-- ruff-claude-hook-end -->

## Workflow

- Do this
- Do that
"""
