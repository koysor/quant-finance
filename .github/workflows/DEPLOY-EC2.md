# Deploy to EC2 Workflow Explained

This document explains the `deploy-ec2.yml` GitHub Actions workflow.

## Overview

The workflow automates the deployment of four Streamlit applications to an AWS EC2 instance. It follows a CI/CD pipeline pattern:

```
Code Push → Code Quality → Build Base → Build App Images → Push to GHCR → Deploy to EC2 → Health Check
```

**Key design decisions:**
- Images are built on GitHub runners (not EC2) due to EC2 t3.micro resource constraints
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
uv sync --locked
```
- Installs the tools at the versions pinned in `uv.lock`, so a new Ruff release cannot fail a deploy without a code change

```bash
uv run ruff check .
```
- Runs the Ruff linter to catch common errors, unused imports, and code smells

```bash
uv run ruff format --check --diff .
```
- `--check` — Exit with error if files need reformatting (doesn't modify files)
- `--diff` — Show what would change (useful for debugging failures)
- `.` — Check all Python files in the repository

**Why:** Ensures consistent code style across the team. Running this first (before expensive Docker builds) fails fast on simple issues.

**Best practice:** Code quality checks are the first job because they're fast (~10 seconds) and catch issues early. No point building Docker images if the code has linting errors.

## Job 2: Build

```yaml
build:
  needs: code-quality
  runs-on: ubuntu-latest
  permissions:
    contents: read
    packages: write
```

This job builds all five images (the shared base and the four apps) in a single [Buildx bake](https://docs.docker.com/build/bake/) run, defined in `docker/docker-bake.hcl`. The base image holds the Python dependencies and the `src/` package; each app image adds only its thin application layer on top.

### Why one bake run

Each app is built `FROM` the base image **of the same run**: the bake file passes the `base` target to the apps as a named build context (`contexts = { quant-finance-base = "target:base" }`). The apps are never built on a base image pulled from the registry.

Building the apps on `base:latest` from the registry had two flaws:
- **Pull requests tested the wrong base.** Pull requests push nothing, so their apps were built on the base from the last merge to main. A pull request that changed dependencies (for example from Dependabot, which cannot push packages) never built or tested its apps with them.
- **Concurrent builds raced.** Two merges in quick succession could build one commit's apps on the other's base.

BuildKit builds the base once and the four apps in parallel, so one job is no slower than the previous five.

### Permissions

| Permission | Purpose |
|------------|---------|
| `contents: read` | Read repository code |
| `packages: write` | Push images to GHCR |

**Best practice:** Follow the principle of least privilege. Only request the permissions the job actually needs. This limits the blast radius if a workflow is compromised.

### Key Steps

#### GHCR Authentication

```yaml
- uses: docker/login-action@v4
  if: github.event_name != 'pull_request'
  with:
    registry: ${{ env.REGISTRY }}
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

Pull requests push nothing, so they skip the login.

**Best practice:** Use `GITHUB_TOKEN` instead of personal access tokens. It's automatically provided, scoped to the repository, and expires after the workflow completes.

#### Build and Push

```yaml
- uses: docker/bake-action@v6
  env:
    IMAGE_PREFIX: ${{ env.IMAGE_PREFIX }}
    TAG: ${{ github.sha }}
    PUSH_LATEST: ${{ github.ref == 'refs/heads/main' && github.event_name != 'pull_request' }}
    GHA_CACHE: true
  with:
    source: .
    files: docker/docker-bake.hcl
    push: ${{ github.event_name != 'pull_request' }}
```

The environment variables set the bake file's variables:

| Variable | Value | Purpose |
|----------|-------|---------|
| `TAG` | Full commit SHA | Immutable tag naming the exact build; the deploy job uses it |
| `PUSH_LATEST` | `true` on main | Also tag `latest`, for pulling the current version by hand |
| `GHA_CACHE` | `true` | Cache layers in the GitHub Actions cache, one scope per image |

