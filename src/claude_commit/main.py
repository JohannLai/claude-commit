#!/usr/bin/env python3
"""
claude-commit - AI-powered git commit message generator

Analyzes your git repository changes and generates a meaningful commit message
using Claude's AI capabilities.
"""

import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
    CLINotFoundError,
    ProcessError,
)


SYSTEM_PROMPT = """You are an expert software engineer tasked with analyzing code changes and writing excellent git commit messages.

Your goal: Generate a clear, accurate, and meaningful commit message that captures the essence of the changes.

Available tools you can use:
- Bash: Run git commands (git diff, git status, git log, etc.) and other shell commands
- Read: Read any file in the repository to understand context
- Grep: Search for patterns across files to understand relationships
- Glob: Find files matching patterns

Analysis approach (you decide what's necessary):
1. Start by examining what files changed (git status, git diff)
2. For significant changes, READ the modified files to understand:
   - The purpose and context of changed functions/classes
   - How the changes fit into the larger codebase
   - The intent behind the modifications
3. Search for related code (grep) to understand dependencies and impacts
4. Check git history if needed to understand the change trajectory
5. Consider the scope: is this a feature, fix, refactor, docs, chore, etc.?

Commit message guidelines:
- First line: < 50 chars, imperative mood, conventional commits format (feat:, fix:, docs:, refactor:, test:, chore:, style:, perf:)
- Be specific and meaningful (avoid vague terms like "update", "change", "modify")
- Focus on WHAT changed and WHY (the intent), not HOW (implementation details)
- If multiple logical changes, use multi-line format with bullet points
- Base your message on deep understanding, not just diff surface analysis

Examples of excellent commit messages:
- "feat: add JWT-based authentication with refresh token support"
- "fix: prevent memory leak in connection pool by closing idle connections"
- "refactor: extract user validation logic into separate service"
- "perf: optimize database queries by adding composite index on user_email"

At the end of your analysis, output your final commit message in this format:

COMMIT_MESSAGE:
<your commit message here>

Everything between COMMIT_MESSAGE: and the end will be used as the commit message.
"""


