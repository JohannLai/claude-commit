# claude-commit [![PyPI version](https://badge.fury.io/py/claude-commit.svg)](https://badge.fury.io/py/claude-commit)

🤖 AI-powered git commit message generator using Claude Agent SDK and Claude Code CLI

## What is this?

`claude-commit` uses Claude AI to analyze your code changes and write meaningful commit messages. Claude reads your files, understands the context, and generates commit messages following best practices.

## Installation

### Prerequisites

- Python 3.10+
- Node.js
- Git

### Recommended: pipx (for CLI tools)

`pipx` is the **best way to install Python CLI tools**. It creates isolated environments automatically:

```bash
# 1. Install pipx
brew install pipx              # macOS
# or
pip install --user pipx        # Linux/Windows
pipx ensurepath

# 2. Install Claude Code CLI (required)
npm install -g @anthropic-ai/claude-code

# 3. Install claude-commit
pipx install claude-commit
```

### Alternative: pip

If you prefer pip, use one of these methods:

**Option 1: User installation (no admin rights needed)**
```bash
# Install to user directory
pip install --user claude-commit

# Make sure ~/.local/bin is in your PATH
export PATH="$HOME/.local/bin:$PATH"
```

**Option 2: Virtual environment**
```bash
python3 -m venv ~/.venvs/claude-commit
source ~/.venvs/claude-commit/bin/activate
pip install claude-commit
```

### Authentication

`claude-commit` supports two ways to authenticate with Claude:

**Option 1: [Official Claude Code Login](https://docs.claude.com/en/docs/claude-code/quickstart#step-2%3A-log-in-to-your-account) (Recommended)**

**Option 2: Custom API Endpoint (Environment Variables)**

For custom Claude API endpoints or proxies, set these environment variables:

```bash
# Required: Set custom endpoint and credentials
export ANTHROPIC_BASE_URL="https://your-endpoint.com/api/v1"
export ANTHROPIC_AUTH_TOKEN="your-auth-token"

# Optional: Specify custom model name
export ANTHROPIC_MODEL="your-model-name"

# Then use claude-commit normally
claude-commit --commit
```

Add these to your `~/.zshrc` or `~/.bashrc` to persist across sessions.

## Usage

### Basic Commands

```bash
# Generate commit message (default: staged changes only)
claude-commit

# Auto-commit with generated message
claude-commit --commit

# Include all changes (staged + unstaged)
claude-commit --all

# Copy message to clipboard
claude-commit --copy
```

### Common Options

| Option               | Description                        |
| -------------------- | ---------------------------------- |
| `-a, --all`          | Include unstaged changes           |
| `-c, --commit`       | Auto-commit with generated message |
| `--copy`             | Copy message to clipboard          |
| `--preview`          | Preview message only               |
| `-v, --verbose`      | Show detailed analysis             |
| `-p, --path PATH`    | Specify repository path            |
| `--max-diff-lines N` | Limit diff lines (default: 500)    |

## Aliases

Create shortcuts for common commands:

### Install Shell Aliases

```bash
# Install to your shell config
claude-commit alias install

# Activate in current terminal. Very important!
source ~/.zshrc    # zsh
source ~/.bashrc   # bash
```

### Default Aliases

| Alias   | Command                        | Description         |
| ------- | ------------------------------ | ------------------- |
| `ccc`   | `claude-commit --commit`       | Quick commit        |
| `ccp`   | `claude-commit --preview`      | Preview message     |
| `cca`   | `claude-commit --all`          | Include all changes |
| `ccac`  | `claude-commit --all --commit` | Commit all changes  |
| `ccopy` | `claude-commit --copy`         | Copy to clipboard   |

After installation, just use:
```bash
git add .
ccc  # analyzes and commits
```

### Custom Aliases

```bash
# Create your own aliases
claude-commit alias set quick --all --commit
claude-commit alias list
claude-commit alias unset quick
```

## How It Works

Claude autonomously analyzes your changes:

1. **Reads** your modified files to understand context
2. **Searches** the codebase for related code
3. **Understands** the intent and impact of changes
4. **Generates** a clear commit message following conventions

**Example:**
```
feat: add JWT authentication

Implement secure authentication system with token refresh.
Includes login, logout, and session management.
```

## Examples

### Typical Workflow

```bash
# Make changes
git add .

# Preview message
claude-commit --preview

# Commit if satisfied
claude-commit --commit
```

### With Aliases

```bash
# Make changes
git add .

# Quick commit
ccc
```

### Large Changes

```bash
# Limit analysis for faster results
claude-commit --max-diff-lines 200 --commit
```

## Configuration

Configuration files:
- Aliases: `~/.claude-commit/config.json`
- Shell integration: `~/.zshrc`, `~/.bashrc`, or `$PROFILE`

## Platform Support

| Platform | Status | Shells               |
| -------- | ------ | -------------------- |
| macOS    | ✅      | zsh, bash, fish      |
| Linux    | ✅      | bash, zsh, fish      |
| Windows  | ✅      | PowerShell, Git Bash |

**Windows PowerShell** first-time setup:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Troubleshooting

### Fatal error in message reader: Command failed with exit code 1 (exit code: 1)

```
Fatal error in message reader: Command failed with exit code 1 (exit code: 1)
Error output: Check stderr output for details
Traceback (most recent call last):
```

**Solution**: This error means you haven't authenticated with Claude. Choose one method:

**Method A: Official Claude Code login (recommended)**
```bash
claude
```

**Method B: Set custom API endpoint**
```bash
export ANTHROPIC_BASE_URL="https://your-endpoint.com/api/v1"
export ANTHROPIC_AUTH_TOKEN="your-auth-token"
# model name (optional)
export ANTHROPIC_MODEL="your-model-name"

# Add to ~/.zshrc or ~/.bashrc to persist
echo 'export ANTHROPIC_BASE_URL="https://your-endpoint.com/api/v1"' >> ~/.zshrc
echo 'export ANTHROPIC_AUTH_TOKEN="your-auth-token"' >> ~/.zshrc
```

### "externally-managed-environment" error (macOS/Linux)

If you see this error when using `pip install`:

```
error: externally-managed-environment
```

**Solution**: Use `pipx` (recommended for CLI tools):
```bash
brew install pipx
pipx install claude-commit
```

Or use `pip install --user`:
```bash
pip install --user claude-commit
```

**Why this happens**: Modern Python installations (Python 3.11+) protect the system Python to prevent conflicts. This is not a bug in `claude-commit`.

### Claude Code not found

```bash
npm install -g @anthropic-ai/claude-code
```

### No changes detected

```bash
git add .              # stage changes
# or
claude-commit --all    # include unstaged
```

### Analysis too slow

```bash
claude-commit --max-diff-lines 200
```

### Command not found after installation

If `claude-commit` is not found after installation:

**With pipx:**
```bash
pipx ensurepath
# Restart your terminal
```

**With pip --user:**
```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
source ~/.zshrc  # or ~/.bashrc
```

### Aliases not working

```bash
claude-commit alias install
source ~/.zshrc  # or ~/.bashrc
```

## Development

```bash
# Clone and setup
git clone https://github.com/JohannLai/claude-commit.git
cd claude-commit
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file

## Links

- [Claude Agent SDK](https://docs.anthropic.com/en/docs/claude-code/agent-sdk)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Repository](https://github.com/JohannLai/claude-commit)
- [PyPI Package](https://pypi.org/project/claude-commit/)
- [Issue Tracker](https://github.com/JohannLai/claude-commit/issues)

---

Made with ❤️ by [Johann Lai](https://x.com/programerjohann)
