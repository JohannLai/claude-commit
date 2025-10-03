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
import time

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import pyperclip

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

from .config import Config, resolve_alias

console = Console()


SYSTEM_PROMPT = """You are an expert software engineer tasked with analyzing code changes and writing excellent git commit messages.

Your goal: Generate a clear, accurate, and meaningful commit message that captures the essence of the changes.

Available tools you can use:
- Bash: Run git commands (git diff, git status, git log, etc.) and other shell commands
- Read: Read any file in the repository to understand context
- Grep: Search for patterns across files to understand relationships
- Glob: Find files matching patterns

Analysis approach (you decide what's necessary):
1. IMPORTANT: First check recent commit history (git log -10 --oneline or git log -10 --pretty=format:"%s") to understand the existing commit message style
   - Check if the project uses gitmoji (emojis like 🎉, ✨, 🐛, etc.)
   - Check if messages are in Chinese, English, or other languages
   - Check if they use conventional commits (feat:, fix:, etc.) or other formats
   - Note any specific patterns or conventions used
2. Examine what files changed (git status, git diff)
3. For significant changes, READ the modified files to understand:
   - The purpose and context of changed functions/classes
   - How the changes fit into the larger codebase
   - The intent behind the modifications
4. Search for related code (grep) to understand dependencies and impacts
5. Consider the scope: is this a feature, fix, refactor, docs, chore, etc.?

Commit message guidelines:
- **FOLLOW THE EXISTING FORMAT**: Match the style, language, and conventions used in recent commits
- If no clear pattern exists in history, use conventional commits format (feat:, fix:, docs:, refactor:, test:, chore:, style:, perf:)
- First line: < 50 chars (or follow existing convention), imperative mood, summarize the main change
- **IMPORTANT**: Use multi-line format with bullet points for detailed changes:
  ```
  type: brief summary (< 50 chars)
  
  - First change detail
  - Second change detail
  - Third change detail
  ```
- Be specific and meaningful (avoid vague terms like "update", "change", "modify")
- Focus on WHAT changed and WHY (the intent), not HOW (implementation details)
- Base your message on deep understanding, not just diff surface analysis

Examples of excellent commit messages (multi-line format):

Conventional commits style:
```
feat: add user authentication system

- Implement JWT-based authentication with refresh tokens
- Add login and registration endpoints
- Create user session management
- Add password hashing with bcrypt
```

```
fix: prevent memory leak in connection pool

- Close idle connections after timeout
- Add connection limit configuration
- Improve error handling for failed connections
```

With gitmoji:
```
✨ add user authentication system

- Implement JWT-based authentication with refresh tokens
- Add login and registration endpoints
- Create user session management
```

In Chinese:
```
新增：用户认证系统

- 实现基于 JWT 的身份验证和刷新令牌
- 添加登录和注册接口
- 创建用户会话管理
```

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
        console.print(f"[blue]🔍 Analyzing repository:[/blue] {repo_path}")
        console.print(f"[blue]📝 Mode:[/blue] {'staged changes only' if staged_only else 'all changes'}")

    # Build the analysis prompt - give AI freedom to explore
    prompt = f"""Analyze the git repository changes and generate an excellent commit message.

Context:
- Working directory: {repo_path.absolute()}
- Analysis scope: {"staged changes only (git diff --cached)" if staged_only else "all uncommitted changes (git diff)"}
- You have access to: Bash, Read, Grep, and Glob tools

Your task:
1. **FIRST**: Check the recent commit history (e.g., `git log -3 --oneline` or `git log -3 --pretty=format:"%s"`) to understand the commit message format/style used in this project
   - Does it use gitmoji? (emojis like ✨, 🐛, ♻️, etc.)
   - What language? (Chinese, English, etc.)
   - What format? (conventional commits, custom format, etc.)
   - **IMPORTANT**: You MUST follow the same style/format/language as the existing commits
2. Investigate the changes thoroughly. Use whatever tools and commands you need.
3. Understand the INTENT and IMPACT of the changes, not just the surface-level diff.
4. Read relevant files to understand context and purpose.
5. Generate a commit message in **MULTI-LINE FORMAT** with:
   - First line: brief summary (< 50 chars)
   - Empty line
   - Bullet points (starting with "-") for detailed changes
   Example:
   ```
   fix: correct formatting issue
   
   - Preserve empty lines in commit messages
   - Update prompt to require multi-line format
   - Add examples showing proper structure
   ```

