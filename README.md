# claude-commit

🤖 AI-powered git commit message generator using Claude Agent SDK

## Overview

`claude-commit` is an **agentic AI tool** that deeply analyzes your git repository changes and generates meaningful, best-practice commit messages using Claude's AI capabilities. Unlike simple diff-to-text tools, Claude autonomously explores your codebase, reads relevant files, and understands the context and intent behind your changes.

## Features

- 🤖 **Agentic Analysis**: Claude autonomously decides what to investigate - reading files, searching code, understanding context
- 🔍 **Deep Code Understanding**: Goes beyond surface-level diffs to understand purpose, relationships, and impact
- 📋 **Best Practices**: Follows conventional commits format and git commit best practices
- 🎯 **Intent-Based Messages**: Captures WHAT changed and WHY, not just HOW
- 🔧 **Flexible Options**: Analyze staged changes or all changes
- 📝 **Multiple Output Modes**: Preview, copy to clipboard, or auto-commit
- 🚀 **Zero External Dependencies**: Uses only Claude's built-in tools (Bash, Read, Grep, Glob)

## Installation

### Prerequisites

1. **Python 3.10+**
2. **Node.js**
3. **Claude Code CLI** - Required for the SDK to work:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

### Install claude-commit

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-commit.git
cd claude-commit

# Install in development mode
pip install -e .

# Or install from PyPI (once published)
pip install claude-commit
```

## Usage

### Basic Usage

```bash
# Analyze staged changes and generate commit message
claude-commit

# Analyze all changes (staged + unstaged)
claude-commit --all

# Show verbose output with analysis details
claude-commit --verbose
```

### Advanced Usage

```bash
# Preview the message without any action
claude-commit --preview

# Copy generated message to clipboard
claude-commit --copy

# Automatically commit with the generated message
claude-commit --commit

# Specify a different repository path
claude-commit --path /path/to/repo

# Limit diff analysis (useful for large changes)
claude-commit --max-diff-lines 300
```

### Workflow Examples

**Standard workflow:**
```bash
# Stage your changes
git add .

# Generate commit message
claude-commit

# Review and commit manually
git commit -m "feat: add user authentication module"
```

**Quick commit workflow:**
```bash
# Stage changes and auto-commit
git add .
claude-commit --commit
```

**Copy to clipboard workflow:**
```bash
# Generate and copy message
claude-commit --copy

# Then paste in your git client or IDE
```

## Command Line Options

| Option               | Description                                            |
| -------------------- | ------------------------------------------------------ |
| `-a, --all`          | Analyze all changes, not just staged ones              |
| `-v, --verbose`      | Show detailed analysis and processing information      |
| `-p, --path PATH`    | Path to git repository (defaults to current directory) |
| `--max-diff-lines N` | Maximum number of diff lines to analyze (default: 500) |
| `-c, --commit`       | Automatically commit with the generated message        |
| `--copy`             | Copy the generated message to clipboard                |
| `--preview`          | Just preview the message without any action            |

## How It Works (Agentic Approach)

Unlike traditional tools that just format git diffs, `claude-commit` uses an **agentic approach** where Claude autonomously decides how to analyze your changes:

1. **Initial Discovery**: Claude starts by running `git status` and `git diff` to see what changed
2. **Autonomous Investigation**: Claude decides what additional context is needed:
   - 📖 **Reads modified files** to understand their purpose and structure
   - 🔍 **Searches the codebase** (grep) to find related functions, classes, or dependencies
   - 🌳 **Explores file structure** (glob) to understand the project organization
   - 📜 **Checks git history** to understand the change trajectory
3. **Deep Understanding**: Claude analyzes:
   - The *intent* behind the changes (not just what lines changed)
   - How changes fit into the larger codebase
   - The impact and relationships with other code
4. **Generate Message**: Creates a commit message that captures:
   - **WHAT** changed (the functionality)
   - **WHY** it changed (the intent/purpose)
   - Following best practices: imperative mood, conventional commits, clear and concise

**Example of Claude's autonomous analysis:**
```
1. Sees changes in authentication.py
2. Reads authentication.py to understand the auth system
3. Greps for "JWT" to see how tokens are used elsewhere
4. Reads related files like user_model.py for context
5. Generates: "feat: add JWT-based authentication with refresh token support"
```

## Commit Message Examples

**Feature addition:**
```
feat: add user authentication with JWT tokens

Implement secure authentication system using JSON Web Tokens.
Includes login, logout, and token refresh endpoints.
```

**Bug fix:**
```
fix: resolve memory leak in connection pool

Connection objects were not being properly released back to the pool
after failed queries, causing gradual memory exhaustion.
```

**Documentation:**
```
docs: update API documentation for v2 endpoints

Add examples for new pagination parameters and response formats.
Include migration guide from v1 to v2.
```

## Configuration

### Claude Agent Options

The tool uses these Claude Agent SDK options by default:

```python
ClaudeAgentOptions(
    system_prompt=SYSTEM_PROMPT,  # Expert commit message writer
    allowed_tools=["Bash", "Read", "Grep", "Glob"],
    permission_mode="acceptEdits",
    max_turns=10,
)
```

### Customization

You can customize the behavior by modifying `src/claude_commit/main.py`:

- **SYSTEM_PROMPT**: Adjust the AI's instructions for commit messages
- **max_turns**: Change how many iterations Claude can use
- **allowed_tools**: Add or remove tools Claude can use

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-commit.git
cd claude-commit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Troubleshooting

### "Claude Code not found" Error

If you see this error:
```
❌ Error: Claude Code CLI not found.
📦 Please install it: npm install -g @anthropic-ai/claude-code
```

**Solution**: Install the Claude Code CLI:
```bash
npm install -g @anthropic-ai/claude-code
```

### "No changes detected" Error

**Solution**: Make sure you have either:
- Staged changes: `git add <files>`
- Use `--all` flag to analyze unstaged changes: `claude-commit --all`

### Large Diffs Taking Too Long

**Solution**: Limit the analysis scope:
```bash
claude-commit --max-diff-lines 200
```

## API Usage

You can also use `claude-commit` as a Python library:

```python
from claude_commit import generate_commit_message
from pathlib import Path
import asyncio

async def example():
    message = await generate_commit_message(
        repo_path=Path("/path/to/repo"),
        staged_only=True,
        verbose=True
    )
    
    if message:
        print(f"Generated: {message}")

asyncio.run(example())
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Claude Agent SDK](https://docs.anthropic.com/en/docs/claude-code/agent-sdk)
- Inspired by best practices from the git community
- Thanks to Anthropic for providing Claude AI

## Related Projects

- [Claude Agent SDK](https://github.com/anthropics/claude-code-sdk) - Official SDK for building Claude agents
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message convention

## Support

- 📖 [Documentation](https://github.com/yourusername/claude-commit/wiki)
- 🐛 [Issue Tracker](https://github.com/yourusername/claude-commit/issues)
- 💬 [Discussions](https://github.com/yourusername/claude-commit/discussions)

---

Made with ❤️ using Claude AI

