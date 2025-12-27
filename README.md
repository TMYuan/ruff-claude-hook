# ruff-claude-hook

Automatic [ruff](https://github.com/astral-sh/ruff) linting and formatting hook for [Claude Code](https://claude.com/claude-code).

## Features

- ✅ **Install once, use everywhere** - Global installation works across all projects
- ✅ **Automatic linting** - Runs after every Python file edit in Claude Code
- ✅ **Smart merging** - Preserves existing Claude Code settings
- ✅ **Zero configuration** - Works out of the box
- ✅ **Easy updates** - Update once, all projects benefit

## Installation

```bash
# Install the hook package (includes ruff automatically)
uv tool install ruff-claude-hook

# Verify installation
ruff-claude-hook check
```

## Usage

### Initialize in a Project

Navigate to your Python project and run:

```bash
cd ~/my-python-project
ruff-claude-hook init
```

This creates or updates:
- `.claude/settings.json` - Hook configuration
- `.claude/settings.local.json` - Permissions
- `.claude/CLAUDE.md` - Instructions for Claude

### How It Works

1. Open your project in Claude Code
2. Ask Claude to edit any Python file
3. The hook runs automatically after each edit
4. Claude sees the results and fixes any errors

### Example Session

```
You: "Add logging to api.py"

Claude: [Edits api.py]
✅ Ruff checks passed: api.py

Claude: "Added logging to api.py. All code quality checks passed."
```

If there are errors:

```
You: "Add a new function to utils.py"

Claude: [Edits utils.py]
❌ Ruff errors in utils.py:
utils.py:45:5: F841 Local variable 'result' is assigned to but never used

Claude: [Reads file, fixes the error, edits again]
✅ Ruff checks passed: utils.py

Claude: "Added the function. Fixed unused variable issue."
```

## Configuration

### Per-Project Customization

Customize ruff behavior in your project's `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100  # Default: 88

[tool.ruff.lint]
select = ["E", "W", "F"]  # Choose your rules
ignore = ["E501"]  # Ignore specific rules
```

### Force Overwrite

To replace existing settings (creates backups):

```bash
ruff-claude-hook init --force
```

## Updating

```bash
# Update the hook package
uv tool upgrade ruff-claude-hook

# All projects automatically use the new version!
```

## Commands

```bash
# Initialize hook in current project
ruff-claude-hook init

# Force overwrite (with backup)
ruff-claude-hook init --force

# Verify installation
ruff-claude-hook check

# Show version
ruff-claude-hook --version

# Short alias for all commands
rch init
rch check
```

## How the Hook Works

When Claude edits a Python file, the hook automatically:

1. **Auto-fix** - Runs `ruff check --fix` to fix common issues
2. **Format** - Runs `ruff format` to ensure PEP 8 compliance
3. **Validate** - Runs `ruff check` to verify no errors remain
4. **Report** - Shows results to Claude

If errors remain after auto-fixing, Claude will see them and fix them before continuing.

## Architecture

```
Global Installation:
~/.local/bin/ruff-claude-hook  # Command installed here

Per-Project Setup:
my-project/
├── .claude/
│   ├── settings.json           # Points to global command
│   ├── settings.local.json      # Permissions
│   └── CLAUDE.md                # Instructions for Claude
└── pyproject.toml               # Ruff configuration (optional)
```

## Requirements

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) package manager
- [Claude Code](https://claude.com/claude-code) CLI

## Troubleshooting

### Hook not running?

1. Verify installation:
   ```bash
   ruff-claude-hook check
   ```

2. Check `.claude/settings.json` contains:
   ```json
   {
     "hooks": {
       "PostToolUse": [
         {
           "matcher": "Edit",
           "hooks": [{"type": "command", "command": "ruff-claude-hook"}]
         }
       ]
     }
   }
   ```

3. Check permissions in `.claude/settings.local.json`:
   ```json
   {
     "permissions": {
       "allow": ["Bash(ruff-claude-hook:*)"]
     }
   }
   ```

### Ruff not found?

The hook package includes ruff as a dependency, so it should be installed automatically. If you still get errors:

```bash
# Reinstall the hook package
uv tool uninstall ruff-claude-hook
uv tool install ruff-claude-hook

# Verify ruff is available
ruff --version
```

### Smart merge not working?

If `ruff-claude-hook init` isn't merging with your existing settings:

```bash
# Use --force to replace (creates backups)
ruff-claude-hook init --force

# Then manually merge from backups:
.claude/settings.json.backup
.claude/settings.local.json.backup
```

## Development

```bash
# Clone the repository
git clone https://github.com/your-username/ruff-claude-hook
cd ruff-claude-hook

# Install in development mode
uv tool install .

# Run tests
uv run pytest

# Install in a test project
cd /path/to/test-project
ruff-claude-hook init
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Links

- [Claude Code Documentation](https://code.claude.com)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [uv Documentation](https://docs.astral.sh/uv/)
