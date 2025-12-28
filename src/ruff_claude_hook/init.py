"""Project initialization logic with smart settings merge."""

import json
import shutil
from pathlib import Path
from typing import Any


def merge_settings(
    existing: dict[str, Any], ruff_hook: dict[str, Any]
) -> dict[str, Any]:
    """Merge ruff hook into existing settings without overwriting.

    Args:
        existing: Existing settings configuration
        ruff_hook: Ruff hook configuration to add

    Returns:
        Merged configuration
    """
    # Ensure hooks structure exists
    existing.setdefault("hooks", {})
    existing["hooks"].setdefault("PostToolUse", [])

    # Check if ruff hook already exists
    has_ruff_hook = any(
        "ruff-claude-hook" in str(hook) for hook in existing["hooks"]["PostToolUse"]
    )

    if not has_ruff_hook:
        # Add ruff hook to PostToolUse
        existing["hooks"]["PostToolUse"].append(ruff_hook)

    return existing


def merge_permissions(existing: dict[str, Any]) -> dict[str, Any]:
    """Merge ruff-claude-hook permission into existing permissions.

    Args:
        existing: Existing permissions configuration

    Returns:
        Merged configuration
    """
    # Ensure permissions structure exists
    existing.setdefault("permissions", {})
    existing["permissions"].setdefault("allow", [])

    # Check if permission already exists
    permission = "Bash(ruff-claude-hook:*)"
    if permission not in existing["permissions"]["allow"]:
        existing["permissions"]["allow"].append(permission)

    return existing


def init_project(force: bool = False) -> int:
    """Initialize ruff hook in current project.

    Args:
        force: If True, backup and overwrite existing files

    Returns:
        Exit code (0 for success, 1 for error)
    """
    print("🚀 Initializing ruff-claude-hook...\n")

    # Get template directory
    template_dir = Path(__file__).parent / "templates"
    if not template_dir.exists():
        print(f"❌ Error: Template directory not found: {template_dir}")
        return 1

    # Create .claude directory if needed
    claude_dir = Path(".claude")
    claude_dir.mkdir(exist_ok=True)
    print(f"✅ Directory: {claude_dir.absolute()}")

    # Define ruff hook configuration
    ruff_hook_config = {
        "matcher": "Edit",
        "hooks": [{"type": "command", "command": "ruff-claude-hook"}],
    }

    # Process settings.json
    settings_file = claude_dir / "settings.json"
    template_settings = template_dir / "settings.json.template"

    if settings_file.exists() and not force:
        # Smart merge
        print(f"📝 Merging with existing: {settings_file}")
        try:
            with open(settings_file) as f:
                config = json.load(f)

            # Merge ruff hook
            config = merge_settings(config, ruff_hook_config)

            # Write merged config
            with open(settings_file, "w") as f:
                json.dump(config, f, indent=2)
            print("   ✅ Ruff hook added to existing settings")

        except (OSError, json.JSONDecodeError) as e:
            print(f"   ⚠️  Error reading settings.json: {e}")
            print("   Creating backup and using template...")
            shutil.copy(settings_file, settings_file.with_suffix(".json.backup"))
            shutil.copy(template_settings, settings_file)

    else:
        # Create from template
        if settings_file.exists() and force:
            backup = settings_file.with_suffix(".json.backup")
            shutil.copy(settings_file, backup)
            print(f"   💾 Backed up to: {backup}")

        shutil.copy(template_settings, settings_file)
        print(f"✅ Created: {settings_file}")

    # Process settings.local.json
    local_settings_file = claude_dir / "settings.local.json"
    template_local_settings = template_dir / "settings.local.json.template"

    if local_settings_file.exists() and not force:
        # Smart merge permissions
        print(f"📝 Merging with existing: {local_settings_file}")
        try:
            with open(local_settings_file) as f:
                config = json.load(f)

            # Merge permissions
            config = merge_permissions(config)

            # Write merged config
            with open(local_settings_file, "w") as f:
                json.dump(config, f, indent=2)
            print("   ✅ Ruff permission added to existing settings")

        except (OSError, json.JSONDecodeError) as e:
            print(f"   ⚠️  Error reading settings.local.json: {e}")
            print("   Creating backup and using template...")
            shutil.copy(
                local_settings_file, local_settings_file.with_suffix(".json.backup")
            )
            shutil.copy(template_local_settings, local_settings_file)

    else:
        # Create from template
        if local_settings_file.exists() and force:
            backup = local_settings_file.with_suffix(".json.backup")
            shutil.copy(local_settings_file, backup)
            print(f"   💾 Backed up to: {backup}")

        shutil.copy(template_local_settings, local_settings_file)
        print(f"✅ Created: {local_settings_file}")

    # Process CLAUDE.md
    claude_md_file = claude_dir / "CLAUDE.md"
    template_claude_md = template_dir / "CLAUDE.md.template"

    if claude_md_file.exists() and not force:
        # Smart merge - add or update ruff section
        print(f"📝 Updating existing: {claude_md_file}")

        with open(template_claude_md) as f:
            template_content = f.read()

        with open(claude_md_file) as f:
            existing_content = f.read()

        # Markers to identify ruff section
        start_marker = "<!-- ruff-claude-hook-start -->"
        end_marker = "<!-- ruff-claude-hook-end -->"

        # Strip markers from template (they're already in the template file)
        # We just want the content between them
        if start_marker in template_content and end_marker in template_content:
            template_start = template_content.find(start_marker) + len(start_marker)
            template_end = template_content.find(end_marker)
            clean_template = template_content[template_start:template_end].strip()
        else:
            clean_template = template_content

        # Check if ruff section already exists
        if start_marker in existing_content and end_marker in existing_content:
            # Replace existing section (keep existing markers)
            start_idx = existing_content.find(start_marker) + len(start_marker)
            end_idx = existing_content.find(end_marker)
            new_content = (
                existing_content[:start_idx]
                + f"\n\n{clean_template}\n\n"
                + existing_content[end_idx:]
            )
            print("   ✅ Ruff section updated")
        else:
            # Add new section with markers
            new_content = (
                f"{existing_content}\n\n---\n\n"
                f"{start_marker}\n\n{clean_template}\n\n{end_marker}\n"
            )
            print("   ✅ Ruff section added")

        with open(claude_md_file, "w") as f:
            f.write(new_content)

    else:
        # Create from template
        if claude_md_file.exists() and force:
            backup = claude_md_file.with_suffix(".md.backup")
            shutil.copy(claude_md_file, backup)
            print(f"   💾 Backed up to: {backup}")

        shutil.copy(template_claude_md, claude_md_file)
        print(f"✅ Created: {claude_md_file}")

    # Success message
    print("\n✅ Ruff hook initialized successfully!")
    print("\nNext steps:")
    print("  1. Review .claude/settings.json to ensure hook is configured")
    print("  2. Open this project in Claude Code")
    print("  3. Edit a Python file - the hook will run automatically")
    print("\nTo update: ruff-claude-hook init --force")

    return 0
