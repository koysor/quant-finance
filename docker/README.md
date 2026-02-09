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

All applications are served via an Nginx reverse proxy on port 80, using path-based routing.

| App | URL |
|-----|-----|
| Quant Finance | http://koysor.duckdns.org/quant/ |
| Options | http://koysor.duckdns.org/options/ |
| Fixed Income | http://koysor.duckdns.org/fixed-income/ |
| Portfolio Management | http://koysor.duckdns.org/portfolio/ |

## Reverse Proxy (Nginx)

An Nginx reverse proxy runs on port 80 and routes requests to the correct Streamlit container based on the URL path. The Nginx configuration is version-controlled at `docker/nginx.conf` and deployed automatically via GitHub Actions.

Each Streamlit app has a `baseUrlPath` configured so that it knows its subpath:

```
Client Request           Nginx                 Docker Container
──────────────           ─────                 ────────────────
/quant/           ──►    proxy_pass :8501  ──► quant-finance    (baseUrlPath=quant)
/options/         ──►    proxy_pass :8502  ──► options           (baseUrlPath=options)
/fixed-income/    ──►    proxy_pass :8503  ──► fixed-income      (baseUrlPath=fixed-income)
/portfolio/       ──►    proxy_pass :8504  ──► portfolio-mgmt    (baseUrlPath=portfolio)
```

The root URL (`/`) redirects to `/quant/`.

## Port Mapping Explained

All Streamlit apps run on port 8501 **inside** their containers. Docker maps each to a unique **external** port on the EC2 host. Nginx then routes path-based URLs to these ports:

```
EC2 Host Port    Container Port    App                   URL Path
─────────────    ──────────────    ─────────────────     ────────────
8501        ──►  8501              quant-finance         /quant/
8502        ──►  8501              options               /options/
8503        ──►  8501              fixed-income          /fixed-income/
8504        ──►  8501              portfolio-management  /portfolio/
```

The `-p` flag syntax: `-p <host-port>:<container-port>`

```bash
docker run -p 8502:8501 options-app
#             │     │
#             │     └── Port inside container (always 8501 for Streamlit)
#             └──────── Port on EC2 (must be unique per app)
```

### Adding New Apps

To deploy another Streamlit app:

1. Choose the next available port (e.g., 8505)
2. Set `--server.baseUrlPath` to the desired URL path
3. Add a corresponding `location` block in `docker/nginx.conf`
4. Remember to add the new port to the EC2 security group

## Local Development

### Build and Run All Applications

```bash
# From the repository root directory
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

3. **Clone and build**
   ```bash
   git clone https://github.com/koysor/quant-finance.git
   cd quant-finance

   sudo docker build -f docker/Dockerfile.quant-finance -t quant-finance-app .
   sudo docker build -f docker/Dockerfile.options -t options-app .
   sudo docker build -f docker/Dockerfile.fixed-income -t fixed-income-app .
   sudo docker build -f docker/Dockerfile.portfolio-management -t portfolio-management-app .
   ```

4. **Run containers**
   ```bash
   sudo docker run -d -p 8501:8501 --name quant-finance --restart unless-stopped quant-finance-app
   sudo docker run -d -p 8502:8501 --name options --restart unless-stopped options-app
   sudo docker run -d -p 8503:8501 --name fixed-income --restart unless-stopped fixed-income-app
   sudo docker run -d -p 8504:8501 --name portfolio --restart unless-stopped portfolio-management-app
   ```

5. **Install and configure Nginx**
   ```bash
   sudo dnf install -y nginx
   sudo cp ~/quant-finance/docker/nginx.conf /etc/nginx/conf.d/streamlit.conf
   sudo nginx -t && sudo systemctl start nginx
   sudo systemctl enable nginx
   ```

### Update Deployed Apps (Automated - Recommended)

Simply push to the `main` branch. GitHub Actions will:
1. Build Docker images on GitHub runners
2. Push images to GHCR
3. SSH into EC2 and pull the new images
4. Restart containers with the updated images
5. Deploy the Nginx configuration and reload Nginx

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
docker-compose -f docker-compose.prod.yml down
docker pull ghcr.io/koysor/quant-finance/quant-finance:latest
docker pull ghcr.io/koysor/quant-finance/options:latest
docker pull ghcr.io/koysor/quant-finance/fixed-income:latest
docker pull ghcr.io/koysor/quant-finance/portfolio-management:latest
docker-compose -f docker-compose.prod.yml up -d
sudo cp ~/quant-finance/docker/nginx.conf /etc/nginx/conf.d/streamlit.conf
sudo nginx -t && sudo systemctl reload nginx
```

