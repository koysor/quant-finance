# Docker Deployment Guide

This directory contains Docker configurations for deploying the Quantitative Finance Streamlit applications to AWS.

## Available Applications

| Application | Dockerfile | Description |
|-------------|------------|-------------|
| Quantitative Finance | `Dockerfile.quant-finance` | Stochastic processes, Greeks, volatility modeling, risk management |
| Options | `Dockerfile.options` | Options pricing models, binomial trees, Black-Scholes |
| Fixed Income | `Dockerfile.fixed-income` | Bond pricing and fixed income securities |
| Portfolio Management | `Dockerfile.portfolio-management` | Modern Portfolio Theory, CAPM, alpha analysis |

## Local Development

### Build and Run All Applications

```bash
# From the docker directory
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
docker run -p 8501:8501 quant-finance-app
docker run -p 8501:8501 options-app
docker run -p 8501:8501 fixed-income-app
docker run -p 8501:8501 portfolio-management-app
```

## AWS Deployment

### Prerequisites

- AWS CLI configured with appropriate credentials
- Docker installed locally
- An AWS ECR repository for each application

### Push to Amazon ECR

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com

# Create ECR repositories (if not exists)
aws ecr create-repository --repository-name quant-finance-app
aws ecr create-repository --repository-name options-app
aws ecr create-repository --repository-name fixed-income-app
aws ecr create-repository --repository-name portfolio-management-app

# Tag and push images
docker tag quant-finance-app:latest <account-id>.dkr.ecr.<region>.amazonaws.com/quant-finance-app:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/quant-finance-app:latest

# Repeat for other applications...
```

### AWS App Runner

App Runner is the simplest option for deploying containerized web applications.

1. Go to AWS App Runner console
2. Create a new service
3. Select "Container registry" → "Amazon ECR"
4. Choose your ECR image
5. Configure:
   - Port: `8501`
   - CPU: 1 vCPU (minimum)
   - Memory: 2 GB (recommended for data processing)
6. Deploy

### AWS ECS (Fargate)

For more control over networking and scaling:

1. Create an ECS cluster
2. Create a task definition:
   ```json
   {
     "family": "quant-finance-task",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "containerDefinitions": [
       {
         "name": "quant-finance",
         "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/quant-finance-app:latest",
         "portMappings": [
           {
             "containerPort": 8501,
             "protocol": "tcp"
           }
         ],
         "healthCheck": {
           "command": ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"],
           "interval": 30,
           "timeout": 10,
           "retries": 3,
           "startPeriod": 5
         }
       }
     ]
   }
   ```
3. Create a service with an Application Load Balancer
4. Configure target group health checks to use `/_stcore/health`

### AWS Elastic Beanstalk

1. Create a `Dockerrun.aws.json` file:
   ```json
   {
     "AWSEBDockerrunVersion": "1",
     "Image": {
       "Name": "<account-id>.dkr.ecr.<region>.amazonaws.com/quant-finance-app:latest",
       "Update": "true"
     },
     "Ports": [
       {
         "ContainerPort": 8501,
         "HostPort": 8501
       }
     ]
   }
   ```
2. Deploy using EB CLI or console

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STREAMLIT_SERVER_HEADLESS` | Run without browser | `true` |
| `STREAMLIT_SERVER_PORT` | Application port | `8501` |
| `STREAMLIT_SERVER_ADDRESS` | Bind address | `0.0.0.0` |

### Health Checks

All Dockerfiles include health checks compatible with AWS load balancers:

- **Endpoint:** `/_stcore/health`
- **Interval:** 30 seconds
- **Timeout:** 10 seconds
- **Start period:** 5 seconds
- **Retries:** 3

### Security

- Images run as non-root user (`appuser`)
- Only necessary files are copied (see `.dockerignore`)
- No secrets stored in images

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs <container-id>

# Run interactively for debugging
docker run -it --entrypoint /bin/bash quant-finance-app
```

### Health check failing

```bash
# Test health endpoint manually
curl http://localhost:8501/_stcore/health
```

### Out of memory

Increase container memory allocation. Recommended minimum: 2 GB for data-intensive operations.

### Slow cold starts

Consider using AWS App Runner with provisioned concurrency or ECS with minimum task count > 0.
