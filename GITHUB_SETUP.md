# 🐝 LeaseBee - GitHub Setup Guide

## Your Repository is Ready! ✅

Git repository initialized with initial commit containing:
- 55 files
- 5,709 lines of code
- Complete Phase 1 (MVP) implementation

## Quick Push to GitHub

### Option 1: Using GitHub CLI (Recommended)

If you have GitHub CLI installed:

```bash
# Login to GitHub (if not already)
gh auth login

# Create repository and push
gh repo create leasebee --public --source=. --remote=origin --push

# Or create as private
gh repo create leasebee --private --source=. --remote=origin --push
```

### Option 2: Using GitHub Web Interface

#### Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. **Repository name:** `leasebee`
3. **Description:** `🐝 LeaseBee - AI-powered lease abstraction. Sweet extraction, no sting!`
4. **Visibility:** Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click **Create repository**

#### Step 2: Push Your Code

GitHub will show you commands. Use these:

```bash
# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/leasebee.git

# Push to GitHub
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Verify Upload

After pushing, visit:
```
https://github.com/YOUR_USERNAME/leasebee
```

You should see:
- ✅ All files uploaded
- ✅ README.md displayed with bee emoji
- ✅ 55 files in repository
- ✅ Initial commit message

## Next Steps After Upload

### 1. Add Repository Description

On GitHub, click the ⚙️ settings icon and add:

**Description:**
```
🐝 AI-powered commercial lease abstraction - Buzzing through leases in seconds
```

**Topics (tags):**
- `lease-abstraction`
- `ai`
- `claude`
- `fastapi`
- `nextjs`
- `typescript`
- `real-estate`
- `automation`
- `pdf-extraction`

### 2. Add Repository Image

1. Create a simple banner image with:
   - Bee emoji or illustration
   - "LeaseBee" text
   - Tagline
2. Go to Settings → General → Social Preview
3. Upload image

### 3. Set Up GitHub Pages (Optional)

For documentation hosting:
1. Settings → Pages
2. Source: Deploy from branch
3. Branch: main, folder: /docs
4. Save

### 4. Add Secrets for CI/CD (Future)

Settings → Secrets and variables → Actions

Add these secrets when ready to deploy:
- `ANTHROPIC_API_KEY`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DATABASE_URL`

### 5. Enable Issues

Settings → General → Features
- ✅ Issues
- ✅ Discussions (optional)
- ✅ Projects (optional)

## Suggested Repository Settings

### Branch Protection (When ready for production)

Settings → Branches → Add rule

**Branch name pattern:** `main`

Enable:
- ✅ Require pull request before merging
- ✅ Require status checks to pass
- ✅ Require branches to be up to date

### Collaborators

Settings → Collaborators and teams

Add team members with appropriate permissions:
- **Admin** - Full access
- **Maintain** - Can merge PRs
- **Write** - Can push to branches
- **Read** - View only

## Clone Repository Elsewhere

To clone on another machine:

```bash
git clone https://github.com/YOUR_USERNAME/leasebee.git
cd leasebee

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
alembic upgrade head
uvicorn app.main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local
npm run dev
```

## Create Development Workflow

### Branching Strategy

```bash
# Create feature branch
git checkout -b feature/add-batch-processing

# Make changes, commit
git add .
git commit -m "Add batch processing for multiple PDFs"

# Push to GitHub
git push origin feature/add-batch-processing

# Create Pull Request on GitHub
# After review, merge to main
```

### Commit Message Format

Use conventional commits:

```
feat: Add batch PDF upload
fix: Resolve extraction timeout issue
docs: Update deployment guide
refactor: Simplify Claude service code
test: Add unit tests for field schema
chore: Update dependencies
```

## Add CI/CD with GitHub Actions (Future)

Create `.github/workflows/test.yml`:

```yaml
name: Test

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && pytest

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm install
      - run: cd frontend && npm test
```

## Recommended README Badges

Add to top of README.md:

```markdown
![GitHub](https://img.shields.io/github/license/YOUR_USERNAME/leasebee)
![GitHub Stars](https://img.shields.io/github/stars/YOUR_USERNAME/leasebee)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
```

## Make Repository Stand Out

### Create a Great README

Your README.md already has:
- ✅ Clear title with emoji
- ✅ Project description
- ✅ Architecture overview
- ✅ Setup instructions
- ✅ Features list

Consider adding:
- Screenshots/demo GIF
- Live demo link (when deployed)
- Roadmap
- Contributing guidelines
- License information

### Add a LICENSE

Create `LICENSE` file:

```bash
# For proprietary/closed source
echo "Copyright (c) 2025 LeaseBee. All rights reserved." > LICENSE

# Or choose open source license at
# https://choosealicense.com/
```

### Create CONTRIBUTING.md

```markdown
# Contributing to LeaseBee

We love your input! We want to make contributing as easy as possible.

## Development Process

1. Fork the repo
2. Create your feature branch
3. Make your changes
4. Write/update tests
5. Ensure tests pass
6. Commit your changes
7. Push to your fork
8. Open a Pull Request

## Code Style

- Backend: Follow PEP 8
- Frontend: Use ESLint configuration
- Write descriptive commit messages
```

## Monitor Repository

### GitHub Insights

Check regularly:
- **Traffic:** Visitor stats
- **Community:** Issues, PRs
- **Network:** Forks, contributors
- **Pulse:** Recent activity

### Notifications

Settings → Notifications
- Watch your repository
- Get notified of issues, PRs, mentions

## Backup Strategy

GitHub is your primary backup, but also:
1. Clone to local machine
2. Clone to backup drive
3. Consider GitLab/Bitbucket mirror (optional)

---

## Quick Reference

**Clone:**
```bash
git clone https://github.com/YOUR_USERNAME/leasebee.git
```

**Create branch:**
```bash
git checkout -b feature/my-feature
```

**Commit:**
```bash
git add .
git commit -m "Description of changes"
```

**Push:**
```bash
git push origin feature/my-feature
```

**Update from main:**
```bash
git checkout main
git pull origin main
git checkout feature/my-feature
git merge main
```

---

🐝 **LeaseBee is now on GitHub!** Ready to buzz! ✨

Your repository URL will be:
`https://github.com/YOUR_USERNAME/leasebee`

Share it with your team and start collaborating!
