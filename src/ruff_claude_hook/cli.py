"""Command-line interface for ruff-claude-hook."""

import argparse
import shutil
import sys

from . import __version__
from .hook import main as hook_main
from .init import init_project


def check_installation():
    """Verify ruff-claude-hook installation.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("🔍 Checking ruff-claude-hook installation...\n")

    # Check if ruff is available
    ruff_path = shutil.which("ruff")
    if ruff_path:
        print(f"✅ ruff found: {ruff_path}")
        import subprocess

        result = subprocess.run(  # noqa: S603
            ["ruff", "--version"],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"   Version: {result.stdout.strip()}")
    else:
        print("❌ ruff not found")
        print("   Install with: uv tool install ruff")
        return 1

    # Check if ruff-claude-hook is available
    hook_path = shutil.which("ruff-claude-hook")
    if hook_path:
        print(f"✅ ruff-claude-hook found: {hook_path}")
        print(f"   Version: {__version__}")
    else:
        print("⚠️  ruff-claude-hook command not found in PATH")
        return 1

    print("\n✅ Installation looks good!")
    print("\nNext steps:")
    print("  1. cd <your-project>")
    print("  2. ruff-claude-hook init")
    print("  3. Open project in Claude Code")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Automatic ruff linting and formatting hook for Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize hook in current project
  ruff-claude-hook init

  # Force overwrite existing configuration
  ruff-claude-hook init --force

  # Verify installation
  ruff-claude-hook check

  # Show version
  ruff-claude-hook --version
        """,
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"ruff-claude-hook {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser(
        "init", help="Initialize ruff hook in current project"
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing files (creates backups)",
    )

    # Check command
    subparsers.add_parser("check", help="Verify installation")

    args = parser.parse_args()

    # Handle commands
    if args.command == "init":
        return init_project(force=args.force)
    elif args.command == "check":
        return check_installation()
    elif args.command is None:
        # No command - run as hook (called by Claude Code)
        return hook_main()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
