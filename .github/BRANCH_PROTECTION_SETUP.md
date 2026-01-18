# 🐝 LeaseBee Branch Protection Setup

Step-by-step guide to protect your `main` branch on GitHub.

## Why Branch Protection?

Branch protection prevents:
- ❌ Accidental direct pushes to main
- ❌ Merging broken code
- ❌ Losing code history
- ❌ Deploying untested changes

Branch protection enables:
- ✅ Code review process
- ✅ Automated testing before merge
- ✅ Better code quality
- ✅ Team collaboration

---

## Quick Setup (Recommended for Start)

### Step 1: Go to Settings

1. Navigate to https://github.com/mostlyerror/leasebee
2. Click **Settings** (top navigation)
3. Click **Branches** (left sidebar)

### Step 2: Add Branch Protection Rule

1. Click **Add rule** (or **Add branch protection rule**)
2. **Branch name pattern:** `main`
3. Configure settings below

### Step 3: Configure Protection Settings

#### ✅ **Require a pull request before merging**

Check this box, then:
- **Required approvals:** `1`
  - For solo: Can be `0` initially
  - For team: Minimum `1`
- ✅ **Dismiss stale pull request approvals when new commits are pushed**
- ✅ **Require review from Code Owners** (optional, for teams)

#### ✅ **Require status checks to pass before merging** (when CI/CD is set up)

Check this box, then:
- ✅ **Require branches to be up to date before merging**
- Status checks to require: (add these when you have CI/CD)
  - `backend-tests`
  - `frontend-tests`
  - `lint`

#### ✅ **Require conversation resolution before merging**

Ensures all PR comments are addressed before merging.

#### ⚠️ **Do not allow bypassing the above settings**

For teams: Check this to enforce rules even for admins

For solo: Leave unchecked so you can bypass if needed

#### Optional Settings

- **Require signed commits** - Extra security (requires GPG setup)
- **Require linear history** - Prevents merge commits (cleaner history)
- **Require deployments to succeed** - Wait for deployment before merge
- **Lock branch** - Make branch read-only (for archival)

### Step 4: Save Changes

Click **Create** or **Save changes** at the bottom

---

## Configuration Examples

### Solo Developer (Starting Out)

**Goal:** Basic protection without blocking yourself

```
Branch name pattern: main

✅ Require a pull request before merging
   Required approvals: 0
   ✅ Dismiss stale reviews

✅ Require conversation resolution before merging

❌ Do not allow bypassing (unchecked - you can override)
```

**Why this setup:**
- Forces you to use PRs (good habit)
- Doesn't require approvals (you're solo)
- You can still bypass in emergencies

### Small Team (2-4 developers)

**Goal:** Enforce code review, allow flexibility

```
Branch name pattern: main

✅ Require a pull request before merging
   Required approvals: 1
   ✅ Dismiss stale reviews

✅ Require status checks to pass
   ✅ Require branches to be up to date
   Status checks: (when CI/CD ready)
     - backend-tests
     - frontend-tests

✅ Require conversation resolution before merging

❌ Do not allow bypassing (unchecked for now)
```

**Why this setup:**
- Enforces 1 approval (peer review)
- Runs automated tests
- Flexible for urgent fixes

### Production Team (5+ developers)

**Goal:** Strict quality control

```
Branch name pattern: main

✅ Require a pull request before merging
   Required approvals: 2
   ✅ Dismiss stale reviews
   ✅ Require review from Code Owners

✅ Require status checks to pass
   ✅ Require branches to be up to date
   Status checks:
     - backend-tests
     - frontend-tests
     - lint
     - security-scan
     - e2e-tests

✅ Require conversation resolution before merging

✅ Require signed commits

✅ Do not allow bypassing the above settings

✅ Require linear history
```

**Why this setup:**
- Maximum protection
- Multiple reviews required
- Comprehensive testing
- No bypassing allowed

---

## Testing Your Protection

### Test 1: Try Direct Push (Should Fail)

```bash
# Make a change on main
git checkout main
echo "test" >> README.md
git add README.md
git commit -m "test: Direct commit"
git push origin main
```

**Expected result:** ❌ Push rejected
```
remote: error: GH006: Protected branch update failed
```

**Success!** Branch protection is working.

### Test 2: Use PR Process (Should Work)

```bash
# Create feature branch
git checkout -b test/branch-protection
echo "test" >> README.md
git add README.md
git commit -m "test: Testing branch protection"
git push origin test/branch-protection
```

