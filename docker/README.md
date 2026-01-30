# Docker Deployment Guide

This directory contains Docker configurations for deploying the Quantitative Finance Streamlit applications.

## Available Applications

| Application | Dockerfile | Port | Description |
|-------------|------------|------|-------------|
| Quantitative Finance | `Dockerfile.quant-finance` | 8501 | Stochastic processes, Greeks, volatility modeling, risk management |
| Options | `Dockerfile.options` | 8502 | Options pricing models, binomial trees, Black-Scholes |
| Fixed Income | `Dockerfile.fixed-income` | 8503 | Bond pricing and fixed income securities |
| Portfolio Management | `Dockerfile.portfolio-management` | 8504 | Modern Portfolio Theory, CAPM, alpha analysis |

## Live URLs

### Via Domain (Recommended)

| App | URL |
|-----|-----|
| Quant Finance | http://koysor.duckdns.org:8501 |
| Options | http://koysor.duckdns.org:8502 |
| Fixed Income | http://koysor.duckdns.org:8503 |
| Portfolio Management | http://koysor.duckdns.org:8504 |
| Maths Python | http://koysor.duckdns.org:8505 |

### Via IP Address

| App | URL |
|-----|-----|
| Quant Finance | http://13.50.72.89:8501 |
| Options | http://13.50.72.89:8502 |
| Fixed Income | http://13.50.72.89:8503 |
| Portfolio Management | http://13.50.72.89:8504 |
| Maths Python | http://13.50.72.89:8505 |

## Port Mapping Explained

All Streamlit apps run on port 8501 **inside** their containers. Docker maps each to a unique **external** port on the EC2 host:

```
EC2 Host Port    Container Port    App
─────────────    ──────────────    ─────────────────────
8501        ──►  8501              quant-finance
8502        ──►  8501              options
8503        ──►  8501              fixed-income
8504        ──►  8501              portfolio-management
8505        ──►  8501              maths-python (separate repo)
```

The `-p` flag syntax: `-p <host-port>:<container-port>`

```bash
docker run -p 8502:8501 options-app
#             │     │
#             │     └── Port inside container (always 8501 for Streamlit)
#             └──────── Port on EC2 (must be unique per app)
```

### Adding New Apps

To deploy another Streamlit app, choose the next available port (8506, 8507, etc.):

```bash
docker run -d -p 8506:8501 --name new-app --restart unless-stopped new-app-image
```

Remember to add the new port to the EC2 security group.

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
- Quantitative Finance: http://localhost:8501
- Options: http://localhost:8502
- Fixed Income: http://localhost:8503
- Portfolio Management: http://localhost:8504

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

### Update Deployed Apps (Automated - Recommended)

Simply push to the `main` branch. GitHub Actions will:
1. Build Docker images on GitHub runners
2. Push images to GHCR
3. SSH into EC2 and pull the new images
4. Restart containers with the updated images

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
│     (EC2)             docker-compose -f docker-compose.prod.yml up       │
│         ↓                                                                │
│  4. Health Check      Verify all apps respond on ports 8501-8504         │
└─────────────────────────────────────────────────────────────────────────┘
```

1. **Code quality checks** - Black and Ruff run on GitHub runners
2. **Build and push** - Four Docker images built in parallel on GitHub runners, pushed to GHCR
3. **Deploy to EC2** - SSH into EC2, pull pre-built images from GHCR (no building on EC2)
4. **Health checks** - Verify all applications are responding

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

### Health Checks

All Dockerfiles include health checks:

- **Endpoint:** `/_stcore/health`
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
curl http://localhost:8501/_stcore/health
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
| Quant Finance | http://koysor.duckdns.org:8501 |
| Options | http://koysor.duckdns.org:8502 |
| Fixed Income | http://koysor.duckdns.org:8503 |
| Portfolio Management | http://koysor.duckdns.org:8504 |
| Maths Python | http://koysor.duckdns.org:8505 |

### Step 3: Remove Port Numbers with Nginx (Optional)

Access apps without ports (e.g., `http://koysor.duckdns.org/options/`).

Connect to EC2 via Instance Connect and run:

```bash
sudo dnf install -y nginx

sudo tee /etc/nginx/conf.d/streamlit.conf > /dev/null <<'EOF'
server {
    listen 80;
    server_name koysor.duckdns.org;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    location /options/ {
        proxy_pass http://localhost:8502/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    location /fixed-income/ {
        proxy_pass http://localhost:8503/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    location /portfolio/ {
        proxy_pass http://localhost:8504/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    location /maths/ {
        proxy_pass http://localhost:8505/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
EOF

sudo systemctl start nginx
sudo systemctl enable nginx
```

Access at:
- http://koysor.duckdns.org/ (Quant Finance)
- http://koysor.duckdns.org/options/
- http://koysor.duckdns.org/fixed-income/
- http://koysor.duckdns.org/portfolio/
- http://koysor.duckdns.org/maths/

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