### Update Deployed Apps (Manual - Building Locally)

If you need to build images locally on EC2 (not recommended due to resource constraints):

```bash
cd ~/quant-finance
git pull
sudo docker stop quant-finance options fixed-income portfolio
sudo docker rm quant-finance options fixed-income portfolio
sudo docker build -f docker/Dockerfile.quant-finance -t quant-finance-app .
sudo docker build -f docker/Dockerfile.options -t options-app .
sudo docker build -f docker/Dockerfile.fixed-income -t fixed-income-app .
sudo docker build -f docker/Dockerfile.portfolio-management -t portfolio-management-app .
sudo docker run -d -p 8501:8501 --name quant-finance --restart unless-stopped quant-finance-app
sudo docker run -d -p 8502:8501 --name options --restart unless-stopped options-app
sudo docker run -d -p 8503:8501 --name fixed-income --restart unless-stopped fixed-income-app
sudo docker run -d -p 8504:8501 --name portfolio --restart unless-stopped portfolio-management-app
```

**Note:** Building on t2.micro often fails due to memory and disk constraints. Use pre-built images from GHCR instead.

## GitHub Container Registry (GHCR)

Docker images are built on GitHub-hosted runners and published to [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) (GHCR). The packages are publicly visible at:

**https://github.com/koysor?tab=packages&visibility=public**

### Available Images

| Image | Pull Command |
|-------|--------------|
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
│  2. Build & Push      Build 4 Docker images in parallel                  │
│     (GitHub Runner)   Push to ghcr.io/koysor/quant-finance/*            │
│         ↓                                                                │
│  3. Deploy            SSH to EC2, pull images from GHCR                  │
│     (EC2)             docker-compose up + deploy nginx.conf              │
│         ↓                                                                │
│  4. Health Check      Verify all apps respond on their base URL paths    │
└─────────────────────────────────────────────────────────────────────────┘
```

1. **Code quality checks** - Black and Ruff run on GitHub runners
2. **Build and push** - Four Docker images built in parallel on GitHub runners, pushed to GHCR
3. **Deploy to EC2** - SSH into EC2, pull pre-built images from GHCR (no building on EC2), deploy Nginx config
4. **Health checks** - Verify all applications are responding on their base URL paths

### Production vs Local Docker Compose

| File | Purpose | Images |
|------|---------|--------|
| `docker-compose.yml` | Local development | Builds from Dockerfiles |
| `docker-compose.prod.yml` | Production (EC2) | Pulls from GHCR |

The production compose file uses pre-built images:

```yaml
services:
  quant-finance:
    image: ghcr.io/koysor/quant-finance/quant-finance:latest
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
# Check individual app health (include baseUrlPath)
curl http://localhost:8501/quant/_stcore/health
curl http://localhost:8502/options/_stcore/health
curl http://localhost:8503/fixed-income/_stcore/health
curl http://localhost:8504/portfolio/_stcore/health
```

### Check Nginx status
```bash
sudo systemctl status nginx
sudo nginx -t  # test configuration
sudo cat /var/log/nginx/error.log  # view error logs
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
| Quant Finance | http://koysor.duckdns.org/quant/ |
| Options | http://koysor.duckdns.org/options/ |
| Fixed Income | http://koysor.duckdns.org/fixed-income/ |
| Portfolio Management | http://koysor.duckdns.org/portfolio/ |

### Step 3: Nginx Reverse Proxy

The Nginx configuration is managed as part of the repository at `docker/nginx.conf` and deployed automatically via GitHub Actions. To set it up manually for the first time:

```bash
sudo dnf install -y nginx
sudo cp ~/quant-finance/docker/nginx.conf /etc/nginx/conf.d/streamlit.conf
sudo nginx -t
sudo systemctl start nginx
sudo systemctl enable nginx
```

Subsequent updates to the Nginx configuration are deployed automatically when pushing to the `main` branch.

### Step 4: Add Free HTTPS (Optional)

Get a free SSL certificate from Let's Encrypt:

```bash
sudo dnf install -y python3-pip
sudo pip3 install certbot certbot-nginx
sudo certbot --nginx -d koysor.duckdns.org
```

Follow the prompts. Certbot will:
- Obtain SSL certificate
- Configure Nginx for HTTPS
- Set up auto-renewal

Access at: https://koysor.duckdns.org/

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
