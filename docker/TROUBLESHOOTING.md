# Troubleshooting Guide

Common issues and solutions for the Docker/EC2 deployment.

## Connection Issues

### "Site can't be reached" / Connection timeout

**Cause:** Security group not allowing traffic on the port.

**Fix:**
1. EC2 Console → **Security Groups** → Select your group
2. **Edit inbound rules**
3. Add rule: Type `Custom TCP`, Port `8501-8505`, Source `0.0.0.0/0`
4. **Save rules**

### "Not Secure" warning in browser

**Cause:** Using HTTP instead of HTTPS.

**Fix:** This is cosmetic for personal use. For HTTPS:
- Use CloudFlare (free) as a proxy
- Or install Let's Encrypt SSL certificate

### IP address changed after reboot

**Cause:** No Elastic IP assigned.

**Fix:**
1. EC2 Console → **Elastic IPs** → **Allocate**
2. Select the IP → **Actions** → **Associate**
3. Choose your instance
4. Update `EC2_HOST` GitHub secret with new IP

---

## Docker Issues

### Check container status

```bash
sudo docker ps -a
```

| STATUS | Meaning |
|--------|---------|
| `Up X minutes` | Running normally |
| `Exited (0)` | Stopped gracefully |
| `Exited (1)` | Crashed with error |
| `Restarting` | Crash loop |

### View container logs

```bash
# Last 50 lines
sudo docker logs --tail 50 quant-finance

# Follow logs in real-time
sudo docker logs -f options

# All logs
sudo docker logs maths-python
```

### Container won't start

```bash
# Check the error
sudo docker logs <container-name>

# Run interactively to debug
sudo docker run -it --entrypoint /bin/bash maths-python-app
```

### "Port already in use" error

```bash
# Find what's using the port
sudo lsof -i :8501

# Stop the conflicting container
sudo docker stop <container-name>

# Or kill the process
sudo kill <PID>
```

### Container keeps restarting

```bash
# Check logs for the crash reason
sudo docker logs --tail 100 <container-name>

# Common causes:
# - Out of memory (OOM killed)
# - Missing dependencies
# - Application error
```

### Remove and recreate container

```bash
sudo docker stop quant-finance
sudo docker rm quant-finance
sudo docker run -d -p 8501:8501 --name quant-finance --restart unless-stopped quant-finance-app
```

---

## Build Issues

### "Killed" during docker build

**Cause:** Out of memory (t2.micro has only 1GB RAM).

**Fix:** Add swap space:
```bash
sudo dd if=/dev/zero of=/swapfile bs=128M count=16
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```

### "No space left on device"

**Cause:** Docker images filling up disk.

**Fix:**
```bash
# Remove unused images
sudo docker system prune -a

# Check disk usage
df -h

# Remove old images
sudo docker image prune -a
```

### Build takes too long

**Cause:** Rebuilding everything from scratch.

**Fix:** Use layer caching - don't change `pyproject.toml` unless necessary.

---

## SSH/CI-CD Issues

### "Permission denied (publickey)"

**Cause:** SSH key mismatch.

**Fix:**
1. Generate new key locally:
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/quant-finance-deploy -N ""
   ```

2. Add public key to EC2 (via Instance Connect):
   ```bash
   echo "YOUR_PUBLIC_KEY" >> ~/.ssh/authorized_keys
   ```

3. Update `EC2_SSH_KEY` GitHub secret with the private key.

### "Host key verification failed"

**Cause:** EC2 IP changed, SSH remembers old host key.

**Fix (local):**
```bash
ssh-keygen -R 13.50.72.89
```

### GitHub Actions workflow fails

1. Check the logs: `https://github.com/koysor/quant-finance/actions`
2. Common issues:
   - `EC2_HOST` secret incorrect
   - `EC2_SSH_KEY` secret has wrong format
   - EC2 instance stopped
   - Security group blocking SSH (port 22)

---

## Application Issues

### Streamlit health check failing

```bash
# Test manually
curl http://localhost:8501/_stcore/health

# Should return: {"status":"ok"}
```

### App loads but shows error

```bash
# Check application logs
sudo docker logs -f quant-finance

# Common causes:
# - Missing Python dependencies
# - File not found errors
# - Import errors
```

### App is slow

**Causes:**
- t2.micro has limited CPU/RAM
- Multiple apps competing for resources

**Fixes:**
- Upgrade to t3.small (~$15/month)
- Or stop unused apps:
  ```bash
  sudo docker stop fixed-income portfolio
  ```

---

## Useful Commands Reference

### Docker

```bash
# List running containers
sudo docker ps

# List all containers (including stopped)
sudo docker ps -a

# Stop all containers
sudo docker stop $(sudo docker ps -q)

# Start all containers
sudo docker start quant-finance options fixed-income portfolio maths-python

# Restart a container
sudo docker restart quant-finance

# Remove all stopped containers
sudo docker container prune

# Remove all unused images
sudo docker image prune -a

# Check disk usage
sudo docker system df
```

### System

```bash
# Check memory usage
free -h

# Check disk usage
df -h

# Check running processes
top

# Check what's using a port
sudo lsof -i :8501
```

### Logs

```bash
# Docker logs
sudo docker logs <container-name>

# System logs
sudo journalctl -u docker

# Last 100 lines
sudo docker logs --tail 100 <container-name>
```

---

## Quick Recovery

If everything is broken, start fresh:

```bash
# Stop and remove all containers
sudo docker stop $(sudo docker ps -aq)
sudo docker rm $(sudo docker ps -aq)

# Remove all images
sudo docker rmi $(sudo docker images -q)

# Rebuild and run
cd ~/quant-finance
git pull
sudo docker build -f docker/Dockerfile.quant-finance -t quant-finance-app .
sudo docker build -f docker/Dockerfile.options -t options-app .
sudo docker build -f docker/Dockerfile.fixed-income -t fixed-income-app .
sudo docker build -f docker/Dockerfile.portfolio-management -t portfolio-management-app .

sudo docker run -d -p 8501:8501 --name quant-finance --restart unless-stopped quant-finance-app
sudo docker run -d -p 8502:8501 --name options --restart unless-stopped options-app
sudo docker run -d -p 8503:8501 --name fixed-income --restart unless-stopped fixed-income-app
sudo docker run -d -p 8504:8501 --name portfolio --restart unless-stopped portfolio-management-app

cd ~/maths-python
git pull
sudo docker build -f docker/Dockerfile -t maths-python-app .
sudo docker run -d -p 8505:8501 --name maths-python --restart unless-stopped maths-python-app
```

---

## Getting Help

1. Check container logs first: `sudo docker logs <container-name>`
2. Check AWS EC2 console for instance status
3. Check GitHub Actions for CI/CD errors
4. Verify security group rules allow traffic
