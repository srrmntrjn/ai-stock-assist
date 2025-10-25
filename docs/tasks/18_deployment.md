# Task 18: Deployment Guide

**Status:** ⏭️ PENDING

**Estimated Time:** 1 hour

---

## Overview

Deploy the trading bot to a cloud server for 24/7 operation.

---

## Deployment Options

### **Option 1: Railway.app** (Recommended - Easiest)

#### Setup Steps

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Prepare Repository**
   ```bash
   # Make sure code is in GitHub
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

3. **Create Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `ai-stock-assist`

4. **Configure Environment Variables**
   - In Railway dashboard → Variables
   - Add all variables from `.env`:
     ```
     EXCHANGE=mock
     ANTHROPIC_API_KEY=sk-ant-...
     INITIAL_BALANCE=10000
     ... (all other vars)
     ```

5. **Deploy**
   - Railway auto-deploys on git push
   - Monitor logs in dashboard

#### Cost
- $5/month for always-on service
- Free trial available

---

### **Option 2: DigitalOcean Droplet**

#### Setup Steps

1. **Create Droplet**
   - OS: Ubuntu 22.04 LTS
   - Size: Basic $6/month
   - Region: Choose closest to you

2. **SSH into Server**
   ```bash
   ssh root@your-droplet-ip
   ```

3. **Install Dependencies**
   ```bash
   # Update system
   apt update && apt upgrade -y

   # Install Python 3.10+
   apt install python3.10 python3-pip python3-venv -y

   # Install git
   apt install git -y
   ```

4. **Clone Repository**
   ```bash
   cd /opt
   git clone https://github.com/yourusername/ai-stock-assist.git
   cd ai-stock-assist
   ```

5. **Setup Environment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Create .env file
   nano .env
   # (paste your environment variables)
   ```

6. **Create Systemd Service**
   ```bash
   nano /etc/systemd/system/trading-bot.service
   ```

   ```ini
   [Unit]
   Description=AI Trading Bot
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/ai-stock-assist
   Environment="PATH=/opt/ai-stock-assist/venv/bin"
   ExecStart=/opt/ai-stock-assist/venv/bin/python src/scheduler.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start Service**
   ```bash
   systemctl daemon-reload
   systemctl enable trading-bot
   systemctl start trading-bot

   # Check status
   systemctl status trading-bot

   # View logs
   journalctl -u trading-bot -f
   ```

---

### **Option 3: Docker Deployment**

#### Create Dockerfile

```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY .env .env

# Run bot
CMD ["python", "src/scheduler.py"]
```

#### Build and Run

```bash
# Build image
docker build -t ai-trading-bot .

# Run container
docker run -d \
  --name trading-bot \
  --restart unless-stopped \
  --env-file .env \
  ai-trading-bot

# View logs
docker logs -f trading-bot

# Stop
docker stop trading-bot
```

---

### **Option 4: Local (Development)**

#### Using Screen

```bash
# Install screen
sudo apt install screen  # Linux
brew install screen      # Mac

# Start screen session
screen -S trading-bot

# Run bot
python src/scheduler.py

# Detach: Ctrl+A, then D

# Reattach later
screen -r trading-bot

# Kill session
screen -X -S trading-bot quit
```

---

## Post-Deployment Checklist

- [ ] Bot is running and logs are visible
- [ ] First iteration completed successfully
- [ ] Market data fetching works
- [ ] AI model responding
- [ ] Trades being simulated (if mock mode)
- [ ] Logs rotating properly
- [ ] Set up monitoring/alerts

---

## Monitoring

### View Logs

**Railway:** Dashboard → Logs tab

**DigitalOcean:**
```bash
# Systemd logs
journalctl -u trading-bot -f

# Or file logs
tail -f /opt/ai-stock-assist/logs/trading_bot.log
```

**Docker:**
```bash
docker logs -f trading-bot
```

### Key Metrics to Monitor

- Iteration count (should increment every 3 min)
- API call success rate
- Trade execution
- Portfolio value changes
- Error rates

---

## Updating the Bot

### Railway
```bash
# Just push to GitHub
git push origin main
# Railway auto-deploys
```

### DigitalOcean
```bash
# SSH into server
ssh root@your-droplet-ip

# Pull updates
cd /opt/ai-stock-assist
git pull

# Restart service
systemctl restart trading-bot
```

### Docker
```bash
# Rebuild
docker build -t ai-trading-bot .

# Stop old container
docker stop trading-bot
docker rm trading-bot

# Start new container
docker run -d --name trading-bot --restart unless-stopped --env-file .env ai-trading-bot
```

---

## Troubleshooting

### Bot not starting
```bash
# Check logs for errors
journalctl -u trading-bot -n 50

# Check .env file
cat .env

# Validate config
python -c "from src.config import settings; settings.validate_config()"
```

### API rate limits
- Add delays between API calls
- Use caching for market data
- Reduce polling frequency

### Out of memory
- Increase droplet size
- Monitor memory usage: `htop`
- Check for memory leaks

---

## Security Best Practices

1. **Never commit `.env` to Git**
2. **Use SSH keys** (not passwords)
3. **Enable firewall** on server
4. **Keep dependencies updated**
5. **Monitor API key usage**
6. **Use separate API keys** for test/production

---

## Production Cutover (Mock → Coinbase)

When ready to trade real money:

1. **Open Coinbase Financial Markets account**
2. **Generate API keys**
3. **Update `.env`:**
   ```bash
   EXCHANGE=coinbase
   COINBASE_API_KEY=your_real_key
   COINBASE_SECRET=your_real_secret
   ENABLE_TRADING=true
   ```
4. **Start with small capital** ($500-1000)
5. **Monitor closely** for first 24 hours
6. **Gradually increase** if profitable

---

## Cost Summary

| Option | Monthly Cost | Setup Time | Difficulty |
|--------|-------------|------------|-----------|
| Railway | $5 | 10 min | Easy |
| DigitalOcean | $6 | 30 min | Medium |
| Docker (local) | $0 | 15 min | Medium |
| AWS EC2 | Free (1yr) | 45 min | Hard |

**Recommendation:** Start with Railway for simplicity

---

## Next Steps

1. Choose deployment option
2. Deploy bot
3. Monitor for 24-48 hours
4. Review performance
5. Iterate and improve
6. Consider production cutover when profitable
