# 🐝 LeaseBee Branching Strategy

## Overview

LeaseBee uses a simplified **GitHub Flow** model optimized for continuous deployment and small team collaboration.

## Branch Types

### 🌳 Main Branches

#### `main`
- **Purpose:** Production-ready code
- **Protection:** ✅ Protected (requires PR + reviews)
- **Deployment:** Auto-deploys to production
- **Always:** Stable, tested, deployable

#### `develop` (Optional for larger teams)
- **Purpose:** Integration branch for features
- **Protection:** ✅ Protected (requires PR)
- **Deployment:** Auto-deploys to staging
- **Always:** Latest development state

---

## Recommended Strategy: Simplified GitHub Flow

Perfect for LeaseBee's current stage (MVP → production).

### Branch Structure

```
main (production)
  ├── feature/add-batch-upload
  ├── feature/pdf-viewer
  ├── fix/extraction-timeout
  ├── docs/api-documentation
  └── hotfix/critical-bug
```

### Workflow

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Work on Feature**
   ```bash
   # Make changes
   git add .
   git commit -m "feat: Add batch upload functionality"
   git push origin feature/your-feature-name
   ```

3. **Open Pull Request**
   - Go to GitHub
   - Create PR from `feature/your-feature-name` → `main`
   - Add description, screenshots
   - Request reviews

4. **Code Review**
   - Team reviews code
   - Run automated tests
   - Address feedback

5. **Merge & Deploy**
   - Squash and merge to `main`
   - Delete feature branch
   - Auto-deploy to production

---

## Branch Naming Conventions

### Format
```
<type>/<short-description>
```

### Types

**Features** (new functionality)
```bash
feature/batch-pdf-upload
feature/pdf-viewer-integration
feature/dark-mode
feature/user-authentication
```

**Fixes** (bug fixes)
```bash
fix/extraction-timeout
fix/s3-upload-error
fix/ui-alignment
fix/memory-leak
```

**Hotfixes** (urgent production fixes)
```bash
hotfix/critical-security-patch
hotfix/data-loss-bug
hotfix/api-down
```

**Documentation**
```bash
docs/api-documentation
docs/setup-guide
docs/deployment-instructions
```

**Refactoring** (code improvements, no new features)
```bash
refactor/claude-service
refactor/database-queries
refactor/component-structure
```

**Tests**
```bash
test/unit-tests-claude-service
test/e2e-upload-flow
test/integration-tests
```

**Chores** (maintenance, dependencies)
```bash
chore/update-dependencies
chore/cleanup-unused-code
chore/migrate-to-pnpm
```

**Performance**
```bash
perf/optimize-extraction-speed
perf/reduce-bundle-size
perf/database-indexing
```

### Examples

✅ **Good:**
- `feature/add-lease-comparison`
- `fix/csv-export-encoding`
- `docs/update-quickstart`
- `refactor/simplify-field-schema`

❌ **Bad:**
- `my-changes`
- `fixes`
- `update`
- `branch-1`
- `johns-work`

---

## Workflow Examples

### Example 1: Adding a New Feature

**Goal:** Add batch PDF upload

```bash
# 1. Start from main
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/batch-pdf-upload

# 3. Make changes
# ... edit files ...

# 4. Commit regularly
git add .
git commit -m "feat: Add UI for batch upload"
git push origin feature/batch-pdf-upload

# ... more commits ...
git commit -m "feat: Implement backend batch processing"
git push origin feature/batch-pdf-upload

# 5. Open PR on GitHub
# 6. Address review feedback
# 7. Merge when approved
```

### Example 2: Fixing a Bug

**Goal:** Fix extraction timeout issue

```bash
# 1. Create fix branch
git checkout main
git pull origin main
git checkout -b fix/extraction-timeout

# 2. Fix the bug
# ... edit files ...

# 3. Test the fix
cd backend
pytest tests/test_claude_service.py

# 4. Commit
git add .
git commit -m "fix: Increase Claude API timeout to 120s"
git push origin fix/extraction-timeout

# 5. Open PR → Merge → Delete branch
```

### Example 3: Hotfix (Urgent Production Bug)

**Goal:** Fix critical data loss bug