Recommendations (not requirements - use your judgment):
- Start with `git log -3 --oneline` to check the commit message style
- Then use `git status` and `git diff {"--cached" if staged_only else ""}` to see what changed
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
            console.print("[cyan]🔍 Claude is analyzing your changes...[/cyan]\n")
        else:
            console.print("[cyan]🔍 Analyzing changes...[/cyan]\n")

        commit_message = None
        all_text = []
        
        # Use rich progress for spinner
        progress = None
        task_id = None
        spinner_started = False

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                # Stop spinner when we get content
                if progress is not None and task_id is not None:
                    progress.stop()
                    progress = None
                    task_id = None
                    spinner_started = False
                
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text = block.text.strip()
                        all_text.append(text)
                        if verbose and text:
                            console.print(f"[dim]💭 {text}[/dim]")
                    
                    elif isinstance(block, ToolUseBlock):
                        # Show what tool Claude is using (simplified output)
                        tool_name = block.name
                        tool_input = block.input
                        
                        if tool_name == "Bash":
                            cmd = tool_input.get("command", "")
                            if verbose:
                                description = tool_input.get("description", "")
                                if description:
                                    console.print(f"  [cyan]🔧 {cmd}[/cyan]  [dim]# {description}[/dim]")
                                else:
                                    console.print(f"  [cyan]🔧 {cmd}[/cyan]")
                            else:
                                # Non-verbose: only show git commands and other important ones
                                if cmd.startswith("git "):
                                    console.print(f"  [cyan]🔧 {cmd}[/cyan]")
                                    
                        elif tool_name == "Read":
                            file_path = tool_input.get("file_path", "")
                            if file_path:
                                import os
                                try:
                                    rel_path = os.path.relpath(file_path, repo_path)
                                    if verbose:
                                        console.print(f"  [yellow]📖 Reading {rel_path}[/yellow]")
                                    else:
                                        # Show just filename for non-verbose
                                        if len(rel_path) > 45:
                                            filename = os.path.basename(rel_path)
                                            console.print(f"  [yellow]📖 {filename}[/yellow]")
                                        else:
                                            console.print(f"  [yellow]📖 {rel_path}[/yellow]")
                                except:
                                    filename = os.path.basename(file_path)
                                    console.print(f"  [yellow]📖 {filename}[/yellow]")
                                    
                        elif tool_name == "Grep":
                            pattern = tool_input.get("pattern", "")
                            path = tool_input.get("path", ".")
                            if verbose:
                                console.print(f"  [magenta]🔍 Searching for '{pattern}' in {path}[/magenta]")
                            elif pattern and len(pattern) <= 40:
                                console.print(f"  [magenta]🔍 {pattern}[/magenta]")
                                
                        elif tool_name == "Glob":
                            pattern = tool_input.get("pattern", "")
                            if pattern:
                                if verbose:
                                    console.print(f"  [blue]📁 Finding files matching {pattern}[/blue]")
                                else:
                                    console.print(f"  [blue]📁 {pattern}[/blue]")
                    
                    elif isinstance(block, ToolResultBlock):
                        # Optionally show tool results in verbose mode
                        if verbose and block.content:
                            result = str(block.content)
                            if len(result) > 200:
                                result = result[:197] + "..."
                            console.print(f"     [dim]↳ {result}[/dim]")
                
                # After processing all blocks, start spinner if no output in non-verbose mode
                # Only start spinner once, not on every message
                if not verbose and not spinner_started:
                    if progress is None:
                        progress = Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            console=console,
                            transient=True,
                        )
                        progress.start()
                        task_id = progress.add_task("⏳ Waiting for response...", total=None)
                        spinner_started = True

            elif isinstance(message, ResultMessage):
                # Stop spinner if it's running
                if progress is not None and task_id is not None:
                    progress.stop()
                    progress = None
                    task_id = None
                    spinner_started = False
                console.print("\n[green]✨ Analysis complete![/green]")
                if verbose:
                    if message.total_cost_usd:
                        console.print(f"[yellow]💰 Cost: ${message.total_cost_usd:.4f}[/yellow]")
                    console.print(f"[blue]⏱️  Duration: {message.duration_ms / 1000:.2f}s[/blue]")
                    console.print(f"[cyan]🔄 Turns: {message.num_turns}[/cyan]")

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
                            if not in_code_block:
                                cleaned_lines.append(line.rstrip())
                        
                        commit_message = "\n".join(cleaned_lines).strip()
        
        # Make sure progress is stopped before returning
        if progress is not None and task_id is not None:
            progress.stop()

        return commit_message

    except CLINotFoundError:
        # Stop progress on error
        if 'progress' in locals() and progress is not None:
            progress.stop()
        console.print("[red]❌ Error: Claude Code CLI not found.[/red]", file=sys.stderr)
        console.print("[yellow]📦 Please install it: npm install -g @anthropic-ai/claude-code[/yellow]", file=sys.stderr)
        return None
    except ProcessError as e:
        if 'progress' in locals() and progress is not None:
            progress.stop()
        console.print(f"[red]❌ Process error: {e}[/red]", file=sys.stderr)
        if e.stderr:
            console.print(f"   stderr: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        if 'progress' in locals() and progress is not None:
            progress.stop()
        console.print(f"[red]❌ Unexpected error: {e}[/red]", file=sys.stderr)
        if verbose:
            import traceback

            traceback.print_exc()
        return None


def handle_alias_command(args):
    """Handle alias management subcommands"""
    if len(args) == 0 or args[0] == "list":
        # List all aliases
        config = Config()
        aliases = config.list_aliases()
        
        if not aliases:
            print("📋 No aliases configured")
            return
        
        print("📋 Configured aliases:")
        print()
        max_alias_len = max(len(alias) for alias in aliases.keys())
        
        for alias, command in sorted(aliases.items()):
            if command:
                print(f"  {alias:<{max_alias_len}} → claude-commit {command}")
            else:
                print(f"  {alias:<{max_alias_len}} → claude-commit")
        
        print()
        print("💡 Usage: claude-commit <alias> [additional args]")
        print("   Example: claude-commit cca  (expands to: claude-commit --all)")
        print()
        print("🔧 To use aliases directly in shell (like 'ccc' instead of 'claude-commit ccc'):")
        print("   Run: claude-commit alias install")
    
    elif args[0] == "install":
        # Install shell aliases
        config = Config()
        aliases = config.list_aliases()
        
        if not aliases:
            print("📋 No aliases configured")
            return
        
        import platform
        import os
        
        # Detect shell and platform
        shell = os.environ.get("SHELL", "")
        system = platform.system()
        
        # Windows detection
        if system == "Windows":
            # Check if running in Git Bash (has SHELL env var on Windows)
            if shell and ("bash" in shell or "sh" in shell):
                # Git Bash on Windows
                rc_file = Path.home() / ".bashrc"
                shell_name = "bash (Git Bash)"
            else:
                # PowerShell (default on Windows)
                # Check for PowerShell profile
                ps_profile = os.environ.get("USERPROFILE", "")
                if ps_profile:
                    # PowerShell 7+ or Windows PowerShell
                    rc_file = Path(ps_profile) / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"
                    # Also check PowerShell 7+
                    ps7_profile = Path(ps_profile) / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
                    if ps7_profile.parent.exists():
                        rc_file = ps7_profile
                    shell_name = "powershell"
                else:
                    print("⚠️  Could not detect PowerShell profile location")
                    print()
                    print("   To manually add aliases in PowerShell, add to your $PROFILE:")
                    print()
                    for alias, command in sorted(aliases.items()):
                        if command:
                            print(f'   Set-Alias -Name {alias} -Value "claude-commit {command}"')
                        else:
                            print(f'   Set-Alias -Name {alias} -Value "claude-commit"')
                    return
        # Unix-like systems
        elif "zsh" in shell:
            rc_file = Path.home() / ".zshrc"
            shell_name = "zsh"
        elif "bash" in shell:
            rc_file = Path.home() / ".bashrc"
            # On macOS, also check .bash_profile
            if system == "Darwin":
                bash_profile = Path.home() / ".bash_profile"
                if bash_profile.exists():
                    rc_file = bash_profile
            shell_name = "bash"
        elif "fish" in shell:
            # Fish shell uses different config location
            rc_file = Path.home() / ".config" / "fish" / "config.fish"
            shell_name = "fish"
        else:
            print(f"⚠️  Unknown shell: {shell or 'not detected'}")
            print("   Supported shells: bash, zsh, fish, powershell (Windows)")
            print()
            print("   To manually add aliases, add these lines to your shell config:")
            print()
            for alias, command in sorted(aliases.items()):
                if command:
                    print(f"   alias {alias}='claude-commit {command}'")
                else:
                    print(f"   alias {alias}='claude-commit'")
            return
        
        # Generate alias commands (different syntax for PowerShell)
        if shell_name == "powershell":
            alias_lines = ["", "# claude-commit aliases (auto-generated)"]
            for alias, command in sorted(aliases.items()):
                if command:
                    # PowerShell doesn't support Set-Alias with arguments, use function instead
                    alias_lines.append(f"function {alias} {{ claude-commit {command} $args }}")
                else:
                    alias_lines.append(f"function {alias} {{ claude-commit $args }}")
            alias_lines.append("")
        else:
            # Unix-style shells (bash, zsh, fish)
            alias_lines = ["", "# claude-commit aliases (auto-generated)"]
            for alias, command in sorted(aliases.items()):
                if command:
                    alias_lines.append(f"alias {alias}='claude-commit {command}'")
                else:
                    alias_lines.append(f"alias {alias}='claude-commit'")
            alias_lines.append("")
        
        alias_block = "\n".join(alias_lines)
        
        print(f"📝 Generated shell aliases for {shell_name}:")
        print(alias_block)
        print()
        
        # Check if aliases already exist
        if rc_file.exists():
            content = rc_file.read_text()
            if "# claude-commit aliases" in content:
                print(f"⚠️  Aliases already exist in {rc_file}")
                response = input("   Replace existing aliases? [Y/n]: ").strip().lower()
                if response == "n" or response == "no":
                    print("❌ Installation cancelled")
                    return
                
                # Remove old aliases
                lines = content.split("\n")
                new_lines = []
                skip = False
                for line in lines:
                    if "# claude-commit aliases" in line:
                        skip = True
                    elif skip and (line.strip() == "" or not line.startswith("alias ")):
                        skip = False
                    
                    if not skip:
                        new_lines.append(line)
                
                content = "\n".join(new_lines)
        else:
            content = ""
        
        # Append new aliases
        new_content = content.rstrip() + alias_block + "\n"
        
        try:
            # Ensure directory exists (especially for PowerShell profile)
            rc_file.parent.mkdir(parents=True, exist_ok=True)
            
            rc_file.write_text(new_content)
            print(f"✅ Aliases installed to {rc_file}")
            print()
            
            # Show activation instructions (different for PowerShell)
            if shell_name == "powershell":
                print("📋 To activate aliases in your current PowerShell session, run:")
                print()
                print(f"   \033[1;36m. {rc_file}\033[0m")
                print()
                print("Or restart PowerShell.")
                print()
                print("💡 Note: You may need to run this first to allow script execution:")
                print("   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser")
            else:
                print("📋 To activate aliases in your current shell, run:")
                print()
                print(f"   \033[1;36msource {rc_file}\033[0m")
                print()
                print("Or copy and paste this command:")
                print(f"   \033[1;32msource {rc_file} && echo '✅ Aliases activated! Try: ccc'\033[0m")
            print()
            print("💡 Aliases will be automatically available in new terminal windows.")
        except Exception as e:
            print(f"❌ Failed to write to {rc_file}: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args[0] == "uninstall":
        # Remove shell aliases
        import platform
        import os
        
        shell = os.environ.get("SHELL", "")
        
        if "zsh" in shell:
            rc_file = Path.home() / ".zshrc"
        elif "bash" in shell:
            rc_file = Path.home() / ".bashrc"
            if platform.system() == "Darwin":
                bash_profile = Path.home() / ".bash_profile"
                if bash_profile.exists():
                    rc_file = bash_profile
        else:
            print(f"⚠️  Unknown shell: {shell}")
            return
        
        if not rc_file.exists():
            print(f"❌ {rc_file} not found")
            return
        
        content = rc_file.read_text()
        
        if "# claude-commit aliases" not in content:
            print(f"📋 No claude-commit aliases found in {rc_file}")
            return
        
        # Remove aliases block
        lines = content.split("\n")
        new_lines = []
        skip = False
        removed = False
        
        for line in lines:
            if "# claude-commit aliases" in line:
                skip = True
                removed = True
            elif skip and (line.strip() == "" or not line.startswith("alias ")):
                skip = False
            
            if not skip:
                new_lines.append(line)
        
        if removed:
            rc_file.write_text("\n".join(new_lines))
            print(f"✅ Aliases removed from {rc_file}")
            print()
            print("🔄 To apply changes, run:")
            print(f"   source {rc_file}")
            print()
            print("   Or open a new terminal window.")
        
    elif args[0] == "set":
        # Set an alias
        if len(args) < 2:
            print("❌ Error: Please provide alias name", file=sys.stderr)
            print("   Usage: claude-commit alias set <name> [command]", file=sys.stderr)
            sys.exit(1)
        
        alias_name = args[1]
        command = " ".join(args[2:]) if len(args) > 2 else ""
        
        config = Config()
        config.set_alias(alias_name, command)
        
        if command:
            print(f"✅ Alias '{alias_name}' set to: claude-commit {command}")
        else:
            print(f"✅ Alias '{alias_name}' set to: claude-commit")
        
    elif args[0] == "unset":
        # Delete an alias
        if len(args) < 2:
            print("❌ Error: Please provide alias name", file=sys.stderr)
            print("   Usage: claude-commit alias unset <name>", file=sys.stderr)
            sys.exit(1)
        
        alias_name = args[1]
        config = Config()
        
        if config.delete_alias(alias_name):
            print(f"✅ Alias '{alias_name}' removed")
        else:
            print(f"❌ Alias '{alias_name}' not found", file=sys.stderr)
            sys.exit(1)
    
    else:
        print(f"❌ Unknown alias command: {args[0]}", file=sys.stderr)
        print("   Available commands: list, set, unset, install, uninstall", file=sys.stderr)
        sys.exit(1)


def show_first_run_tip():
    """Show helpful tip on first run"""
    welcome_text = """[bold]👋 Welcome to claude-commit![/bold]

[yellow]💡 Tip:[/yellow] Install shell aliases for faster usage:
   [cyan]claude-commit alias install[/cyan]

   After installation, use short commands like:
   • [green]ccc[/green]   → auto-commit
   • [green]cca[/green]   → analyze all changes
   • [green]ccp[/green]   → preview message

   Run '[cyan]claude-commit alias list[/cyan]' to see all aliases.
"""
    console.print()
    console.print(Panel(welcome_text, border_style="blue", padding=(1, 2)))
    console.print()


def main():
    """Main CLI entry point."""
    # Check if this is the first run
    config = Config()
    if config.is_first_run() and len(sys.argv) > 1 and sys.argv[1] not in ["alias", "-h", "--help"]:
        show_first_run_tip()
        config.mark_first_run_complete()
    
    # Check if first argument is 'alias' command
    if len(sys.argv) > 1 and sys.argv[1] == "alias":
        handle_alias_command(sys.argv[2:])
        return
    
    # Resolve any aliases in the arguments
    resolved_args = resolve_alias(sys.argv[1:])
    
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

Alias Management:
  # List all aliases
  claude-commit alias list

  # Install shell aliases (so you can use 'ccc' directly)
  claude-commit alias install

  # Set a custom alias
  claude-commit alias set cca --all
  claude-commit alias set ccv --verbose
  claude-commit alias set ccac --all --commit

  # Remove an alias
  claude-commit alias unset cca

  # Uninstall shell aliases
  claude-commit alias uninstall

  # Use an alias (after install)
  cca           (expands to: claude-commit --all)
  ccc           (expands to: claude-commit --commit)
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

    args = parser.parse_args(resolved_args)

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
        console.print("\n[yellow]⚠️  Interrupted by user[/yellow]", file=sys.stderr)
        sys.exit(130)

    if not commit_message:
        console.print("[red]❌ Failed to generate commit message[/red]", file=sys.stderr)
        sys.exit(1)

    # Display the generated message with rich formatting
    console.print()
    console.print(Panel(
        commit_message,
        title="[bold]📝 Generated Commit Message[/bold]",
        border_style="green",
        padding=(1, 2)
    ))

    # Handle different output modes
    if args.preview:
        console.print("\n[green]✅ Preview complete (no action taken)[/green]")
        return

    if args.copy:
        try:
            pyperclip.copy(commit_message)
            console.print("\n[green]✅ Commit message copied to clipboard![/green]")
        except Exception as e:
            console.print(f"\n[yellow]⚠️  Failed to copy to clipboard: {e}[/yellow]", file=sys.stderr)

    if args.commit:
        try:
            import subprocess

            # Confirm before committing
            response = console.input("\n[yellow]❓ Commit with this message? [Y/n]:[/yellow] ").strip().lower()
            if response == "n" or response == "no":
                console.print("[red]❌ Commit cancelled[/red]")
                return

            # Execute git commit
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True,
                text=True,
                check=True,
            )
            console.print("\n[green]✅ Successfully committed![/green]")
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(f"\n[red]❌ Failed to commit: {e}[/red]", file=sys.stderr)
            if e.stderr:
                console.print(e.stderr, file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]❌ Unexpected error during commit: {e}[/red]", file=sys.stderr)
            sys.exit(1)
    else:
        # Default: just show the command
        console.print("\n[dim]💡 To commit with this message, run:[/dim]")
        # Escape single quotes in the message for shell
        escaped_message = commit_message.replace("'", "'\\''")
        console.print(f"   [cyan]git commit -m '{escaped_message}'[/cyan]")
        console.print("\n[dim]Or use: claude-commit --commit[/dim]")


if __name__ == "__main__":
    main()
