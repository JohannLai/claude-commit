# Agentic Design Philosophy

## Why Agentic Approach?

Traditional commit message generators follow a rigid pattern:
1. Get git diff
2. Send diff to LLM
3. Get commit message back

This approach has limitations:
- ❌ Only sees surface-level changes (lines added/removed)
- ❌ Lacks context about the codebase
- ❌ Can't understand the intent behind changes
- ❌ Produces generic messages like "update file.py"

## Our Agentic Approach

`claude-commit` gives Claude **autonomy** to investigate changes however it deems necessary:

```
User Request: "Generate commit message"
         ↓
    Claude Agent (autonomous decision-making)
         ↓
    ┌─────────────────────────────────────┐
    │ What should I investigate?          │
    │ - git status (what files changed?)  │
    │ - git diff (what lines changed?)    │
    │ - Read files (what do they do?)     │
    │ - Grep codebase (how is this used?) │
    │ - Explore structure (project layout)│
    └─────────────────────────────────────┘
         ↓
    Deep Understanding
         ↓
    Accurate Commit Message
```

## Tool Access

Claude has access to:

### 1. **Bash** - Execute Commands
```bash
git status
git diff --cached
git log --oneline -5
git show HEAD
wc -l src/**/*.py
find . -name "*.py" | head -10
```

### 2. **Read** - Read Files
```python
# Claude can read any file to understand context
- Read modified file to see its full structure
- Read related files (imports, dependencies)
- Read documentation or README for context
```

### 3. **Grep** - Search Codebase
```bash
# Find where a function is called
grep -r "authenticate_user" .

# Find all references to a class
grep -r "class UserAuth" .

# Understand how an API is used
grep -r "POST /api/auth" .
```

### 4. **Glob** - Find Files
```bash
# Find all test files
glob **/*test*.py

# Find all config files
glob **/config.*

# Find related modules
glob src/auth/**/*.py
```

## Comparison: Traditional vs Agentic

### Example Change: Adding authentication

**Traditional Approach:**
```
Input: git diff showing 50 lines of code changes
Output: "feat: add authentication functionality"
```

**Agentic Approach:**
```
Claude's Analysis Process:
1. git diff --cached
   → Sees changes in auth.py, user_model.py, api_routes.py

2. Read src/auth/auth.py
   → Understands JWT token implementation

3. Read src/models/user_model.py
   → Sees User model with password hashing

4. grep -r "verify_token" src/
   → Finds token verification used in middleware

5. Read src/api/routes.py
   → Sees new login/logout endpoints

Output: "feat: add JWT-based authentication with refresh token support

Implement secure authentication system using bcrypt password hashing
and JWT tokens. Include login, logout, refresh endpoints and 
authentication middleware for protected routes."
```

## Benefits of Agentic Design

### 1. **Context-Aware Messages**
Claude understands the broader context, not just the diff.

### 2. **Intent-Based**
Messages capture WHY things changed, not just WHAT lines changed.

### 3. **Accurate Categorization**
Correctly identifies feat/fix/refactor/etc. by understanding the change purpose.

### 4. **Handles Complex Changes**
Can analyze multi-file changes and understand their relationships.

### 5. **Adapts to Codebase**
Different projects need different investigation strategies - Claude adapts.

## Examples of Autonomous Decision Making

### Scenario 1: Simple Change
```python
# Change: Fix typo in comment
Claude's decision:
- git diff is sufficient
- No need to read files or grep
- Quick analysis → "docs: fix typo in authentication comment"
```

### Scenario 2: Complex Refactoring
```python
# Change: Extract function to separate module
Claude's decisions:
1. Read old file to understand original structure
2. Read new file to understand new organization
3. Grep to see if function is called elsewhere
4. Check if imports were updated correctly
Result: "refactor: extract user validation to separate service

Move user validation logic from auth.py to validators/user_validator.py
for better separation of concerns and reusability."
```

### Scenario 3: Bug Fix
```python
# Change: Fix memory leak
Claude's decisions:
1. Read the file to understand the function
2. Grep to find where connections are created
3. git log to see if related to previous issues
4. Read related connection pool code
Result: "fix: prevent memory leak in connection pool

Close database connections properly in error handling path.
Connections were not released when queries failed, causing
gradual memory exhaustion under error conditions."
```

## Implementation Details

### System Prompt Design
The system prompt is designed to:
- ✅ Encourage exploration and investigation
- ✅ Suggest tools but allow Claude to decide
- ✅ Focus on understanding intent, not just changes
- ✅ Provide examples of excellent commit messages

### Message Extraction
Claude outputs messages in a specific format:
```
COMMIT_MESSAGE:
<actual commit message here>
```

This allows Claude to:
- Explain its analysis process
- Show what it discovered
- Then provide the final message in a parseable format

### Freedom vs Guidance
We provide:
- **Guidance**: Best practices, examples, suggestions
- **Freedom**: Claude decides what to investigate and how
- **Constraints**: Output format, message style guidelines

## Future Enhancements

Potential improvements to the agentic approach:

1. **Learning from History**
   - Analyze past commits in the repo
   - Match the existing commit message style
   
2. **Interactive Mode**
   - Ask user questions if context is unclear
   - Request additional information if needed

3. **Team Conventions**
   - Read CONTRIBUTING.md or .commit-template
   - Follow project-specific conventions

4. **Impact Analysis**
   - Run tests to see what's affected
   - Check for breaking changes

5. **Related Issue Detection**
   - Check git branch names for issue numbers
   - Search for TODO/FIXME comments in changes

## Conclusion

The agentic approach transforms commit message generation from a simple text transformation task into an intelligent code analysis process. By giving Claude the tools and freedom to investigate thoroughly, we get commit messages that truly capture the meaning and impact of changes.

