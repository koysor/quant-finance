# AWS Cloud Usage

This document summarises how Amazon Web Services (AWS) is used by this repository.

## Overview

AWS is used exclusively as an **infrastructure hosting platform** for deploying the Streamlit web applications. There is no programmatic use of AWS services through SDKs or APIs within the application code itself.

## AWS Services Used

### EC2 (Elastic Compute Cloud)

The primary AWS service used is EC2 for hosting Docker containers running the Streamlit applications.  The Docker containers are platform-agnostic and could be deployed on any Linux server with Docker support.

| Configuration    | Value                            |
| ---------------- | -------------------------------- |
| Instance Type    | t3.micro (2 vCPU burstable, 1 GiB RAM) |
| Region / AZ      | eu-north-1 (Stockholm) / eu-north-1a   |
| Operating System | Amazon Linux 2023                |
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

An Elastic IP is used to maintain a static public IP address, preventing IP changes when the instance is stopped/started. The address (`13.50.72.89`) was unchanged after the instance was stopped and restarted in October 2026, which indicates an Elastic IP is attached.

### Stopped instance

If the instance is stopped, the deploy job fails at the SSH step with `dial tcp ***:22: i/o timeout`. Start it from EC2 Console (region **eu-north-1**) → Instances → Instance state → Start instance, then re-run the failed deploy jobs. The instance was stopped when the AWS account's free plan lapsed in 2026; it came back after the account was upgraded to a paid plan (29 September 2026) and the instance was started manually. Starting it does not change `EC2_HOST` while the Elastic IP stays attached.

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
│                            (t3.micro)                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Docker Compose (prod)                         │    │
│  │  ┌─────────┐                                                     │    │
│  │  │  Caddy   │ :80/:443 (HTTPS + Let's Encrypt)                   │    │
│  │  │  (proxy) │──┬─► quant-finance:8501      /quant/               │    │
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
| Quantitative Finance | https://koysor.duckdns.org/quant/        |
| Options              | https://koysor.duckdns.org/options/      |
| Fixed Income         | https://koysor.duckdns.org/fixed-income/ |
| Portfolio Management | https://koysor.duckdns.org/portfolio/    |
| Maths Python         | https://koysor.duckdns.org/maths/        |
| Flash Cards          | https://koysor.duckdns.org/flashcards/   |

The bare root (`https://koysor.duckdns.org/`) permanently redirects to `/quant/`. Flash Cards is a Flask app deployed from the `quant-finance-flash-cards` repository (host port 8506); see its `docker/README.md`.

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

**Why pre-built images?** Building Docker images on the t3.micro instance is problematic due to limited RAM (1GB), disk space constraints, and slow build times. By building on GitHub's runners and pushing to GHCR, the EC2 instance only needs to pull pre-built images—a fast and reliable operation. See [README.md](README.md) for details.

### GitHub Secrets

| Secret          | Description                    |
| --------------- | ------------------------------ |
| `EC2_HOST`    | EC2 instance public IP address |
| `EC2_SSH_KEY` | Private SSH key for EC2 access |

## Cost Estimation

The AWS account is on a **paid plan** (upgraded 29 September 2026); the free tier has ended, so everything is pay-as-you-go. Check actual spend in the AWS console under Billing and Cost Management → Cost Explorer.

| Resource                  | Billing                                                  |
| ------------------------- | -------------------------------------------------------- |
| EC2 t3.micro              | Hourly while running; not charged for compute when stopped |
| EBS root volume           | Monthly, charged even while the instance is stopped      |
| Public IPv4 / Elastic IP  | Hourly, charged while allocated (attached or not)        |
| Data transfer out         | Per GB above the monthly allowance                       |
| DuckDNS domain            | Free                                                     |
| Let's Encrypt SSL (Caddy) | Free, automatic                                          |

## Monitoring and Alerts

| Layer | What it does | Where |
| ----- | ------------ | ----- |
| UptimeRobot | External availability and uptime history for the live apps | Public status page linked from the [repository README](../README.md#app-availability-monitoring) |
| Deploy health checks | `curl -f .../_stcore/health` against each Streamlit app after every deploy; the workflow fails if one does not answer | `.github/workflows/deploy-ec2.yml` |
| Docker restart policy | `restart: unless-stopped` brings a crashed container back up | `docker-compose.prod.yml` |
| CloudWatch CPU alarm | Emails the owner when the instance's CPU is high | `eu-north-1` (see below) |
| AWS budget | Emails the owner when spend approaches the monthly limit | AWS Budgets (see below) |

Memory is **not** monitored: CloudWatch cannot see memory on EC2 without the CloudWatch agent installed on the instance. A container killed for running out of memory is restarted silently by Docker. UptimeRobot only notices if the outage lasts long enough to be caught by a check.

### CloudWatch CPU alarm

Created on 17 October 2026 in `eu-north-1`.

| Setting | Value |
| ------- | ----- |
| Alarm name | `quant-finance-ec2-high-cpu` |
| Metric | `AWS/EC2` `CPUUtilization` for the instance |
| Condition | Average > 80% for 3 consecutive 5-minute periods (15 minutes) |
| Missing data | Treated as not breaching (so a stopped instance does not alarm) |
| Action | Publishes to the SNS topic `quant-finance-alerts`, which emails the owner |

The email subscription to the topic must be confirmed once (click the link in AWS's confirmation email); until then no alert emails are sent. A burstable t3.micro exhausts its CPU credits under sustained load, so this alarm is the early warning for the apps being CPU-starved.

### Budget alert

| Setting | Value |
| ------- | ----- |
| Budget name | `monthly-cost-15-usd` |
| Limit | USD 15 per month (cost budget) |
| Alert 1 | Actual spend above 80% of the limit |
| Alert 2 | Forecast spend above 100% of the limit |
| Delivery | Email to the owner (budget emails need no confirmation) |

## AWS CLI

The AWS CLI (v2) is used for administration from a laptop. The deployments themselves do not use it: the workflows deploy over SSH with `appleboy/ssh-action`, so no AWS credentials are stored in the repository for deployment.

### Install

On Ubuntu, install v2 from the snap's `v2/stable` channel. The default `latest/stable` channel is AWS CLI **v1**, and `apt install awscli` may be an old version or unavailable.

```bash
sudo snap install aws-cli --classic --channel=v2/stable
aws --version        # should report aws-cli/2.x
```

### Sign in

Prefer short-lived credentials from `aws login` over long-lived access keys:

```bash
aws login            # opens a browser; add --remote if no browser is available
aws sts get-caller-identity   # confirm which identity you are using
aws logout           # when finished
```

If `aws login` is not available, create an IAM user (no console access) with only the permissions needed, create a CLI access key for it, run `aws configure` with the region `eu-north-1`, and delete the key when finished. Notes:

- Do not use the root user for routine work. `aws login` can sign in as root, and `get-caller-identity` shows `:root` in the ARN when it does. Log out afterwards.
- Never commit access keys, and never paste them into chat or issues.
- The `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and related secrets in the GitHub repositories were set in January 2026 and are not referenced by any workflow (only `EC2_HOST`, `EC2_SSH_KEY` and the built-in `GITHUB_TOKEN` are). Consider deleting them if the keys are no longer needed.

### Useful commands

The instance is in `eu-north-1`, so pass `--region eu-north-1` (or set `AWS_REGION`). AWS Budgets is a global service served from `us-east-1`.

```bash
# Instance state, type and public IP
aws ec2 describe-instances --region eu-north-1 \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name,PublicIpAddress]' --output table

# Start a stopped instance (see "Stopped instance" above), then re-run the deploy jobs
aws ec2 start-instances --region eu-north-1 --instance-ids <instance-id>

# Alarm state and subscribers
aws cloudwatch describe-alarms --region eu-north-1 --alarm-names quant-finance-ec2-high-cpu \
  --query 'MetricAlarms[].[AlarmName,StateValue]' --output table
aws sns list-subscriptions-by-topic --region eu-north-1 --topic-arn <topic-arn>

# Budget and its alerts
aws budgets describe-budget --region us-east-1 --account-id <account-id> --budget-name monthly-cost-15-usd
aws budgets describe-notifications-for-budget --region us-east-1 --account-id <account-id> --budget-name monthly-cost-15-usd
```

Find the account ID with `aws sts get-caller-identity --query Account --output text` and the topic ARN with `aws sns list-topics --region eu-north-1`.

## Related Documentation

- [Docker Deployment Guide](README.md) - Detailed deployment instructions
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