async def generate_commit_message(
    repo_path: Optional[Path] = None,
    staged_only: bool = True,
    verbose: bool = False,
    max_diff_lines: int = 500,
) -> Optional[str]:
    """
    Generate a commit message based on current git changes.

    Args:
        repo_path: Path to git repository (defaults to current directory)
        staged_only: Only analyze staged changes (git diff --cached)
        verbose: Print detailed information
        max_diff_lines: Maximum number of diff lines to analyze

    Returns:
        Generated commit message or None if failed
    """
    repo_path = repo_path or Path.cwd()

    if verbose:
        print(f"🔍 Analyzing repository: {repo_path}")
        print(f"📝 Mode: {'staged changes only' if staged_only else 'all changes'}")

    # Build the analysis prompt - give AI freedom to explore
    prompt = f"""Analyze the git repository changes and generate an excellent commit message.

Context:
- Working directory: {repo_path.absolute()}
- Analysis scope: {"staged changes only (git diff --cached)" if staged_only else "all uncommitted changes (git diff)"}
- You have access to: Bash, Read, Grep, and Glob tools

Your task:
1. Investigate the changes thoroughly. Use whatever tools and commands you need.
2. Understand the INTENT and IMPACT of the changes, not just the surface-level diff.
3. Read relevant files to understand context and purpose.
4. Generate a commit message that accurately reflects what changed and why.

Recommendations (not requirements - use your judgment):
- Start with `git status` and `git diff {"--cached" if staged_only else ""}` to see what changed
- For non-trivial changes, READ the modified files to understand their purpose
- Use grep to find related code or understand how functions are used
- Consider the broader context of the codebase

When you're confident you understand the changes, output your commit message in this exact format:

COMMIT_MESSAGE:
<your commit message>

Everything after "COMMIT_MESSAGE:" will be extracted as the final commit message.
Begin your analysis now.
"""
    try:
        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=["Bash", "Read", "Grep", "Glob"],
            permission_mode="acceptEdits",
            cwd=str(repo_path.absolute()),
            max_turns=10
        )

        if verbose:
            print("🤖 Claude is analyzing your changes...")

        commit_message = None
        all_text = []

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text = block.text.strip()
                        all_text.append(text)
                        if verbose and text:
                            print(f"💭 {text}")

            elif isinstance(message, ResultMessage):
                if verbose:
                    if message.total_cost_usd:
                        print(f"💰 Cost: ${message.total_cost_usd:.4f}")
                    print(f"⏱️  Duration: {message.duration_ms / 1000:.2f}s")
                    print(f"🔄 Turns: {message.num_turns}")

                if not message.is_error:
                    # Extract commit message from COMMIT_MESSAGE: marker
                    full_response = "\n".join(all_text)
                    
                    # Look for COMMIT_MESSAGE: marker
                    if "COMMIT_MESSAGE:" in full_response:
                        # Extract everything after COMMIT_MESSAGE:
                        parts = full_response.split("COMMIT_MESSAGE:", 1)
                        if len(parts) > 1:
                            commit_message = parts[1].strip()
                    else:
                        # Fallback: try to extract the last meaningful text block
                        # Skip explanatory text and get the actual commit message
                        for text in reversed(all_text):
                            text = text.strip()
                            if text and not any(
                                text.lower().startswith(prefix)
                                for prefix in ["let me", "i'll", "i will", "now i", "first", "i can see"]
                            ):
                                commit_message = text
                                break
                    
                    # Clean up markdown code blocks if present
                    if commit_message:
                        lines = commit_message.split("\n")
                        cleaned_lines = []
                        in_code_block = False
                        
                        for line in lines:
                            if line.strip().startswith("```"):
                                in_code_block = not in_code_block
                                continue
                            if not in_code_block and line.strip():
                                cleaned_lines.append(line.rstrip())
                        
                        commit_message = "\n".join(cleaned_lines).strip()

        return commit_message

    except CLINotFoundError:
        print("❌ Error: Claude Code CLI not found.", file=sys.stderr)
        print("📦 Please install it: npm install -g @anthropic-ai/claude-code", file=sys.stderr)
        return None
    except ProcessError as e:
        print(f"❌ Process error: {e}", file=sys.stderr)
        if e.stderr:
            print(f"   stderr: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if verbose:
            import traceback

            traceback.print_exc()
        return None


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate AI-powered git commit messages using Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate commit message for staged changes
  claude-commit

  # Generate message for all changes (staged + unstaged)
  claude-commit --all

  # Show verbose output with analysis details
  claude-commit --verbose

  # Generate message and copy to clipboard (requires pbcopy/xclip)
  claude-commit --copy

  # Automatically commit with generated message
  claude-commit --commit

  # Preview without committing
  claude-commit --preview
        """,
    )

    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Analyze all changes, not just staged ones",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed analysis and processing information",
    )
    parser.add_argument(
        "-p",
        "--path",
        type=Path,
        default=None,
        help="Path to git repository (defaults to current directory)",
    )
    parser.add_argument(
        "--max-diff-lines",
        type=int,
        default=500,
        help="Maximum number of diff lines to analyze (default: 500)",
    )
    parser.add_argument(
        "-c",
        "--commit",
        action="store_true",
        help="Automatically commit with the generated message",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy the generated message to clipboard",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Just preview the message without any action",
    )

    args = parser.parse_args()

    # Run async function
    try:
        commit_message = asyncio.run(
            generate_commit_message(
                repo_path=args.path,
                staged_only=not args.all,
                verbose=args.verbose,
                max_diff_lines=args.max_diff_lines,
            )
        )
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user", file=sys.stderr)
        sys.exit(130)

    if not commit_message:
        print("❌ Failed to generate commit message", file=sys.stderr)
        sys.exit(1)

    # Display the generated message
    print("\n" + "=" * 60)
    print("📝 Generated Commit Message:")
    print("=" * 60)
    print(commit_message)
    print("=" * 60)

    # Handle different output modes
    if args.preview:
        print("\n✅ Preview complete (no action taken)")
        return

    if args.copy:
        try:
            import subprocess
            import platform

            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run("pbcopy", input=commit_message.encode(), check=True)
                print("\n✅ Commit message copied to clipboard!")
            elif system == "Linux":
                subprocess.run("xclip -selection clipboard", input=commit_message.encode(), shell=True, check=True)
                print("\n✅ Commit message copied to clipboard!")
            else:
                print("\n⚠️  Clipboard copy not supported on this platform", file=sys.stderr)
        except Exception as e:
            print(f"\n⚠️  Failed to copy to clipboard: {e}", file=sys.stderr)

    if args.commit:
        try:
            import subprocess

            # Confirm before committing
            response = input("\n❓ Commit with this message? [y/N]: ")
            if response.lower() != "y":
                print("❌ Commit cancelled")
                return

            # Execute git commit
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True,
                text=True,
                check=True,
            )
            print("\n✅ Successfully committed!")
            if result.stdout:
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Failed to commit: {e}", file=sys.stderr)
            if e.stderr:
                print(e.stderr, file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error during commit: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Default: just show the command
        print("\n💡 To commit with this message, run:")
        # Escape single quotes in the message for shell
        escaped_message = commit_message.replace("'", "'\\''")
        print(f"   git commit -m '{escaped_message}'")
        print("\nOr use: claude-commit --commit")


if __name__ == "__main__":
    main()

