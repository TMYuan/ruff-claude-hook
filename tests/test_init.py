"""Tests for init.py - Project initialization logic."""

import json

import pytest

from ruff_claude_hook.init import (
    init_project,
    merge_permissions,
    merge_settings,
)


@pytest.mark.unit
def test_merge_settings_adds_hook_to_empty_config():
    """Test merging hook into empty configuration."""
    existing = {}
    ruff_hook = {
        "matcher": "Edit",
        "hooks": [{"type": "command", "command": "ruff-claude-hook"}],
    }

    result = merge_settings(existing, ruff_hook)

    assert "hooks" in result
    assert "PostToolUse" in result["hooks"]
    assert len(result["hooks"]["PostToolUse"]) == 1
    assert result["hooks"]["PostToolUse"][0] == ruff_hook


@pytest.mark.unit
def test_merge_settings_preserves_existing_hooks():
    """Test that existing hooks are preserved during merge."""
    existing = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "Read",
                    "hooks": [{"type": "command", "command": "echo 'test'"}],
                }
            ]
        },
        "customOption": "value",
    }
    ruff_hook = {
        "matcher": "Edit",
        "hooks": [{"type": "command", "command": "ruff-claude-hook"}],
    }

    result = merge_settings(existing, ruff_hook)

    assert len(result["hooks"]["PostToolUse"]) == 2
    assert result["customOption"] == "value"
    assert result["hooks"]["PostToolUse"][0]["matcher"] == "Read"
    assert result["hooks"]["PostToolUse"][1] == ruff_hook


@pytest.mark.unit
def test_merge_settings_skips_if_already_present():
    """Test idempotency - don't add duplicate ruff hooks."""
    ruff_hook = {
        "matcher": "Edit",
        "hooks": [{"type": "command", "command": "ruff-claude-hook"}],
    }
    existing = {"hooks": {"PostToolUse": [ruff_hook]}}

    result = merge_settings(existing, ruff_hook)

    # Should still be only 1 hook
    assert len(result["hooks"]["PostToolUse"]) == 1


@pytest.mark.unit
def test_merge_permissions_adds_to_empty_config():
    """Test adding permission to empty configuration."""
    existing = {}

    result = merge_permissions(existing)

    assert "permissions" in result
    assert "allow" in result["permissions"]
    assert "Bash(ruff-claude-hook:*)" in result["permissions"]["allow"]


@pytest.mark.unit
def test_merge_permissions_preserves_existing():
    """Test that existing permissions are preserved."""
    existing = {
        "permissions": {"allow": ["Bash(git:*)", "Bash(npm:*)"]},
        "customSetting": "preserved",
    }

    result = merge_permissions(existing)

    assert len(result["permissions"]["allow"]) == 3
    assert "Bash(git:*)" in result["permissions"]["allow"]
    assert "Bash(ruff-claude-hook:*)" in result["permissions"]["allow"]
    assert result["customSetting"] == "preserved"


@pytest.mark.unit
def test_merge_permissions_skips_if_already_present():
    """Test idempotency - don't add duplicate permissions."""
    existing = {"permissions": {"allow": ["Bash(ruff-claude-hook:*)"]}}

    result = merge_permissions(existing)

    # Should still be only 1 permission
    assert len(result["permissions"]["allow"]) == 1


@pytest.mark.unit
def test_init_creates_claude_directory(tmp_project, monkeypatch, capsys):
    """Test that .claude/ directory is created."""
    monkeypatch.chdir(tmp_project)

    init_project()

    claude_dir = tmp_project / ".claude"
    assert claude_dir.exists()
    assert claude_dir.is_dir()


@pytest.mark.unit
def test_init_creates_settings_json_from_template(tmp_project, monkeypatch):
    """Test that settings.json is created from template."""
    monkeypatch.chdir(tmp_project)

    init_project()

    settings_file = tmp_project / ".claude" / "settings.json"
    assert settings_file.exists()

    # Verify it's valid JSON with ruff hook
    with open(settings_file) as f:
        config = json.load(f)

    assert "hooks" in config
    assert "PostToolUse" in config["hooks"]
    assert any(
        "ruff-claude-hook" in str(hook) for hook in config["hooks"]["PostToolUse"]
    )


