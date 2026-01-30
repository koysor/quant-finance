# Deploy to EC2 Workflow Explained

This document explains the `deploy-ec2.yml` GitHub Actions workflow.

## Overview

The workflow automates the deployment of four Streamlit applications to an AWS EC2 instance. It follows a CI/CD pipeline pattern:

```
Code Push → Code Quality → Build Images → Push to GHCR → Deploy to EC2 → Health Check
```

**Key design decisions:**
- Images are built on GitHub runners (not EC2) due to EC2 t2.micro resource constraints
- Images are stored in GitHub Container Registry (GHCR) for reliable, fast deployments
- Pull requests only build images (no deployment) to validate changes without affecting production
- Health checks verify deployment success before marking the workflow complete

## Workflow Triggers

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
```

| Trigger | When | What happens |
|---------|------|--------------|
| `push` | Code merged to main | Full pipeline: quality → build → push → deploy |
| `pull_request` | PR opened/updated | Quality checks + build only (no push, no deploy) |
| `workflow_dispatch` | Manual trigger in GitHub UI | Full pipeline (useful for re-deploys) |

**Best practice:** Separate triggers allow PRs to validate that code compiles and images build successfully without deploying untested code to production.

## Environment Variables

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ghcr.io/${{ github.repository }}
```

| Variable | Value | Purpose |
|----------|-------|---------|
| `REGISTRY` | `ghcr.io` | GitHub Container Registry hostname |
| `IMAGE_PREFIX` | `ghcr.io/koysor/quant-finance` | Base path for all images |

**Best practice:** Define shared values as environment variables to avoid repetition and ensure consistency. If you need to change the registry, you only change it in one place.

## Job 1: Code Quality

```yaml
code-quality:
  runs-on: ubuntu-latest
```

This job validates code formatting and linting before any builds occur.

### Key Commands

