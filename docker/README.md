# Docker Deployment Guide

This directory contains Docker configurations for deploying the Quantitative Finance Streamlit applications.

## Available Applications

| Application | Dockerfile | Port | URL Path | Description |
|-------------|------------|------|----------|-------------|
| Quantitative Finance | `Dockerfile.quant-finance` | 8501 | `/quant/` | Stochastic processes, Greeks, volatility modelling, risk management |
| Options | `Dockerfile.options` | 8502 | `/options/` | Options pricing models, binomial trees, Black-Scholes |
| Fixed Income | `Dockerfile.fixed-income` | 8503 | `/fixed-income/` | Bond pricing and fixed income securities |
| Portfolio Management | `Dockerfile.portfolio-management` | 8504 | `/portfolio/` | Modern Portfolio Theory, CAPM, alpha analysis |

## Live URLs

| App | URL |
|-----|-----|
| Quant Finance | https://koysor.duckdns.org/ |
| Options | https://koysor.duckdns.org/options/ |
| Fixed Income | https://koysor.duckdns.org/fixed-income/ |
| Portfolio Management | https://koysor.duckdns.org/portfolio/ |
| Maths Python | https://koysor.duckdns.org/maths/ |

All traffic is served over HTTPS via a [Caddy](https://caddyserver.com/) reverse proxy with automatic Let's Encrypt certificates.

## Production Architecture

In production, a Caddy reverse proxy sits in front of all Streamlit containers. Apps are not exposed directly on host ports — all traffic goes through Caddy on ports 80 (HTTP, redirects to HTTPS) and 443 (HTTPS).

```
Internet (HTTPS :443)
        │
   ┌────▼─────┐
   │   Caddy   │  Automatic Let's Encrypt certificates
   │  (proxy)  │  HTTP → HTTPS redirect
   └────┬──────┘
        ├──► quant-finance:8501      /
        ├──► options:8501            /options/
        ├──► fixed-income:8501       /fixed-income/
        ├──► portfolio-management:8501  /portfolio/
        └──► maths-python:8501       /maths/
```

### How It Works

- All Streamlit containers run on port 8501 internally and use `expose` (Docker network only, not on host)
- Non-root apps set `STREAMLIT_SERVER_BASE_URL_PATH` so Streamlit generates correct internal URLs for their path prefix
- Caddy handles TLS termination, certificate renewal, WebSocket upgrades, and path-based routing
- The `Caddyfile` in this directory defines all routing rules
- Certificate data is stored in the `caddy_data` Docker volume (persists across deployments)

## Local Development

### Build and Run All Applications

The app Dockerfiles depend on a shared base image that must be built first:

```bash
# From the repository root directory

# 1. Build the shared base image (contains Python deps + src/)
docker build -f docker/Dockerfile.base -t quant-finance-base .

# 2. Build and start all app containers
cd docker
docker-compose up --build

# Run in detached mode
docker-compose up --build -d

# Stop all containers
docker-compose down
```

**Local URLs:**
- Quantitative Finance: http://localhost:8501/quant/
- Options: http://localhost:8502/options/
- Fixed Income: http://localhost:8503/fixed-income/
- Portfolio Management: http://localhost:8504/portfolio/

### Build Individual Images

```bash
# From the repository root directory

# Build base first (required by all app images)
docker build -f docker/Dockerfile.base -t quant-finance-base .

# Then build individual app images
docker build -f docker/Dockerfile.quant-finance -t quant-finance-app .
docker build -f docker/Dockerfile.options -t options-app .
docker build -f docker/Dockerfile.fixed-income -t fixed-income-app .
docker build -f docker/Dockerfile.portfolio-management -t portfolio-management-app .
```

### Run Individual Containers

```bash
docker run -d -p 8501:8501 --name quant-finance quant-finance-app
docker run -d -p 8502:8501 --name options options-app
docker run -d -p 8503:8501 --name fixed-income fixed-income-app
docker run -d -p 8504:8501 --name portfolio portfolio-management-app
```

## AWS EC2 Deployment (Free Tier)

The apps are deployed on an AWS EC2 t2.micro instance (free tier eligible).

### Manual Deployment

1. **SSH into EC2 (via EC2 Instance Connect)**
   - Go to EC2 Console → Instances → Select instance → Connect → EC2 Instance Connect

2. **Install Docker (first time only)**
   ```bash
   sudo dnf update -y
   sudo dnf install -y docker git
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -aG docker ec2-user
   ```

3. **Clone and deploy**
   ```bash
   git clone https://github.com/koysor/quant-finance.git
   cd quant-finance/docker
   docker volume create caddy_data
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Update Deployed Apps (Automated - Recommended)

Simply push to the `main` branch. GitHub Actions will:
1. Build Docker images on GitHub runners
2. Push images to GHCR
3. SSH into EC2 and pull the new images
4. Restart containers with the updated images via Caddy

```bash
git push origin main
# Monitor at: https://github.com/koysor/quant-finance/actions
```

### Update Deployed Apps (Manual - Using Pre-Built Images)

If you need to manually update the EC2 deployment using images from GHCR:

```bash
cd ~/quant-finance
git pull
cd docker
docker volume create caddy_data 2>/dev/null || true
docker-compose -f docker-compose.prod.yml down
docker pull ghcr.io/koysor/quant-finance/base:latest
docker pull ghcr.io/koysor/quant-finance/quant-finance:latest
docker pull ghcr.io/koysor/quant-finance/options:latest
docker pull ghcr.io/koysor/quant-finance/fixed-income:latest
docker pull ghcr.io/koysor/quant-finance/portfolio-management:latest
docker pull ghcr.io/koysor/maths-python/maths-python:latest
docker pull caddy:2-alpine
docker-compose -f docker-compose.prod.yml up -d
```

## GitHub Container Registry (GHCR)

Docker images are built on GitHub-hosted runners and published to [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) (GHCR). The packages are publicly visible at:

**https://github.com/koysor?tab=packages&visibility=public**

### Available Images

| Image | Pull Command |
|-------|--------------|
| Base (shared deps) | `docker pull ghcr.io/koysor/quant-finance/base:latest` |
| Quant Finance | `docker pull ghcr.io/koysor/quant-finance/quant-finance:latest` |
| Options | `docker pull ghcr.io/koysor/quant-finance/options:latest` |
| Fixed Income | `docker pull ghcr.io/koysor/quant-finance/fixed-income:latest` |
| Portfolio Management | `docker pull ghcr.io/koysor/quant-finance/portfolio-management:latest` |

### Why Pre-Built Images?

Building Docker images on the EC2 t2.micro instance has several drawbacks:

1. **Resource constraints** - The t2.micro has only 1GB RAM and limited CPU. Building images with large dependencies (NumPy, SciPy, Pandas) frequently causes out-of-memory errors and very slow builds.

2. **Disk space** - Building images requires significant temporary disk space for layers and caches. The t2.micro's 8GB default storage fills up quickly, causing failed builds.

3. **Build time** - Builds that take seconds on a modern laptop can take 10+ minutes on t2.micro, during which the applications are unavailable.

4. **Reliability** - Pre-built images are tested and verified before deployment. If an image fails to build on GitHub Actions, it won't be deployed, preventing broken deployments.

By building on GitHub's runners (which have 7GB RAM and fast CPUs) and pushing to GHCR, the EC2 instance only needs to pull the pre-built images—a fast and reliable operation.

### Image Tags

Each image is tagged with:
- `latest` - Updated on every push to the `main` branch
- `<sha>` - Git commit SHA for traceability (e.g., `b9a30ea`)

## CI/CD with GitHub Actions

Automatic deployment on every push to `main`.

### Setup

1. **Add GitHub Secrets** (Settings → Secrets → Actions):

   | Secret | Value |
   |--------|-------|
   | `EC2_HOST` | `13.50.72.89` |
   | `EC2_SSH_KEY` | Contents of your `.pem` file |

2. **Push to deploy**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

3. **Monitor** at https://github.com/koysor/quant-finance/actions

### How It Works

The workflow at `.github/workflows/deploy-ec2.yml`:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GitHub Actions Pipeline                          │
├─────────────────────────────────────────────────────────────────────────┤
│  1. Code Quality      Black formatting + Ruff linting                    │
│         ↓                                                                │
│  2. Build Base        Build shared base image (Python deps + src/)       │
│     (GitHub Runner)   Push to ghcr.io/koysor/quant-finance/base         │
│         ↓                                                                │
│  3. Build & Push      Build 4 thin app images in parallel                │
│     (GitHub Runner)   Push to ghcr.io/koysor/quant-finance/*            │
│         ↓                                                                │
│  4. Deploy            SSH to EC2, pull base + app images + Caddy         │
│     (EC2)             docker-compose -f docker-compose.prod.yml up       │
│         ↓                                                                │
│  5. Health Check      Verify all apps + Caddy are responding             │
└─────────────────────────────────────────────────────────────────────────┘
```

1. **Code quality checks** - Black and Ruff run on GitHub runners
2. **Build base image** - Shared base image with Python deps and `src/` modules, pushed to GHCR
3. **Build and push** - Four thin app Docker images built in parallel on GitHub runners, pushed to GHCR
4. **Deploy to EC2** - SSH into EC2, pull base image first (app images share its layers), then app images + Caddy
5. **Health checks** - Verify all Streamlit apps and Caddy reverse proxy are responding

### Production vs Local Docker Compose

| File | Purpose | Images |
|------|---------|--------|
| `docker-compose.yml` | Local development | Builds from Dockerfiles |
| `docker-compose.prod.yml` | Production (EC2) | Pulls from GHCR |

The production compose file uses pre-built images and includes Caddy for HTTPS:

```yaml
services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
  quant-finance:
    image: ghcr.io/koysor/quant-finance/quant-finance:latest
    expose:
      - "8501"
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STREAMLIT_SERVER_HEADLESS` | Run without browser | `true` |
| `STREAMLIT_SERVER_PORT` | Application port | `8501` |
| `STREAMLIT_SERVER_ADDRESS` | Bind address | `0.0.0.0` |
| `STREAMLIT_SERVER_BASE_URL_PATH` | URL subpath for reverse proxy routing | App-specific (e.g., `quant`, `options`) |

### Health Checks

All Dockerfiles include health checks using the app's base URL path:

- **Endpoint:** `/<baseUrlPath>/_stcore/health` (e.g., `/quant/_stcore/health`)
- **Interval:** 30 seconds
- **Timeout:** 10 seconds
- **Retries:** 3

### Security

- Images run as non-root user (`appuser`)
- Only necessary files are copied (see `.dockerignore`)
- No secrets stored in images
- Streamlit ports are not exposed on the host (only accessible via Caddy)
- All traffic encrypted via HTTPS (TLS 1.2+)

## Troubleshooting

### Check container status
```bash
sudo docker ps -a
```

### View logs
```bash
sudo docker logs quant-finance
sudo docker logs -f options  # follow logs
```

### Restart a container
```bash
sudo docker restart quant-finance
```

### Health check failing
```bash
# Check individual app health via docker exec
cd ~/quant-finance/docker
docker-compose -f docker-compose.prod.yml exec -T quant-finance curl -f http://localhost:8501/_stcore/health
docker-compose -f docker-compose.prod.yml exec -T options curl -f http://localhost:8501/_stcore/health
docker-compose -f docker-compose.prod.yml exec -T fixed-income curl -f http://localhost:8501/_stcore/health
docker-compose -f docker-compose.prod.yml exec -T portfolio-management curl -f http://localhost:8501/_stcore/health
```

### Check Caddy status
```bash
docker logs quant-finance-caddy-1           # view Caddy logs
docker logs -f quant-finance-caddy-1        # follow Caddy logs
curl -sf -o /dev/null http://localhost:80 && echo "Caddy OK"
```

### Out of memory

The t2.micro has 1GB RAM. If builds fail:
```bash
# Add swap space
sudo dd if=/dev/zero of=/swapfile bs=128M count=16
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Custom Domain Setup (DuckDNS)

Free domain via [DuckDNS](https://www.duckdns.org).

### Step 1: Register Domain

1. Go to https://www.duckdns.org
2. Sign in with Google/GitHub
3. Create a subdomain (e.g., `koysor`)
4. Enter your EC2 IP: `13.50.72.89`
5. Click **update ip**

### Step 2: Test It

Wait 1-2 minutes, then access:

| App | URL |
|-----|-----|
| Quant Finance | https://koysor.duckdns.org/ |
| Options | https://koysor.duckdns.org/options/ |
| Fixed Income | https://koysor.duckdns.org/fixed-income/ |
| Portfolio Management | https://koysor.duckdns.org/portfolio/ |
| Maths Python | https://koysor.duckdns.org/maths/ |

### Step 3: Reverse Proxy and HTTPS (Caddy)

HTTPS is handled automatically by the Caddy reverse proxy in `docker-compose.prod.yml`. Caddy:

- Provisions free Let's Encrypt TLS certificates automatically
- Redirects HTTP to HTTPS
- Handles WebSocket upgrades for Streamlit
- Routes path-based URLs to the correct container

**Configuration:** The routing rules are defined in `docker/Caddyfile`.

**Certificates:** Stored in the `caddy_data` Docker volume. This volume is declared as `external` so it survives `docker system prune`. Create it once before first deployment:

```bash
docker volume create caddy_data
```

**EC2 Security Group:** Ensure ports 80 and 443 are open for inbound traffic:

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 80 | TCP | `0.0.0.0/0` | HTTP (ACME challenge + redirect to HTTPS) |
| 443 | TCP | `0.0.0.0/0` | HTTPS (application traffic) |

Ports 8501-8505 can optionally be removed from the security group as they are no longer needed externally.

**First-time setup notes:**
- If nginx was previously installed, stop and disable it first: `sudo systemctl stop nginx && sudo systemctl disable nginx`
- Initial certificate provisioning takes a few seconds on first `docker-compose up`
- Caddy handles certificate renewal automatically (no cron jobs needed)

### Update DuckDNS IP When It Changes

If your EC2 IP changes (e.g., after reboot without Elastic IP):

1. Go to https://www.duckdns.org
2. Update the IP for your subdomain
3. Update `EC2_HOST` GitHub secret

## Cost

| Resource | Monthly Cost |
|----------|-------------|
| EC2 t2.micro | **$0** (free tier, first 12 months) |
| DuckDNS domain | **$0** (free) |
| Let's Encrypt SSL | **$0** (free) |
| After free tier | ~$8-10/month |