@pytest.mark.unit
def test_init_creates_local_settings_from_template(tmp_project, monkeypatch):
    """Test that settings.local.json is created from template."""
    monkeypatch.chdir(tmp_project)

    init_project()

    local_settings = tmp_project / ".claude" / "settings.local.json"
    assert local_settings.exists()

    # Verify it's valid JSON with permission
    with open(local_settings) as f:
        config = json.load(f)

    assert "permissions" in config
    assert "allow" in config["permissions"]
    assert "Bash(ruff-claude-hook:*)" in config["permissions"]["allow"]


@pytest.mark.unit
def test_init_creates_claude_md_from_template(tmp_project, monkeypatch):
    """Test that CLAUDE.md is created from template."""
    monkeypatch.chdir(tmp_project)

    init_project()

    claude_md = tmp_project / ".claude" / "CLAUDE.md"
    assert claude_md.exists()

    content = claude_md.read_text()
    assert "ruff" in content.lower()
    assert "<!-- ruff-claude-hook-start -->" in content
    assert "<!-- ruff-claude-hook-end -->" in content


@pytest.mark.unit
def test_init_merges_with_existing_settings_json(
    tmp_project, monkeypatch, sample_settings
):
    """Test that existing settings.json is merged, not overwritten."""
    monkeypatch.chdir(tmp_project)

    # Create existing settings
    claude_dir = tmp_project / ".claude"
    claude_dir.mkdir()
    settings_file = claude_dir / "settings.json"

    with open(settings_file, "w") as f:
        json.dump(sample_settings, f)

    init_project()

    # Load and verify merge
    with open(settings_file) as f:
        config = json.load(f)

    # Original hook should be preserved
    assert any(hook["matcher"] == "Read" for hook in config["hooks"]["PostToolUse"])

    # Ruff hook should be added
    assert any(
        "ruff-claude-hook" in str(hook) for hook in config["hooks"]["PostToolUse"]
    )

    # Custom option should be preserved
    assert config["customOption"] == "preserved"


@pytest.mark.unit
def test_init_merges_with_existing_local_settings(
    tmp_project, monkeypatch, sample_local_settings
):
    """Test that existing settings.local.json is merged."""
    monkeypatch.chdir(tmp_project)

    claude_dir = tmp_project / ".claude"
    claude_dir.mkdir()
    local_settings = claude_dir / "settings.local.json"

    with open(local_settings, "w") as f:
        json.dump(sample_local_settings, f)

    init_project()

    with open(local_settings) as f:
        config = json.load(f)

    # Original permission should be preserved
    assert "Bash(git:*)" in config["permissions"]["allow"]

    # Ruff permission should be added
    assert "Bash(ruff-claude-hook:*)" in config["permissions"]["allow"]

    # Custom option should be preserved
    assert config["localCustomOption"] == "preserved"


@pytest.mark.unit
def test_init_updates_existing_claude_md_section(
    tmp_project, monkeypatch, sample_claude_md_with_ruff
):
    """Test that existing ruff section is updated, not duplicated."""
    monkeypatch.chdir(tmp_project)

    claude_dir = tmp_project / ".claude"
    claude_dir.mkdir()
    claude_md = claude_dir / "CLAUDE.md"

    claude_md.write_text(sample_claude_md_with_ruff)

    init_project()

    content = claude_md.read_text()

    # Should have exactly one start and one end marker
    assert content.count("<!-- ruff-claude-hook-start -->") == 1
    assert content.count("<!-- ruff-claude-hook-end -->") == 1

    # Custom content should be preserved
    assert "My Project" in content
    assert "Custom Instructions" in content

    # Old content should be replaced
    assert "Old Ruff Instructions" not in content