```bash
# 1. Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/data-loss-on-save

# 2. Fix urgently
# ... fix the critical bug ...

# 3. Test thoroughly
pytest
npm test

# 4. Commit
git add .
git commit -m "hotfix: Prevent data loss when save fails"
git push origin hotfix/data-loss-on-save

# 5. Fast-track PR review
# 6. Merge ASAP
# 7. Monitor production
```

---

## Pull Request Guidelines

### PR Title Format

Use conventional commits:

```
<type>: <description>

Examples:
feat: Add batch PDF upload
fix: Resolve extraction timeout
docs: Update deployment guide
refactor: Simplify Claude service
test: Add unit tests for field schema
```

### PR Description Template

See `.github/pull_request_template.md` (created below)

### PR Checklist

Before opening a PR, ensure:

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated if needed
- [ ] No console errors or warnings
- [ ] Tested locally
- [ ] Branch is up to date with main
- [ ] Descriptive commit messages
- [ ] PR description is clear

### Review Process

**For Small Changes** (docs, minor fixes):
- 1 approval required
- Can self-merge after approval

**For Features** (new functionality):
- 1-2 approvals required
- Author should NOT self-merge
- Run automated tests

**For Hotfixes** (critical bugs):
- Fast-track review
- 1 approval minimum
- Can merge immediately after approval

---

## Commit Message Conventions

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `style`: Code formatting (no logic changes)

### Examples

```bash
# Simple commit
git commit -m "feat: Add batch upload button"

# Detailed commit
git commit -m "feat(upload): Add batch PDF upload functionality

- Support uploading multiple files at once
- Show progress for each file
- Handle errors gracefully
- Add tests for batch upload

Closes #42"

# Bug fix with issue reference
git commit -m "fix(extraction): Resolve timeout on large PDFs

Increased timeout from 60s to 120s to handle larger documents.

Fixes #38"

# Breaking change
git commit -m "feat(api): Change extraction endpoint response format

BREAKING CHANGE: Response now includes metadata object.
Clients need to update to access extraction.data instead of extraction directly.

Closes #55"
```

---

## Branch Protection Rules

### For `main` Branch

Settings → Branches → Add rule

**Branch name pattern:** `main`

**Recommended settings:**

✅ **Require pull request before merging**
- Require approvals: 1
- Dismiss stale reviews when new commits are pushed
- Require review from Code Owners (optional)

✅ **Require status checks to pass before merging**
- Require branches to be up to date
- Status checks: (when CI/CD is set up)
  - Backend tests
  - Frontend tests
  - Linting

✅ **Require conversation resolution before merging**

✅ **Do not allow bypassing the above settings** (for admins)

**Optional:**
- Require signed commits
- Require linear history (prevents merge commits)

### For `develop` Branch (if using)

Same as `main` but:
- Can allow self-merge for small teams
- Fewer required approvals (can be 0 for solo work)

---

## Keeping Branches Updated

### Before Opening PR

```bash
# Update your branch with latest main
git checkout main
git pull origin main
git checkout feature/your-feature
git merge main

# Or use rebase for cleaner history
git checkout feature/your-feature
git rebase main

# Push updated branch
git push origin feature/your-feature --force-with-lease
```

### Resolving Conflicts

```bash
# When merge conflict occurs
git checkout feature/your-feature
git merge main

# Git will show conflicts
# Edit conflicted files
# Look for <<<<<<< HEAD markers

# After resolving
git add .
git commit -m "merge: Resolve conflicts with main"
git push origin feature/your-feature
```

---

## Best Practices

### Do's ✅

1. **Pull main before creating branch**
   ```bash
   git checkout main && git pull origin main
   git checkout -b feature/new-feature
   ```

2. **Commit often with clear messages**
   ```bash
   git commit -m "feat: Add upload validation"
   git commit -m "test: Add tests for validation"
   ```

3. **Keep PRs small and focused**
   - One feature per PR
   - Easier to review
   - Faster to merge

4. **Write descriptive PR descriptions**
   - What changed
   - Why it changed
   - How to test

5. **Delete merged branches**
   ```bash
   git branch -d feature/merged-feature
   git push origin --delete feature/merged-feature
   ```

