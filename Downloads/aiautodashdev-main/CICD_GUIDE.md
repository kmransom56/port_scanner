# AIAutoDash CI/CD Guide

## 📋 Overview

AIAutoDash includes a comprehensive CI/CD pipeline using GitHub Actions for automated testing, building, and deployment.

**CI/CD Features**:
- ✅ Automated testing across multiple Python versions
- ✅ Code quality checks (linting, formatting, type checking)
- ✅ Security scanning (Bandit, Safety, Trivy)
- ✅ Docker image builds with multi-architecture support
- ✅ Automated deployments to production/staging
- ✅ Rollback capabilities
- ✅ Health checks and verification

---

## 🔄 Workflows

### 1. CI - Test and Lint (`ci.yml`)

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Only when Python files or requirements change

**Jobs**:

#### Test Job
- Runs on: `ubuntu-latest`
- Python versions: `3.10`, `3.11`, `3.12`
- Steps:
  1. Checkout code
  2. Set up Python with pip caching
  3. Install dependencies + test tools
  4. Run pytest with coverage
  5. Upload coverage to Codecov

**Example test execution**:
```bash
pytest tests/ -v --cov=. --cov-report=xml --cov-report=term
```

#### Lint Job
- Checks code formatting with Black
- Verifies import sorting with isort
- Runs Flake8 for code quality
- Type checking with MyPy

**Commands**:
```bash
black --check --diff .
isort --check-only --diff .
flake8 . --count --statistics
mypy main.py --ignore-missing-imports
```

#### Security Job
- Bandit for security vulnerabilities
- Safety for dependency vulnerabilities
- Generates reports as artifacts

---

### 2. Docker Build and Push (`docker.yml`)

**Triggers**:
- Push to `main` branch
- Version tags (`v*.*.*`)
- Pull requests to `main`

**Features**:
- Multi-architecture builds (amd64, arm64)
- GitHub Container Registry (ghcr.io)
- Automated tagging strategy
- Docker layer caching
- CVE scanning with Docker Scout
- Container testing before push

**Image Tags**:
```
ghcr.io/kmransom56/aiautodash:latest
ghcr.io/kmransom56/aiautodash:main
ghcr.io/kmransom56/aiautodash:v1.0.0
ghcr.io/kmransom56/aiautodash:main-abc123def
```

**Test Image Job**:
1. Build image locally
2. Start container
3. Wait 10 seconds for startup
4. Test `/health` endpoint
5. Test root endpoint
6. Run Trivy security scan
7. Upload results to GitHub Security

---

### 3. Deploy to Production (`deploy.yml`)

**Triggers**:
- Manual workflow dispatch
- Automatic on push to `main` (specific files)

**Environments**:
- Production (default)
- Staging

**Deployment Process**:
```
1. Checkout code
2. Setup SSH with private key
3. Copy files to server (via SCP)
4. Backup current deployment
5. Update application files
6. Rebuild Docker container
7. Restart container with force-recreate
8. Wait for startup (15 seconds)
9. Health check verification
10. Clean up temporary files
```

**Verification Steps**:
- Health endpoint: `http://100.123.10.72:5902/health`
- Registry endpoint: `/registry`
- Stats endpoint: `/api/stats`
- Integrations endpoint: `/api/integrations`

**Rollback on Failure**:
- Automatically triggered if deployment fails
- Restores from latest backup
- Rebuilds and restarts container
- Verifies restored deployment

---

## 🧪 Testing

### Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Pytest fixtures
├── test_api.py           # API endpoint tests
└── test_agents.py        # Agent functionality tests
```

### Running Tests Locally

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_health_endpoint

# Run tests by marker
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m smoke          # Smoke tests only
```

### Test Categories

**Unit Tests** (`@pytest.mark.unit`):
- Individual endpoint testing
- Agent structure validation
- Data transformation tests

**Integration Tests** (`@pytest.mark.integration`):
- Full workflow testing
- Multi-endpoint interactions
- State management verification

**Smoke Tests** (`@pytest.mark.smoke`):
- Critical endpoint availability
- Basic functionality verification
- Quick health checks

### Test Coverage

**Current Coverage**:
```
tests/test_api.py
  ✓ 15 unit tests
  ✓ 1 integration test
  ✓ 1 smoke test

tests/test_agents.py
  ✓ 5 unit tests
  ✓ Agent execution tests
  ✓ Task counter verification
```

