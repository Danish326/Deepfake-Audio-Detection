# Pre-GitHub Push Checklist — A DevOps Perspective
 
Before you push anything to GitHub (especially a public repo), here's what every experienced DevOps engineer enforces on their teams:
 
---
 
## 🔐 1. Secrets & Credentials — **#1 Priority**
 
This is the most critical and most commonly messed up step.
 
- **Never commit secrets** — API keys, DB passwords, tokens, private keys, `.env` files
- Use **`.gitignore`** to exclude sensitive files *before* your first commit
- Use tools like **`git-secrets`**, **truffleHog**, or **`gitleaks`** to scan your history
- Store secrets in **environment variables**, GitHub Secrets, Vault, or AWS Secrets Manager
- If you accidentally pushed a secret — **rotate it immediately**, then purge it with `git filter-repo`
> ⚠️ GitHub's bots and malicious scrapers find exposed keys within **seconds** of a push.
 
---
 
## 📄 2. `.gitignore` — Set It Up Early
 
Make sure you're ignoring:
 
```
.env
*.pem / *.key / *.p12
node_modules / venv / __pycache__
build / dist / target
*.log
.DS_Store / Thumbs.db
IDE folders (.idea/, .vscode/)
```
 
> 💡 Use **gitignore.io** to generate one tailored to your stack.
 
---
 
## 🏗️ 3. Repository Structure & Hygiene
 
- Have a clear, logical folder structure
- Include a **`README.md`** — purpose, setup instructions, usage, contribution guide
- Add a **`LICENSE`** file (MIT, Apache 2.0, etc.) — critical for open source
- Include a **`CHANGELOG.md`** for tracking versions
- Add **`.editorconfig`** for consistent formatting across editors
---
 
## 🌿 4. Branching Strategy
 
Decide *before* you push:
 
- Will you use **Git Flow**, **trunk-based development**, or **GitHub Flow**?
- Protect your `main`/`master` branch — require PRs, block direct pushes
- Set up **branch naming conventions** (`feature/`, `fix/`, `hotfix/`)
---
 
## 🔁 5. CI/CD Pipeline (GitHub Actions)
 
Set up automation from day one:
 
- **Linting & formatting** checks on every PR
- **Unit/integration tests** that must pass before merging
- **Security scanning** (Dependabot, Snyk, CodeQL)
- **Docker image builds** if containerized
- **Auto-deployment** to staging on merge to `main`
---
 
## 📦 6. Dependency Management
 
- Pin dependency versions (`package-lock.json`, `requirements.txt`, `go.sum`)
- Enable **Dependabot** for automated security updates
- Audit dependencies: `npm audit`, `pip-audit`, `trivy`
- Don't commit `node_modules/`, `vendor/` unless absolutely necessary
---
 
## 🔍 7. Code Quality Gates
 
- Add a **`.eslintrc`** / **`.pylintrc`** / linter config relevant to your stack
- Set up **pre-commit hooks** with tools like `husky` (JS) or `pre-commit` (Python)
- Consider adding **SonarCloud** or **CodeClimate** for code quality scanning
---
 
## 📋 8. Documentation
 
| File | Purpose |
|------|---------|
| `README.md` | Project overview & quickstart |
| `CONTRIBUTING.md` | How to contribute |
| `CODE_OF_CONDUCT.md` | Community standards |
| `SECURITY.md` | How to report vulnerabilities |
| `docs/` folder | Architecture, API docs, runbooks |
 
---
 
## ⚙️ 9. Repository Settings (After Creating the Repo)
 
Configure these in GitHub settings:
 
- ✅ **Branch protection rules** on `main`
- ✅ **Require PR reviews** before merging
- ✅ **Enable Dependabot alerts**
- ✅ **Enable secret scanning** (GitHub's native feature)
- ✅ **Disable force pushes** on protected branches
- ✅ Set repo **visibility** (public vs. private) intentionally
---
 
## 🔑 10. Access & Permissions
 
- Use **SSH keys** or **fine-grained PATs** instead of passwords
- Apply **least privilege** — don't give everyone admin
- Set up **CODEOWNERS** file to auto-assign reviewers
- If an org repo, configure **team permissions** properly
---
 
## ⚡ Quick Pre-Push Command Checklist
 
```bash
# Check what you're about to commit
git status
git diff --staged
 
# Scan for secrets
gitleaks detect --source .
 
# Check .gitignore is working
git ls-files --others --ignored --exclude-standard
 
# Review commit history before push
git log --oneline
```
 
---
 
> **Golden Rule:** Treat every push to GitHub as potentially public, even on private repos.
> Infrastructure gets misconfigured, repos get transferred — secrets should **never** be in version control to begin with.