@pytest.mark.unit
def test_init_adds_new_claude_md_section(tmp_project, monkeypatch, sample_claude_md):
    """Test that ruff section is added to existing CLAUDE.md."""
    monkeypatch.chdir(tmp_project)

    claude_dir = tmp_project / ".claude"
    claude_dir.mkdir()
    claude_md = claude_dir / "CLAUDE.md"

    claude_md.write_text(sample_claude_md)

    init_project()

    content = claude_md.read_text()

    # Markers should be added
    assert "<!-- ruff-claude-hook-start -->" in content
    assert "<!-- ruff-claude-hook-end -->" in content

    # Original content should be preserved
    assert "My Project" in content
    assert "Custom Instructions" in content


@pytest.mark.unit
def test_init_force_creates_backups(tmp_project, monkeypatch):
    """Test that --force creates .backup files."""
    monkeypatch.chdir(tmp_project)

    # Create existing files
    claude_dir = tmp_project / ".claude"
    claude_dir.mkdir()

    settings = claude_dir / "settings.json"
    settings.write_text('{"existing": "config"}')

    local_settings = claude_dir / "settings.local.json"
    local_settings.write_text('{"local": "config"}')

    claude_md = claude_dir / "CLAUDE.md"
    claude_md.write_text("# Existing content")

    init_project(force=True)

    # Verify backups were created
    assert (claude_dir / "settings.json.backup").exists()
    assert (claude_dir / "settings.local.json.backup").exists()
    assert (claude_dir / "CLAUDE.md.backup").exists()


@pytest.mark.unit
def test_init_force_overwrites_all_files(tmp_project, monkeypatch):
    """Test that --force replaces files with templates."""
    monkeypatch.chdir(tmp_project)

    claude_dir = tmp_project / ".claude"
    claude_dir.mkdir()

    settings = claude_dir / "settings.json"
    settings.write_text('{"old": "content"}')

    init_project(force=True)

    # File should be overwritten with template content
    with open(settings) as f:
        config = json.load(f)

    assert "old" not in config
    assert "hooks" in config


@pytest.mark.unit
def test_init_handles_corrupted_settings_json(tmp_project, monkeypatch, capsys):
    """Test recovery from corrupted settings.json."""
    monkeypatch.chdir(tmp_project)

    claude_dir = tmp_project / ".claude"
    claude_dir.mkdir()

    settings = claude_dir / "settings.json"
    settings.write_text("not valid json{{{")

    init_project()

    # Should create backup and use template
    assert (claude_dir / "settings.json.backup").exists()

    # New file should be valid JSON
    with open(settings) as f:
        config = json.load(f)

    assert "hooks" in config

    captured = capsys.readouterr()
    assert "backup" in captured.out.lower() or "error" in captured.out.lower()


@pytest.mark.unit
def test_init_returns_success_code(tmp_project, monkeypatch, capsys):
    """Test that successful init returns 0."""
    monkeypatch.chdir(tmp_project)

    result = init_project()

    assert result == 0

    captured = capsys.readouterr()
    assert "✅" in captured.out


@pytest.mark.unit
def test_init_is_idempotent(tmp_project, monkeypatch):
    """Test that running init multiple times is safe."""
    monkeypatch.chdir(tmp_project)

    # Run init twice
    init_project()
    init_project()

    # Files should exist and be valid
    settings = tmp_project / ".claude" / "settings.json"
    with open(settings) as f:
        config = json.load(f)

    # Should have exactly 2 ruff hooks (Edit and Write)
    ruff_hooks = [
        h for h in config["hooks"]["PostToolUse"] if "ruff-claude-hook" in str(h)
    ]
    assert len(ruff_hooks) == 2

    # Verify we have both Edit and Write matchers
    matchers = {h["matcher"] for h in ruff_hooks}
    assert matchers == {"Edit", "Write"}

    # CLAUDE.md should not have duplicate sections
    claude_md = tmp_project / ".claude" / "CLAUDE.md"
    content = claude_md.read_text()
    assert content.count("<!-- ruff-claude-hook-start -->") == 1