Then on GitHub:
1. Create PR from `test/branch-protection` → `main`
2. Merge the PR
3. Delete branch

**Expected result:** ✅ PR merges successfully

---

## Status Checks Setup (CI/CD)

When you're ready to add automated testing:

### Step 1: Create GitHub Actions Workflow

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  backend-tests:
    name: Backend Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest

  frontend-tests:
    name: Frontend Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm install
      - name: Run tests
        run: |
          cd frontend
          npm test

  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - name: Lint frontend
        run: |
          cd frontend
          npm install
          npm run lint
```

### Step 2: Enable Status Checks in Branch Protection

1. Go to Settings → Branches → Edit `main` rule
2. Under "Require status checks to pass"
3. Search for and add:
   - `backend-tests`
   - `frontend-tests`
   - `lint`
4. Save changes

Now PRs will automatically run tests!

---

## Code Owners (Optional)

Automatically request reviews from specific people.

### Create CODEOWNERS File

Create `.github/CODEOWNERS`:

```
# Default owners for everything
* @mostlyerror

# Backend code
/backend/ @mostlyerror

# Frontend code
/frontend/ @mostlyerror

# Documentation
*.md @mostlyerror
/docs/ @mostlyerror

# Critical files (require your review)
/backend/app/services/claude_service.py @mostlyerror
/backend/app/schemas/field_schema.py @mostlyerror
```

### Enable in Branch Protection

1. Settings → Branches → Edit `main` rule
2. Under "Require pull request before merging"
3. ✅ Check "Require review from Code Owners"
4. Save

Now PRs will auto-request reviews from owners!

---

## Bypassing Protection (Emergency)

### When You Might Need to Bypass

- Critical hotfix needed immediately
- Automated deployment failed
- Reviewer unavailable for urgent fix

### How to Bypass (If Allowed)

#### Method 1: Admin Override

If you unchecked "Do not allow bypassing":
1. Create PR as normal
2. As admin, you'll see **Merge without waiting** option
3. Click to merge immediately

#### Method 2: Temporary Disable

1. Settings → Branches → Edit rule
2. Uncheck protections temporarily
3. Push your fix
4. Re-enable protections immediately

⚠️ **Use sparingly!** Document why in commit message.

---

## Troubleshooting

### Problem: Can't push to main

**Solution:** You need to use PRs!
```bash
git checkout -b fix/my-fix
git push origin fix/my-fix
# Create PR on GitHub
```

### Problem: PR blocked by failing tests

**Solution:** Fix the tests first
```bash
# Run tests locally
cd backend && pytest
cd frontend && npm test

# Fix issues, commit, push
git add .
git commit -m "fix: Resolve failing tests"
git push
```

### Problem: Need 1 approval but I'm solo

**Option 1:** Set required approvals to `0`
**Option 2:** Create a second GitHub account for "rubber duck" reviews
**Option 3:** Use branch protection but allow bypass

### Problem: Status checks not showing up

**Cause:** GitHub Actions not running yet

**Solution:**
1. Make sure `.github/workflows/tests.yml` exists
2. Push to trigger workflow
3. Wait for first run to complete
4. Status checks will then appear in branch protection settings

---

## Recommended Timeline

### Week 1-2 (MVP Phase)
```
✅ Basic protection
✅ Require PRs
❌ No required approvals (solo dev)
❌ No status checks yet
```

### Week 3-4 (Testing Phase)
```
✅ Require PRs
✅ Add GitHub Actions
✅ Require status checks to pass
❌ Still no required approvals
```

### Month 2+ (Production)
```
✅ Require PRs
✅ Require 1 approval (if team)
✅ Require status checks
✅ Require conversation resolution
✅ Enable code owners
```

---

## Quick Reference Commands

### Create Feature Branch
```bash
git checkout main && git pull
git checkout -b feature/my-feature
```

### Push and Create PR
```bash
git push origin feature/my-feature
gh pr create --title "feat: Add feature" --body "Description"
```

### Update Branch with Main
```bash
git checkout main && git pull
git checkout feature/my-feature
git merge main
git push
```

### Delete Merged Branch
```bash
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

---

## Resources

- [GitHub Branch Protection Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [CODEOWNERS Syntax](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

---

🐝 **LeaseBee Branch Protection** - Keeping your code safe and sound!

**Start simple, add complexity as you grow.**
