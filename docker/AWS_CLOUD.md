# AWS Cloud Usage

This document summarises how Amazon Web Services (AWS) is used by this repository.

## Overview

AWS is used exclusively as an **infrastructure hosting platform** for deploying the Streamlit web applications. There is no programmatic use of AWS services through SDKs or APIs within the application code itself.

## AWS Services Used

### EC2 (Elastic Compute Cloud)

The primary AWS service used is EC2 for hosting Docker containers running the Streamlit applications.  The Docker containers are platform-agnostic and could be deployed on any Linux server with Docker support.

| Configuration    | Value                            |
| ---------------- | -------------------------------- |
| Instance Type    | t2.micro (free tier eligible)    |
| Operating System | Amazon Linux 2                   |
| Public IP        | 13.50.72.89                      |
| Domain           | koysor.duckdns.org (via DuckDNS) |

### Security Groups

The EC2 instance requires the following inbound rules:

| Port | Protocol | Purpose                                          |
| ---- | -------- | ------------------------------------------------ |
| 22   | TCP      | SSH access for deployment                        |
| 80   | TCP      | HTTP (Caddy - ACME challenge and HTTPS redirect) |
| 443  | TCP      | HTTPS (Caddy - application traffic)              |

### Elastic IP (Recommended)

An Elastic IP is used to maintain a static public IP address, preventing IP changes when the instance is stopped/started.

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           GitHub Actions                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Build Docker Images → Push to GHCR                              │    │
│  │  (ghcr.io/koysor/quant-finance/*)                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Pull images
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AWS EC2 Instance                                │
│                            (t2.micro)                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Docker Compose (prod)                         │    │
│  │  ┌─────────┐                                                     │    │
│  │  │  Caddy   │ :80/:443 (HTTPS + Let's Encrypt)                   │    │
│  │  │  (proxy) │──┬─► quant-finance:8501      /                     │    │
│  │  │          │  ├─► options:8501            /options/              │    │
│  │  │          │  ├─► fixed-income:8501       /fixed-income/        │    │
│  │  │          │  ├─► portfolio-mgmt:8501     /portfolio/           │    │
│  │  │          │  └─► host:8505              /maths/                │    │
│  │  └─────────┘                                                     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                     https://koysor.duckdns.org
```

## Deployed Applications

| Application          | URL                                      |
| -------------------- | ---------------------------------------- |
| Quantitative Finance | https://koysor.duckdns.org/              |
| Options              | https://koysor.duckdns.org/options/      |
| Fixed Income         | https://koysor.duckdns.org/fixed-income/ |
| Portfolio Management | https://koysor.duckdns.org/portfolio/    |
| Maths Python         | https://koysor.duckdns.org/maths/        |

## Deployment Method

Deployment is automated via GitHub Actions (`.github/workflows/deploy-ec2.yml`):

1. **Code Quality Checks** - Black formatting and Ruff linting run on GitHub-hosted runners
2. **Build & Push Images** - Docker images are built in parallel on GitHub runners and pushed to GitHub Container Registry (GHCR)
3. **SSH Deployment** - Connects to EC2 via SSH using `appleboy/ssh-action`
4. **Pull Images** - EC2 pulls pre-built images from GHCR + Caddy from Docker Hub (no building on EC2)
5. **Container Orchestration** - Docker Compose starts Caddy reverse proxy and all four Streamlit applications using `docker-compose.prod.yml`
6. **Health Checks** - Verifies all Streamlit apps and Caddy are responding

### GitHub Container Registry (GHCR)

Docker images are publicly available at: **https://github.com/koysor?tab=packages&visibility=public**

| Image | URL |
|-------|-----|
| Quant Finance | `ghcr.io/koysor/quant-finance/quant-finance:latest` |
| Options | `ghcr.io/koysor/quant-finance/options:latest` |
| Fixed Income | `ghcr.io/koysor/quant-finance/fixed-income:latest` |
| Portfolio Management | `ghcr.io/koysor/quant-finance/portfolio-management:latest` |

**Why pre-built images?** Building Docker images on the t2.micro instance is problematic due to limited RAM (1GB), disk space constraints, and slow build times. By building on GitHub's runners and pushing to GHCR, the EC2 instance only needs to pull pre-built images—a fast and reliable operation. See [README.md](README.md) for details.

### GitHub Secrets

| Secret          | Description                    |
| --------------- | ------------------------------ |
| `EC2_HOST`    | EC2 instance public IP address |
| `EC2_SSH_KEY` | Private SSH key for EC2 access |

## Cost Estimation

| Resource                  | Monthly Cost                     |
| ------------------------- | -------------------------------- |
| EC2 t2.micro              | £0 (free tier, first 12 months) |
| DuckDNS domain            | £0 (free service)               |
| Let's Encrypt SSL (Caddy) | £0 (free, automatic)            |
| **After free tier** | ~£7-9/month                     |

## Related Documentation

- [Docker Deployment Guide](README.md) - Detailed deployment instructions
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
