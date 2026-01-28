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

| Port      | Protocol | Purpose                            |
| --------- | -------- | ---------------------------------- |
| 22        | TCP      | SSH access for deployment          |
| 8501-8505 | TCP      | Streamlit application access       |
| 80        | TCP      | HTTP (optional, for reverse proxy) |
| 443       | TCP      | HTTPS (optional, for SSL)          |

### Elastic IP (Recommended)

An Elastic IP is used to maintain a static public IP address, preventing IP changes when the instance is stopped/started.

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS EC2 Instance                         │
│                         (t2.micro)                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Docker Compose                         │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │  │
│  │  │ Quant       │ │ Options     │ │ Fixed       │         │  │
│  │  │ Finance     │ │ App         │ │ Income      │         │  │
│  │  │ :8501       │ │ :8502       │ │ :8503       │         │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘         │  │
│  │  ┌─────────────┐                                          │  │
│  │  │ Portfolio   │                                          │  │
│  │  │ Management  │                                          │  │
│  │  │ :8504       │                                          │  │
│  │  └─────────────┘                                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    koysor.duckdns.org
```

## Deployed Applications

| Application          | Port | URL                                     |
| -------------------- | ---- | --------------------------------------- |
| Quantitative Finance | 8501 | http://koysor.duckdns.org/              |
| Options              | 8502 | http://koysor.duckdns.org/options/      |
| Fixed Income         | 8503 | http://koysor.duckdns.org/fixed-income/ |
| Portfolio Management | 8504 | http://koysor.duckdns.org/portfolio/    |

## Deployment Method

Deployment is automated via GitHub Actions (`.github/workflows/deploy-ec2.yml`):

1. **Code Quality Checks** - Black formatting and Ruff linting run on GitHub-hosted runners
2. **SSH Deployment** - On successful checks, connects to EC2 via SSH using `appleboy/ssh-action`
3. **Docker Build** - Clones/updates repository and builds Docker images on EC2
4. **Container Orchestration** - Docker Compose starts all four Streamlit applications
5. **Health Checks** - Verifies all applications are responding on their respective ports

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
| Let's Encrypt SSL         | £0 (free, if configured)        |
| **After free tier** | ~£7-9/month                     |

## Related Documentation

- [Docker Deployment Guide](README.md) - Detailed deployment instructions
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