**Key behaviour:** `push: ${{ github.event_name != 'pull_request' }}` means:
- On push to main → push images to GHCR
- On pull request → build only (validates the Dockerfiles and dependencies, doesn't pollute the registry)

**Why caching matters:** Docker layer caching dramatically speeds up builds. If only application code changed (not dependencies), cached layers for dependency installs are reused. A full build might take 5 minutes; a cached build takes 30 seconds.

To build the same images locally (loaded into Docker, nothing pushed):

```bash
docker buildx bake -f docker/docker-bake.hcl --load
```

## Job 3: Deploy

```yaml
deploy:
  needs: build
  runs-on: ubuntu-latest
  if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
  concurrency:
    group: deploy-ec2
    cancel-in-progress: false
```

### One Deploy at a Time

All deploys share one concurrency group. When a deploy is already running, a newer one waits for it to finish instead of running alongside it. GitHub keeps at most one deploy waiting: a newer one replaces it, so the newest commit is always the one deployed last.

**Why:** Deploys stop, prune and recreate the containers on a single host. Two at once collide (`Conflict. The container name ... is already in use`), which happened when several pull requests were merged in quick succession.

### Pinned to the Commit

The deploy steps receive the commit SHA as `IMAGE_TAG`. On the host the deploy:
1. Checks out that commit (`git reset --hard "$IMAGE_TAG"`), so the compose file and Caddyfile match the images.
2. Pulls the app images tagged with that SHA.
3. Starts them: `docker-compose.prod.yml` uses `${IMAGE_TAG:-latest}` for each app image.

**Why:** `latest` names whatever was pushed most recently, not a particular build. A SHA names exactly one build, so the running version is known.

**Rolling back:** The SHA-tagged images stay in GHCR. To redeploy an earlier version, run `docker-compose -f docker-compose.prod.yml up -d` on the host with `IMAGE_TAG` set to that commit's full SHA, after checking that commit out.

### Conditional Execution

```yaml
if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
```

**Why:** Only deploy on:
- Push to main (automated deployment)
- Manual trigger (re-deploy or rollback)

Pull requests don't trigger deployment—you don't want untested code in production.

### SSH Deployment

The workflow uses the OpenSSH client that is already installed on the GitHub runner, not a third-party SSH action. A "Set up SSH" step writes the key and an `ec2` host alias to `~/.ssh/config`:

```yaml
- name: Set up SSH
  env:
    EC2_HOST: ${{ secrets.EC2_HOST }}
    EC2_SSH_KEY: ${{ secrets.EC2_SSH_KEY }}
  run: |
    install -m 700 -d ~/.ssh
    printf '%s\n' "$EC2_SSH_KEY" > ~/.ssh/ec2
    chmod 600 ~/.ssh/ec2
    cat >> ~/.ssh/config <<EOF
    Host ec2
      HostName $EC2_HOST
      User ec2-user
      IdentityFile ~/.ssh/ec2
      ...
    EOF
```

Each remote step then sends its script as the ssh command:

```yaml
- name: Deploy to EC2 via SSH
  timeout-minutes: 30
  run: |
    script=$(cat <<'REMOTE'
    set -e
    ...
    REMOTE
    )
    ssh -n ec2 "$script"
```

| Setting | Purpose |
|-----------|---------|
| `EC2_HOST`, `EC2_SSH_KEY` | EC2 address and SSH private key, stored as secrets and passed via `env` |
| `User ec2-user` | Default user for Amazon Linux |
| `BatchMode yes` | Fail instead of prompting |
| `StrictHostKeyChecking accept-new` | Trust the host key on first contact |
| `ConnectTimeout 30`, `ConnectionAttempts 3` | Retry a flaky connection |
| `ServerAliveInterval 30`, `ServerAliveCountMax 4` | Drop a dead connection instead of hanging |
| `set -e` | Stop on first error |
| `timeout-minutes: 30` | Allow time for image pulls |
| `ssh -n` | Give the remote side an empty stdin, so `docker-compose exec` cannot consume the script |

**Why not `appleboy/ssh-action`:** it downloads its `drone-ssh` binary from GitHub releases on every run, so an outage of GitHub's release downloads fails the deploy before it reaches the server. That happened to maths-python on 2026-11-08 (HTTP 504). The runner's own `ssh` needs no download.

**Best practice:** Store sensitive values (IP, SSH key) as GitHub Secrets, not in the workflow file.

### Deployment Script

#### Repository Sync

```bash
cd ~/quant-finance || git clone https://github.com/koysor/quant-finance.git ~/quant-finance
cd ~/quant-finance
git fetch origin
git reset --hard "$IMAGE_TAG"
```

| Command | Purpose |
|---------|---------|
| `cd ... \|\| git clone ...` | Clone if doesn't exist, otherwise cd into it |
| `git fetch origin` | Download latest commits without merging |
| `git reset --hard "$IMAGE_TAG"` | Check out exactly the commit being deployed |

**Why `reset --hard` to the commit:** Ensures EC2 has exactly the compose file and Caddyfile of the commit whose images are being deployed, even if main has moved on since. Any local modifications are discarded. This prevents "works on my machine" issues where EC2 has stale or modified files.

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

**Why this matters:** EC2's default root volume is only 8GB. Old images and build cache accumulate quickly. Without cleanup, deployments fail with "no space left on device".

| Flag | Meaning |
|------|---------|
| `-a` | Remove all unused images (not just dangling) |
| `-f` | Force, don't prompt for confirmation |
| `--volumes` | Also remove unused volumes |

**Best practice:** Clean up before pulling new images, not after. This ensures maximum space is available for the pull operation.

#### Pull Images

```bash
for app in quant-finance options fixed-income portfolio-management; do
  docker pull "ghcr.io/koysor/quant-finance/$app:$IMAGE_TAG"
done
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
sleep 45

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

**Why `sleep 45`:** Streamlit apps take time to initialise. Checking immediately would fail even for successful deployments.

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
│  │  code-quality    │  Ruff check + Ruff format                              │
│  │  (ubuntu-latest) │  ~10 seconds                                           │
│  └────────┬─────────┘                                                        │
│           │ needs                                                            │
│           ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │               build (one bake run, docker/docker-bake.hcl)            │   │
│  │                     ┌───────────────────────────┐                     │   │
│  │                     │ base (Python deps + src/) │                     │   │
│  │                     └─────────────┬─────────────┘                     │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │   │
│  │  │quant-finance│ │   options   │ │ fixed-income│ │portfolio-mgmt   │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘  │   │
│  │        apps built on this run's base; tagged with the commit SHA      │   │
│  └────────────────────────────────┬─────────────────────────────────────┘   │
│                                   │ needs                                    │
│                                   ▼                                          │
│                          ┌──────────────────┐                                │
│                          │     deploy       │  SSH → EC2, one at a time      │
│                          │ (ubuntu-latest)  │  Pull + Start + Health Check   │
│                          └──────────────────┘  ~2 minutes                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ docker pull
                                    ▼
                    ┌───────────────────────────────┐
                    │      ghcr.io/koysor/          │
                    │   quant-finance/*:<sha>       │
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
  needs: build
  # ... use EC2_STAGING_HOST, EC2_STAGING_SSH_KEY
```
