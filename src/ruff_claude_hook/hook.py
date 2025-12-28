"""PostToolUse hook for automatic ruff linting and formatting.

This hook runs after Claude edits Python files:
1. ruff check --fix - Auto-fixes linting errors
2. ruff format - Formats code to PEP 8
3. ruff check - Validates no errors remain

If unfixable errors remain, displays them clearly for Claude to fix.
"""

import json
import os
import subprocess
import sys


def main():
    """Execute ruff workflow on edited Python files."""
    # 1. Read tool input from stdin
    try:
        stdin_content = sys.stdin.read()
        data = json.loads(stdin_content)
    except json.JSONDecodeError:
        # Not valid JSON, skip silently
        return 0

    # 2. Check if this is an Edit tool call
    tool_name = data.get("tool_name", "")
    if tool_name != "Edit":
        return 0

    # 3. Extract file path from tool input
    # Support both "parameters" (new format) and "tool_input" (legacy)
    file_path = data.get("parameters", {}).get("file_path") or data.get(
        "tool_input", {}
    ).get("file_path", "")

    # 4. Validate file
    if not file_path:
        return 0

    if not file_path.endswith(".py"):
        return 0

    if not os.path.exists(file_path):
        return 0

    filename = os.path.basename(file_path)

    # 5. Run ruff workflow with error handling
    try:
        # Phase 1: Auto-fix linting errors
        subprocess.run(  # noqa: S603
            ["ruff", "check", "--fix", file_path],  # noqa: S607
            capture_output=True,
            text=True,
        )

        # Phase 2: Format code
        subprocess.run(  # noqa: S603
            ["ruff", "format", file_path],  # noqa: S607
            capture_output=True,
            text=True,
        )

        # Phase 3: Final validation
        check_result = subprocess.run(  # noqa: S603
            ["ruff", "check", file_path],  # noqa: S607
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        # Handle subprocess errors
        error_msg = f"Error running ruff: {e}"
        output = {
            "continue": True,
            "systemMessage": error_msg,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": error_msg,
            },
        }
        print(json.dumps(output))
        return 1

    # 7. Report results via JSON with systemMessage
    if check_result.returncode == 0:
        # Success case - brief message
        success_msg = f"✅ Ruff checks passed: {filename}"
        output = {
            "continue": True,
            "systemMessage": success_msg,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": success_msg,
            },
        }
        print(json.dumps(output))
        return 0
    else:
        # Error case - detailed message for Claude
        error_details = check_result.stdout.strip()
        error_msg = (
            f"❌ Ruff errors in {filename}:\n\n{error_details}\n\n"
            "⚠️  Claude: You MUST fix these errors before continuing"
        )

        output = {
            "continue": True,  # Let Claude continue and fix the errors
            "systemMessage": error_msg,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": error_msg,
            },
        }
        print(json.dumps(output))
        return 1


if __name__ == "__main__":
    sys.exit(main())