6. **Review your own PR first**
   - Check diff on GitHub
   - Catch obvious mistakes
   - Add comments for reviewers

### Don'ts ❌

1. **Don't commit directly to main**
   - Always use feature branches
   - Even for small fixes

2. **Don't create long-lived branches**
   - Merge frequently
   - Avoid divergence from main

3. **Don't merge without reviews** (for main)
   - At least one approval
   - Exception: Hotfixes (with caution)

4. **Don't push broken code**
   - Test locally first
   - Run tests before pushing

5. **Don't merge with conflicts unresolved**
   - Resolve all conflicts
   - Test after resolving

6. **Don't use vague commit messages**
   - ❌ "update"
   - ❌ "fix stuff"
   - ✅ "fix: Resolve S3 upload timeout"

---

## Common Scenarios

### Scenario 1: Need to work on 2 features simultaneously

```bash
# Start feature 1
git checkout -b feature/pdf-viewer
# ... work on it ...
git push origin feature/pdf-viewer

# Start feature 2 (from main, not feature 1!)
git checkout main
git pull origin main
git checkout -b feature/batch-upload
# ... work on it ...
git push origin feature/batch-upload

# Switch between them
git checkout feature/pdf-viewer
git checkout feature/batch-upload
```

### Scenario 2: Feature taking too long, want to merge partial work

```bash
# Split into smaller PRs
git checkout -b feature/pdf-viewer-part1
# ... implement basic viewer ...
git push origin feature/pdf-viewer-part1
# Open PR, merge

# Then part 2
git checkout main
git pull origin main
git checkout -b feature/pdf-viewer-part2
# ... implement highlighting ...
```

### Scenario 3: Realized you're on wrong branch

```bash
# Oops, made changes on main!
git stash

# Create proper branch
git checkout -b feature/my-feature

# Apply changes
git stash pop

# Commit
git add .
git commit -m "feat: Add feature"
git push origin feature/my-feature
```

---

## Quick Reference

### Create Branch
```bash
git checkout -b <type>/<name>
```

### Push Branch
```bash
git push origin <branch-name>
```

### Update Branch
```bash
git checkout main && git pull origin main
git checkout <branch-name>
git merge main
```

### Delete Branch
```bash
# Local
git branch -d <branch-name>

# Remote
git push origin --delete <branch-name>
```

### List Branches
```bash
# Local
git branch

# Remote
git branch -r

# All
git branch -a
```

---

## Tools & Automation

### GitHub CLI

```bash
# Create PR from command line
gh pr create --title "feat: Add feature" --body "Description"

# List PRs
gh pr list

# Checkout PR
gh pr checkout 123

# Merge PR
gh pr merge 123 --squash
```

### Git Aliases

Add to `~/.gitconfig`:

```ini
[alias]
    co = checkout
    br = branch
    ci = commit
    st = status
    cp = cherry-pick
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = log --oneline --graph --decorate --all
    feature = "!f() { git checkout main && git pull && git checkout -b feature/$1; }; f"
    fix = "!f() { git checkout main && git pull && git checkout -b fix/$1; }; f"
```

Usage:
```bash
git feature batch-upload  # Creates feature/batch-upload
git fix timeout-issue     # Creates fix/timeout-issue
```

---

## Timeline & Milestones

### Phase 1 (Current - MVP)
- **Strategy:** Simple feature branches → main
- **Reviews:** Minimal (solo dev)
- **Deployment:** Manual

### Phase 2 (Testing)
- **Strategy:** Add branch protection
- **Reviews:** 1 approval required
- **Deployment:** Semi-automated

### Phase 3 (Production)
- **Strategy:** Full GitHub Flow
- **Reviews:** Required + automated tests
- **Deployment:** Automated CI/CD

### Phase 4 (Scale)
- **Strategy:** Consider Git Flow with develop branch
- **Reviews:** 2 approvals for critical changes
- **Deployment:** Blue-green deployment

---

🐝 **LeaseBee Branching Strategy** - Keep it simple, keep it buzzing!

**Current recommendation:** Start with simple feature branches → main, add complexity as team grows.
