# Git Hooks for claude-commit

This directory contains git hook templates that you can use to integrate `claude-commit` into your git workflow.

## Available Hooks

### prepare-commit-msg

Automatically generates a commit message using Claude AI when you run `git commit`.

**Installation:**

```bash
# Copy the hook to your .git/hooks directory
cp hooks/prepare-commit-msg .git/hooks/prepare-commit-msg
chmod +x .git/hooks/prepare-commit-msg
```

**Usage:**

After installation, simply run:
```bash
git add .
git commit
```

The hook will:
1. Analyze your staged changes
2. Generate a commit message using Claude
3. Pre-fill the commit message in your editor
4. You can still edit or modify the message before confirming

**To disable temporarily:**

```bash
git commit --no-verify
```

## Other Hook Ideas

### commit-msg (Validation)

Validates commit messages follow conventional commits format:

```bash
#!/bin/bash
# Validate commit message format

COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Check if message follows conventional commits
if ! echo "$COMMIT_MSG" | grep -qE "^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+"; then
    echo "❌ Commit message must follow conventional commits format:"
    echo "   type(scope?): description"
    echo ""
    echo "   Examples:"
    echo "   - feat: add new feature"
    echo "   - fix: resolve bug in parser"
    echo "   - docs: update README.md"
    exit 1
fi
```

### pre-commit (Auto-generate if no message)

You can also create a workflow where `claude-commit` runs as part of pre-commit checks.

## Notes

- Git hooks are local to your repository and not tracked by git
- Each developer needs to install hooks manually
- Consider using tools like [Husky](https://github.com/typicode/husky) for team-wide hook management

