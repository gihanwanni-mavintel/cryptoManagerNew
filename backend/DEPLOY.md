# Complete Backend Deployment Guide

## Step 1: Upload Backend Code (From Your Windows Machine)

```bash
scp -r C:\Users\DELL\Desktop\crypto_position_manager\backend root@YOUR_DROPLET_IP:/tmp/
```

## Step 2: On Droplet - Setup Directory Structure

```bash
# Create application directory
sudo mkdir -p /var/www/crypto-manager
cd /var/www/crypto-manager

# Move backend code from tmp
sudo mv /tmp/backend ./
cd backend

# Clean up local dev files
rm -rf venv __pycache__ app/__pycache__ app/*/__pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

## Step 3: Create Python Virtual Environment

```bash
cd /var/www/crypto-manager/backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Setup Environment Variables

```bash
# Copy production env to .env
cp .env.production .env

# Verify env file
cat .env
```

## Step 5: Initialize Database Tables

```bash
# Make sure venv is activated
source venv/bin/activate

# Create database tables
python3 -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Test database connection
python3 -c "from app.config import settings; print(f'Database: {settings.database_url}')"
```

## Step 6: Test Run Manually (Optional)

```bash
# Activate venv
source venv/bin/activate

# Run server manually to test
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, test:
curl http://localhost:8000/health

# Press Ctrl+C to stop when done testing
```

## Step 7: Setup Systemd Service

```bash
# Copy service file
sudo cp /var/www/crypto-manager/backend/crypto-manager.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable crypto-manager

# Start service
sudo systemctl start crypto-manager

# Check status
sudo systemctl status crypto-manager

# View logs
sudo journalctl -u crypto-manager -f
```

## Step 8: Setup Nginx Reverse Proxy

```bash
# Copy nginx config
sudo cp /var/www/crypto-manager/backend/nginx-config /etc/nginx/sites-available/crypto-manager

# Edit and replace YOUR-DOMAIN with actual domain or IP
sudo nano /etc/nginx/sites-available/crypto-manager

# Enable site
sudo ln -s /etc/nginx/sites-available/crypto-manager /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Check nginx status
sudo systemctl status nginx
```

## Step 9: Verify Deployment

```bash
# Test health endpoint
curl http://your-domain-or-ip/health

# Test API docs
# Open browser: http://your-domain-or-ip/docs
```

## Useful Commands

```bash
# Restart backend
sudo systemctl restart crypto-manager

# View logs
sudo journalctl -u crypto-manager -f
sudo journalctl -u crypto-manager -n 100

# Stop backend
sudo systemctl stop crypto-manager

# Check if running
sudo systemctl status crypto-manager

# Restart nginx
sudo systemctl restart nginx

# View nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```