**Coverage Reports**:
- Terminal output (with `--cov-report=term`)
- HTML report (`htmlcov/index.html`)
- XML report (for Codecov)

---

## 🔍 Code Quality

### Black (Code Formatting)

**Configuration** (`pyproject.toml`):
```toml
[tool.black]
line-length = 127
target-version = ['py310', 'py311', 'py312']
```

**Usage**:
```bash
# Check formatting
black --check .

# Auto-format
black .

# Show diff without applying
black --diff .
```

### isort (Import Sorting)

**Configuration** (`.isort.cfg`):
```ini
[settings]
profile = black
line_length = 127
```

**Usage**:
```bash
# Check imports
isort --check-only .

# Auto-sort imports
isort .

# Show diff
isort --diff .
```

### Flake8 (Linting)

**Configuration** (`.flake8`):
```ini
[flake8]
max-line-length = 127
ignore = E203, E501, W503, W504
```

**Usage**:
```bash
# Run linter
flake8 .

# With statistics
flake8 . --statistics

# Specific file
flake8 main.py
```

### MyPy (Type Checking)

**Configuration** (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
```

**Usage**:
```bash
# Type check main file
mypy main.py

# All Python files
mypy *.py
```

---

## 🔐 Security Scanning

### Bandit (Python Security)

Scans for common security issues in Python code.

**Issues Detected**:
- SQL injection vulnerabilities
- Use of `eval()` or `exec()`
- Hardcoded passwords
- Insecure deserialization
- Weak cryptography

**Usage**:
```bash
# Scan all files
bandit -r .

# JSON output
bandit -r . -f json -o bandit-report.json

# Specific severity
bandit -r . -ll  # Low and above
```

### Safety (Dependency Vulnerabilities)

Checks for known security vulnerabilities in dependencies.

**Usage**:
```bash
# Check requirements
safety check

# JSON output
safety check --json

# Full report
safety check --full-report
```

### Trivy (Container Scanning)

Scans Docker images for vulnerabilities.

**Usage**:
```bash
# Scan image
trivy image aiautodash:latest

# Only critical/high
trivy image --severity CRITICAL,HIGH aiautodash:latest

# SARIF output for GitHub
trivy image --format sarif --output results.sarif aiautodash:latest
```

---

## 🐳 Docker Build

### Local Build

```bash
# Build image
docker build -t aiautodash:local .

# Build with cache
docker build --cache-from aiautodash:latest -t aiautodash:local .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t aiautodash:multi .
```

### GitHub Actions Build

**Automated on**:
- Push to `main`
- Version tags
- Pull requests

**Features**:
- BuildKit caching (GitHub Actions cache)
- Multi-architecture support (amd64, arm64)
- Automatic tagging based on branch/tag
- Push to GitHub Container Registry

**Pull Image**:
```bash
# Latest
docker pull ghcr.io/kmransom56/aiautodash:latest

# Specific version
docker pull ghcr.io/kmransom56/aiautodash:v1.0.0

# Main branch
docker pull ghcr.io/kmransom56/aiautodash:main
```

---

## 🚀 Deployment

### Manual Deployment

**Via GitHub UI**:
1. Go to Actions tab
2. Select "Deploy to Production" workflow
3. Click "Run workflow"
4. Choose environment (production/staging)
5. Optionally specify version
6. Click "Run workflow"

**Via GitHub CLI**:
```bash
# Deploy to production
gh workflow run deploy.yml

# Deploy to staging
gh workflow run deploy.yml -f environment=staging

# Deploy specific version
gh workflow run deploy.yml -f version=v1.0.0
```

### Automatic Deployment

Automatically triggers on push to `main` when these files change:
- `main.py`
- `requirements.txt`
- `Dockerfile`
- `templates/**`
- `static/**`

### Deployment Steps

**On Server** (100.123.10.72):
```bash
# 1. Backup current version
sudo tar -czf /opt/backups/aiautodash/backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C /home/keith/Downloads aiautodashdev-main

# 2. Update files
sudo cp -r /tmp/aiautodash-deploy/* /home/keith/Downloads/aiautodashdev-main/

# 3. Rebuild container
cd /home/keith/chat-copilot
docker compose build aiautodash

# 4. Restart with force-recreate
docker compose up -d --force-recreate aiautodash

# 5. Verify health
curl -f http://localhost:5902/health
```

### Rollback Process

**Automatic on Failure**:
1. Identifies latest backup
2. Extracts to original location
3. Rebuilds container from backup
4. Restarts container
5. Verifies health

**Manual Rollback**:
```bash
# SSH to server
ssh keith@100.123.10.72

# Find backup
ls -t /opt/backups/aiautodash/backup-*.tar.gz | head -1

# Restore
BACKUP="/opt/backups/aiautodash/backup-20251024-120000.tar.gz"
sudo tar -xzf "$BACKUP" -C /home/keith/Downloads/

# Rebuild
cd /home/keith/chat-copilot
docker compose build aiautodash
docker compose up -d --force-recreate aiautodash

# Verify
curl http://localhost:5902/health
```

---

## ⚙️ Configuration

### GitHub Secrets

Required secrets for workflows:

| Secret | Purpose | Where to Add |
|--------|---------|-------------|
| `SSH_PRIVATE_KEY` | SSH access to deployment server | Repository Settings → Secrets |
| `GITHUB_TOKEN` | GitHub API access | Automatically provided |

**Add SSH Key**:
```bash
# Generate key (if needed)
ssh-keygen -t ed25519 -C "github-actions@aiautodash"

# Copy private key
cat ~/.ssh/id_ed25519

# Add to GitHub:
# Settings → Secrets and variables → Actions → New repository secret
# Name: SSH_PRIVATE_KEY
# Value: <paste private key>

# Add public key to server
ssh-copy-id -i ~/.ssh/id_ed25519.pub keith@100.123.10.72
```

### Environment Configuration

**GitHub Environments**:
- `production` - Main deployment (100.123.10.72:5902)
- `staging` - Test deployment (optional)

**Setup Environment**:
1. Go to Settings → Environments
2. Click "New environment"
3. Name: `production`
4. Add protection rules (optional):
   - Required reviewers
   - Wait timer
   - Deployment branches

### Workflow Permissions

**Required Permissions**:
- ✅ Read repository contents
- ✅ Write packages (for Docker registry)
- ✅ Write security events (for Trivy SARIF)
- ✅ Create commit comments (for notifications)

**Configure**:
Settings → Actions → General → Workflow permissions
- Select "Read and write permissions"
- Check "Allow GitHub Actions to create and approve pull requests"

---

## 📊 Monitoring CI/CD

### GitHub Actions Dashboard

**View Workflows**:
- Go to "Actions" tab in repository
- See all workflow runs
- Filter by workflow, branch, or status

**Workflow Status**:
- 🟢 Success - All jobs passed
- 🔴 Failure - One or more jobs failed
- 🟡 In Progress - Currently running
- ⚪ Queued - Waiting to start

### Notifications

**Workflow Notifications**:
- GitHub automatically sends notifications on failure
- Commit comments on deployment status
- Can configure additional notifications via webhooks

**Setup Email Notifications**:
1. GitHub Settings → Notifications
2. Check "Actions" under Email notification preferences
3. Choose notification frequency

### Badges

**Add to README**:
```markdown
![CI](https://github.com/kmransom56/ai-research-platform/workflows/CI%20-%20Test%20and%20Lint/badge.svg)
![Docker](https://github.com/kmransom56/ai-research-platform/workflows/Docker%20Build%20and%20Push/badge.svg)
![Deploy](https://github.com/kmransom56/ai-research-platform/workflows/Deploy%20to%20Production/badge.svg)
```

### Logs and Artifacts

**View Logs**:
1. Click on workflow run
2. Click on job name
3. Expand steps to see detailed logs
4. Download logs (top-right menu)

**Artifacts**:
- Bandit security reports
- Coverage reports
- Test results
- Available for 90 days

**Download Artifacts**:
```bash
# Using GitHub CLI
gh run download <run-id>

# Or via GitHub UI
# Actions → Workflow Run → Artifacts section
```

---

## 🔧 Troubleshooting

### CI Tests Failing

**Check**:
1. Review test output in Actions logs
2. Run tests locally to reproduce
3. Check for environment-specific issues
4. Verify dependencies are up to date

**Common Issues**:
- Import errors: Missing dependencies
- Async test failures: Check `pytest-asyncio`
- Coverage issues: Verify `pytest-cov` installed

### Docker Build Failing

**Check**:
1. Dockerfile syntax
2. Base image availability
3. Build context size
4. Network issues during `pip install`

**Debug Locally**:
```bash
# Build with verbose output
docker build --progress=plain -t aiautodash:debug .

# Check build context
docker build --no-cache -t aiautodash:debug .
```

### Deployment Failing

**Check**:
1. SSH connection to server
2. Server disk space
3. Docker daemon running
4. Port 5902 availability

**Debug**:
```bash
# SSH manually
ssh keith@100.123.10.72

# Check disk space
df -h

# Check Docker
docker ps
docker compose ps

# Check logs
docker compose logs aiautodash
```

### Health Check Failing

**Check**:
1. Container is running
2. Port mapping correct
3. Application startup time
4. Network connectivity

**Verify**:
```bash
# Container status
docker ps | grep aiautodash

# Container logs
docker logs aiautodash

# Manual health check
curl http://localhost:5902/health

# Inside container
docker exec -it aiautodash curl http://localhost:5902/health
```

---

## 📈 Best Practices

### Branch Strategy

**Recommended**:
```
main (production)
  ↑
develop (staging)
  ↑
feature/* (feature branches)
```

**Workflow**:
1. Create feature branch from `develop`
2. Make changes and test locally
3. Create PR to `develop`
4. CI runs automatically
5. Merge to `develop` after approval
6. Deploy to staging
7. Create PR from `develop` to `main`
8. Deploy to production

### Commit Messages

**Format**:
```
feat: Add new feature
fix: Fix bug in agent execution
docs: Update CI/CD documentation
test: Add integration tests
chore: Update dependencies
```

**Conventional Commits**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Testing
- `chore`: Maintenance
- `refactor`: Code refactoring
- `perf`: Performance improvement

### Version Tagging

**Semantic Versioning**:
```bash
# Major version (breaking changes)
git tag -a v2.0.0 -m "Version 2.0.0"

# Minor version (new features)
git tag -a v1.1.0 -m "Version 1.1.0"

# Patch version (bug fixes)
git tag -a v1.0.1 -m "Version 1.0.1"

# Push tags
git push origin --tags
```

### Testing Before Push

**Pre-commit Checklist**:
```bash
# 1. Format code
black .
isort .

# 2. Run linter
flake8 .

# 3. Run tests
pytest

# 4. Check coverage
pytest --cov=. --cov-report=term

# 5. Security scan
bandit -r .
```

### Monitoring After Deploy

**Post-deployment Checks**:
```bash
# 1. Health check
curl http://100.123.10.72:5902/health

# 2. Check version
curl http://100.123.10.72:5902/health | jq '.version'

# 3. Test key endpoints
curl http://100.123.10.72:5902/registry
curl http://100.123.10.72:5902/api/stats

# 4. Check container logs
docker logs aiautodash --tail 50

# 5. Monitor metrics
curl http://100.123.10.72:5902/metrics
```

---

## 🎯 Quick Reference

### Common Commands

```bash
# Run tests
pytest

# Run with coverage
pytest --cov

# Format code
black . && isort .

# Lint code
flake8 .

# Type check
mypy main.py

# Security scan
bandit -r . && safety check

# Build Docker locally
docker build -t aiautodash:local .

# Run container locally
docker run -p 5902:5902 aiautodash:local

# Deploy via CLI
gh workflow run deploy.yml
```

### Workflow URLs

| Workflow | Badge | URL |
|----------|-------|-----|
| CI | `ci.yml` | https://github.com/kmransom56/ai-research-platform/actions/workflows/ci.yml |
| Docker | `docker.yml` | https://github.com/kmransom56/ai-research-platform/actions/workflows/docker.yml |
| Deploy | `deploy.yml` | https://github.com/kmransom56/ai-research-platform/actions/workflows/deploy.yml |

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Build Documentation](https://docs.docker.com/engine/reference/commandline/build/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Flake8 Linting](https://flake8.pycqa.org/)
- [Bandit Security Tool](https://bandit.readthedocs.io/)

---

**Version**: 1.0.0
**Last Updated**: 2025-10-24
**Status**: Production Ready
