# Quick Start Guide

## Local Development (5 minutes)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
✅ Backend running at: http://localhost:8000

### Frontend
```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```
✅ Frontend running at: http://localhost:3000

---

## Deploy to Production (15 minutes)

### Frontend to Vercel
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```
✅ Get your Vercel URL: `https://your-app.vercel.app`

### Backend to Digital Ocean
```bash
# On Digital Ocean Droplet
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv python3-pip nginx supervisor git

mkdir -p /var/www/crypto-backend
cd /var/www/crypto-backend

# Upload your backend files (scp or git clone)
# Then:
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nano .env  # Paste your environment variables

# Setup Supervisor
nano /etc/supervisor/conf.d/crypto-backend.conf
```

Paste:
```ini
[program:crypto-backend]
directory=/var/www/crypto-backend
command=/var/www/crypto-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
autostart=true
autorestart=true
stderr_logfile=/var/log/crypto-backend.err.log
stdout_logfile=/var/log/crypto-backend.out.log
```

```bash
supervisorctl reread && supervisorctl update
supervisorctl start crypto-backend

# Setup Nginx
nano /etc/nginx/sites-available/crypto-backend
```

Paste:
```nginx
server {
    listen 80;
    server_name YOUR_DROPLET_IP;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/crypto-backend /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
ufw allow OpenSSH && ufw allow 'Nginx Full' && ufw enable
```

✅ Backend running at: `http://YOUR_DROPLET_IP`

---

## Update Frontend API URL

In Vercel Dashboard:
- Settings → Environment Variables
- `NEXT_PUBLIC_API_URL` = `http://YOUR_DROPLET_IP`
- Redeploy: `vercel --prod`

---

## Test Your System

1. Open: `https://your-app.vercel.app`
2. Paste a signal:
```
#BTCUSDT P | LONG 🟢
Entry: 42000 (CMP)
TP 1 → 43050
Stop Loss: 39900 ☠️
```
3. Check Active Positions page
4. Verify trade in Binance account

---

## Useful Commands

```bash
# Check backend logs
tail -f /var/log/crypto-backend.out.log

# Restart backend
supervisorctl restart crypto-backend

# Check Nginx status
systemctl status nginx

# View Vercel logs
vercel logs
```

---

## Important Settings

**Default Configuration:**
- Leverage: **20x**
- Position Size: **$1000 per trade**
- SL: **5%** below/above entry
- TP: **2.5%** above/below entry
- Margin Mode: **CROSSED**
- Order Type: **LIMIT** (at signal entry price)

**Change in Trade Management page** in the UI.

---

⚠️ **WARNING**: This is configured for **LIVE TRADING** with real money!

For detailed instructions, see [SETUP.md](./SETUP.md)