```bash
black --check --diff .
```
- `--check` — Exit with error if files need reformatting (doesn't modify files)
- `--diff` — Show what would change (useful for debugging failures)
- `.` — Check all Python files in the repository

**Why:** Ensures consistent code style across the team. Running this first (before expensive Docker builds) fails fast on simple issues.

```bash
ruff check .
```
- Runs the Ruff linter to catch common errors, unused imports, and code smells

**Best practice:** Code quality checks are the first job because they're fast (~10 seconds) and catch issues early. No point building Docker images if the code has linting errors.

## Job 2: Build and Push

```yaml
build-and-push:
  needs: code-quality
  runs-on: ubuntu-latest
  permissions:
    contents: read
    packages: write
```

### Job Dependencies

```yaml
needs: code-quality
```

**Why:** Only runs after code quality passes. This prevents wasting compute resources building images for code that fails linting.

### Permissions

```yaml
permissions:
  contents: read
  packages: write
```

| Permission | Purpose |
|------------|---------|
| `contents: read` | Read repository code |
| `packages: write` | Push images to GHCR |

**Best practice:** Follow the principle of least privilege. Only request the permissions the job actually needs. This limits the blast radius if a workflow is compromised.

### Matrix Strategy

```yaml
strategy:
  matrix:
    include:
      - app: quant-finance
        dockerfile: docker/Dockerfile.quant-finance
      - app: options
        dockerfile: docker/Dockerfile.options
      - app: fixed-income
        dockerfile: docker/Dockerfile.fixed-income
      - app: portfolio-management
        dockerfile: docker/Dockerfile.portfolio-management
```

**Why:** Matrix builds run in parallel. Four separate runners build four images simultaneously, reducing total build time from ~20 minutes (sequential) to ~5 minutes (parallel).

**Best practice:** Use matrix strategies when you have multiple similar tasks. It's more maintainable than duplicating job definitions and automatically parallelises.

### Key Steps

#### Docker Buildx Setup

```yaml
- uses: docker/setup-buildx-action@v3
```

**Why:** Buildx enables advanced features:
- Multi-platform builds (if needed later)
- Better layer caching
- BuildKit optimisations for faster builds

#### GHCR Authentication

```yaml
- uses: docker/login-action@v3
  with:
    registry: ${{ env.REGISTRY }}
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `registry` | `ghcr.io` | Target registry |
| `username` | `${{ github.actor }}` | GitHub username of whoever triggered the workflow |
| `password` | `${{ secrets.GITHUB_TOKEN }}` | Automatic token provided by GitHub Actions |

**Best practice:** Use `GITHUB_TOKEN` instead of personal access tokens. It's automatically provided, scoped to the repository, and expires after the workflow completes.

#### Image Tagging

```yaml
- uses: docker/metadata-action@v5
  with:
    images: ${{ env.IMAGE_PREFIX }}/${{ matrix.app }}
    tags: |
      type=sha,prefix=
      type=raw,value=latest,enable={{is_default_branch}}
```

This generates two tags for each image:

| Tag | Example | Purpose |
|-----|---------|---------|
| SHA | `b9a30ea` | Immutable reference to exact commit |
| `latest` | `latest` | Rolling tag for current production version |

**Best practice:** Always tag with commit SHA for traceability. The `latest` tag is convenient for deployments but SHA tags let you roll back to any specific version.

#### Build and Push

```yaml
- uses: docker/build-push-action@v6
  with:
    context: .
    file: ${{ matrix.dockerfile }}
    push: ${{ github.event_name != 'pull_request' }}
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `context` | `.` | Build context is repository root |
| `file` | `docker/Dockerfile.*` | Path to Dockerfile |
| `push` | `true` (except PRs) | Push to registry |
| `cache-from/to` | `type=gha` | Use GitHub Actions cache |

**Key behaviour:** `push: ${{ github.event_name != 'pull_request' }}` means:
- On push to main → push images to GHCR
- On pull request → build only (validates Dockerfile works, doesn't pollute registry)

**Why caching matters:**
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

Docker layer caching dramatically speeds up builds. If only application code changed (not dependencies), cached layers for pip installs are reused. A full build might take 5 minutes; a cached build takes 30 seconds.

## Job 3: Deploy

```yaml
deploy:
  needs: build-and-push
  runs-on: ubuntu-latest
  if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
```

### Conditional Execution

```yaml
if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
```

**Why:** Only deploy on:
- Push to main (automated deployment)
- Manual trigger (re-deploy or rollback)

Pull requests don't trigger deployment—you don't want untested code in production.

### SSH Deployment

```yaml
- uses: appleboy/ssh-action@v1.0.3
  with:
    host: ${{ secrets.EC2_HOST }}
    username: ec2-user
    key: ${{ secrets.EC2_SSH_KEY }}
    script_stop: true
    command_timeout: 30m
```

| Parameter | Purpose |
|-----------|---------|
| `host` | EC2 IP address (stored as secret) |
| `username` | `ec2-user` (default for Amazon Linux) |
| `key` | SSH private key (stored as secret) |
| `script_stop: true` | Stop on first error |
| `command_timeout: 30m` | Allow time for image pulls |

**Best practice:** Store sensitive values (IP, SSH key) as GitHub Secrets, not in the workflow file.

### Deployment Script

#### Repository Sync

```bash
cd ~/quant-finance || git clone https://github.com/koysor/quant-finance.git ~/quant-finance
cd ~/quant-finance
git fetch origin
git reset --hard origin/main
```

| Command | Purpose |
|---------|---------|
| `cd ... \|\| git clone ...` | Clone if doesn't exist, otherwise cd into it |
| `git fetch origin` | Download latest commits without merging |
| `git reset --hard origin/main` | Force local to match remote exactly |

**Why `reset --hard`:** Ensures EC2 has exactly what's in the repository. Any local modifications are discarded. This prevents "works on my machine" issues where EC2 has stale or modified files.

#### Stop Existing Containers

```bash
docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
docker-compose down --remove-orphans 2>/dev/null || true
```

| Flag | Purpose |
|------|---------|
| `-f docker-compose.prod.yml` | Use production compose file |
| `--remove-orphans` | Remove containers not defined in compose file |
| `2>/dev/null` | Suppress error messages |
| `\|\| true` | Don't fail if containers don't exist |

**Why both commands:** Handles both scenarios—if previously deployed with prod file or dev file. The `|| true` ensures the script continues even if no containers are running.

#### Disk Cleanup

```bash
docker system prune -af --volumes || true
docker builder prune -af || true
sudo rm -rf /tmp/* 2>/dev/null || true
```

| Command | Purpose |
|---------|---------|
| `docker system prune -af --volumes` | Remove all unused images, containers, volumes |
| `docker builder prune -af` | Remove build cache |
| `rm -rf /tmp/*` | Clear temporary files |

**Why this matters:** The t2.micro has only 8GB disk. Old images and build cache accumulate quickly. Without cleanup, deployments fail with "no space left on device".

| Flag | Meaning |
|------|---------|
| `-a` | Remove all unused images (not just dangling) |
| `-f` | Force, don't prompt for confirmation |
| `--volumes` | Also remove unused volumes |

**Best practice:** Clean up before pulling new images, not after. This ensures maximum space is available for the pull operation.

#### Pull Images

```bash
docker pull ghcr.io/koysor/quant-finance/quant-finance:latest
docker pull ghcr.io/koysor/quant-finance/options:latest
docker pull ghcr.io/koysor/quant-finance/fixed-income:latest
docker pull ghcr.io/koysor/quant-finance/portfolio-management:latest
```

**Why explicit pulls:** While `docker-compose up` would pull images automatically, explicit pulls provide:
- Clear progress output in logs
- Easier debugging if a specific image fails to pull
- All images downloaded before any containers start

**Note:** No authentication required because the packages are public.

#### Start Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

| Flag | Purpose |
|------|---------|
| `-f docker-compose.prod.yml` | Use production compose file (pulls from GHCR) |
| `-d` | Detached mode (run in background) |

### Health Check

```bash
sleep 30

SERVICES="quant-finance options fixed-income portfolio-management"
for service in $SERVICES; do
  if ! docker ps | grep -q "$service"; then
    echo "Container $service is not running!"
    docker logs docker-${service}-1 2>/dev/null || docker logs ${service} 2>/dev/null || true
    exit 1
  fi
done

curl -f http://localhost:8501/_stcore/health && echo " Quant Finance OK"
curl -f http://localhost:8502/_stcore/health && echo " Options OK"
curl -f http://localhost:8503/_stcore/health && echo " Fixed Income OK"
curl -f http://localhost:8504/_stcore/health && echo " Portfolio OK"
```

**Two-phase health check:**

1. **Container check** — Verify containers are running (`docker ps`)
2. **Application check** — Verify apps respond to HTTP requests (`curl -f`)

| curl flag | Purpose |
|-----------|---------|
| `-f` | Fail silently on HTTP errors (exit code 22 on 4xx/5xx) |

**Why `sleep 30`:** Streamlit apps take time to initialise. Checking immediately would fail even for successful deployments.

**Best practice:** Always include health checks in deployment pipelines. A deployment that "succeeds" but leaves apps broken is worse than a failed deployment—at least failures are visible.

## Secrets Required

| Secret | Description | How to get it |
|--------|-------------|---------------|
| `EC2_HOST` | EC2 public IP address | AWS Console → EC2 → Instances |
| `EC2_SSH_KEY` | Private SSH key (`.pem` file contents) | Created when launching EC2 instance |

**Best practice:** Rotate SSH keys periodically. Consider using AWS Systems Manager Session Manager instead of SSH keys for better security and auditability.

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GitHub Actions                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐                                                        │
│  │  code-quality    │  Black + Ruff                                          │
│  │  (ubuntu-latest) │  ~10 seconds                                           │
│  └────────┬─────────┘                                                        │
│           │ needs                                                            │
│           ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    build-and-push (matrix: 4 parallel jobs)           │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │   │
│  │  │quant-finance│ │   options   │ │ fixed-income│ │portfolio-mgmt   │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘  │   │
│  │                         ~5 minutes (parallel)                         │   │
│  └────────────────────────────────┬─────────────────────────────────────┘   │
│                                   │ needs                                    │
│                                   ▼                                          │
│                          ┌──────────────────┐                                │
│                          │     deploy       │  SSH → EC2                     │
│                          │ (ubuntu-latest)  │  Pull + Start + Health Check   │
│                          └──────────────────┘  ~2 minutes                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ docker pull
                                    ▼
                    ┌───────────────────────────────┐
                    │      ghcr.io/koysor/          │
                    │      quant-finance/*:latest   │
                    └───────────────────────────────┘
                                    │
                                    │ pulled by
                                    ▼
                    ┌───────────────────────────────┐
                    │         AWS EC2               │
                    │   docker-compose.prod.yml     │
                    │   Ports 8501-8504             │
                    └───────────────────────────────┘
```

## Common Modifications

### Add a new application

1. Add to the matrix:
   ```yaml
   - app: new-app
     dockerfile: docker/Dockerfile.new-app
   ```

2. Add to health check:
   ```bash
   curl -f http://localhost:8505/_stcore/health && echo " New App OK"
   ```

3. Add to `docker-compose.prod.yml`

### Change deployment branch

```yaml
on:
  push:
    branches: [production]  # Change from main
```

### Add staging environment

Duplicate the deploy job with different secrets:
```yaml
deploy-staging:
  needs: build-and-push
  # ... use EC2_STAGING_HOST, EC2_STAGING_SSH_KEY
```
