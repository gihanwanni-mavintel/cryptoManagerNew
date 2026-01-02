# Deployment Checklist

Use this checklist to ensure everything is configured correctly before going live.

## Pre-Deployment

### Database (Neon Cloud)
- [ ] Create Neon account and project
- [ ] Run all SQL table creation scripts
- [ ] Verify tables exist: `users`, `market_messages`, `signal_messages`, `trades`, `trade_management_config`
- [ ] Insert default admin user (username: `admin`, password: `admin123`)
- [ ] Insert default trade config for user_id = 1
- [ ] Test database connection from local machine
- [ ] Copy DATABASE_URL to `.env` file

### Binance API
- [ ] Create Binance account (if not already)
- [ ] Generate API keys (with Futures trading enabled)
- [ ] Add IP restrictions (recommended)
- [ ] Enable Futures trading permissions
- [ ] Test API keys with small test trade
- [ ] Verify API key has sufficient balance
- [ ] **IMPORTANT**: Set `BINANCE_TESTNET=false` for live trading
- [ ] Copy API key and secret to `.env` file

### Telegram
- [ ] Create Telegram account
- [ ] Create API app at https://my.telegram.org/apps
- [ ] Note down `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`
- [ ] Generate session string (using telethon)
- [ ] Join the trading signal Telegram group
- [ ] Get group ID (use @username_to_id_bot)
- [ ] Copy all Telegram credentials to `.env` file

### Environment Variables
- [ ] Backend `.env` file created from `.env.example`
- [ ] All credentials filled in backend `.env`
- [ ] Frontend `.env.local` created from `.env.example`
- [ ] `NEXT_PUBLIC_API_URL` set in frontend `.env.local`
- [ ] No `.env` files committed to Git (check `.gitignore`)

---

## Local Testing

### Backend
- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Backend starts without errors (`uvicorn app.main:app --reload`)
- [ ] Health check works: `http://localhost:8000/health`
- [ ] API docs accessible: `http://localhost:8000/docs`
- [ ] Telegram listener starts (check logs)
- [ ] Binance connection successful (check logs)
- [ ] Database queries work

### Frontend
- [ ] Node.js 18+ installed
- [ ] Dependencies installed (`npm install`)
- [ ] Frontend starts without errors (`npm run dev`)
- [ ] Opens at `http://localhost:3000`
- [ ] Can connect to backend API
- [ ] All pages load correctly:
  - [ ] Home / Manual Trading
  - [ ] Active Positions
  - [ ] Trade Management

### End-to-End Test
- [ ] Paste test signal in Manual Trading page
- [ ] Signal is parsed correctly
- [ ] Trade is created in database
- [ ] Limit order placed on Binance
- [ ] SL and TP orders placed
- [ ] Position shows in Active Positions page
- [ ] Can close position from UI
- [ ] Position closed on Binance
- [ ] Trade marked as CLOSED in database

---

## Frontend Deployment (Vercel)

### Preparation
- [ ] Code committed to Git repository
- [ ] Repository pushed to GitHub/GitLab/Bitbucket
- [ ] `package.json` has correct build script
- [ ] Frontend builds successfully locally (`npm run build`)

### Vercel Setup
- [ ] Vercel account created
- [ ] Vercel CLI installed (`npm i -g vercel`)
- [ ] Logged in to Vercel (`vercel login`)
- [ ] Project deployed (`vercel --prod`)
- [ ] Environment variable added: `NEXT_PUBLIC_API_URL`
- [ ] Deployment successful
- [ ] Note Vercel URL: ___________________________

### Verification
- [ ] Vercel site loads correctly
- [ ] Can navigate between pages
- [ ] Environment variables applied
- [ ] Build logs show no errors

---

## Backend Deployment (Digital Ocean)

### Droplet Creation
- [ ] Digital Ocean account created
- [ ] Droplet created (Ubuntu 22.04, min 1GB RAM)
- [ ] SSH key added or password set
- [ ] Note Droplet IP: ___________________________
- [ ] Can SSH into droplet

### Software Installation
- [ ] System updated (`apt update && apt upgrade`)
- [ ] Python 3.11+ installed
- [ ] Nginx installed
- [ ] Supervisor installed
- [ ] Git installed (if cloning repo)

### Backend Setup
- [ ] Backend code uploaded to `/var/www/crypto-backend`
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] `.env` file created with all credentials
- [ ] Test backend runs manually (`uvicorn app.main:app`)

### Supervisor Configuration
- [ ] Supervisor config created at `/etc/supervisor/conf.d/crypto-backend.conf`
- [ ] Config has correct paths
- [ ] Supervisor reloaded (`supervisorctl reread && supervisorctl update`)
- [ ] Backend started (`supervisorctl start crypto-backend`)
- [ ] Backend status is RUNNING (`supervisorctl status`)
- [ ] Logs show no errors (`tail -f /var/log/crypto-backend.out.log`)

### Nginx Configuration
- [ ] Nginx config created at `/etc/nginx/sites-available/crypto-backend`
- [ ] Config has correct Droplet IP or domain
- [ ] Symlink created in `/etc/nginx/sites-enabled/`
- [ ] Default site removed
- [ ] Nginx config tested (`nginx -t`)
- [ ] Nginx restarted (`systemctl restart nginx`)
- [ ] Nginx enabled on boot (`systemctl enable nginx`)

### Firewall
- [ ] UFW installed
- [ ] SSH allowed (`ufw allow OpenSSH`)
- [ ] HTTP/HTTPS allowed (`ufw allow 'Nginx Full'`)
- [ ] Firewall enabled (`ufw enable`)
- [ ] Firewall status verified (`ufw status`)

### SSL Certificate (Optional but Recommended)
- [ ] Domain name purchased and pointed to Droplet IP
- [ ] Certbot installed
- [ ] SSL certificate obtained (`certbot --nginx -d yourdomain.com`)
- [ ] Auto-renewal configured
- [ ] HTTPS works

### Verification
- [ ] Health endpoint works: `http://YOUR_IP/health`
- [ ] API docs accessible: `http://YOUR_IP/docs`
- [ ] Telegram listener running (check logs)
- [ ] Can create test signal via API
- [ ] Backend stays running after SSH disconnect

---

## Post-Deployment Configuration

### Frontend
- [ ] Update `NEXT_PUBLIC_API_URL` in Vercel to backend URL
- [ ] Redeploy frontend (`vercel --prod`)
- [ ] Verify frontend connects to backend
- [ ] Test signal submission from deployed frontend

### Backend CORS
- [ ] Update CORS origins in `app/main.py` to include Vercel URL
- [ ] Restart backend (`supervisorctl restart crypto-backend`)
- [ ] Verify no CORS errors in browser console

### Database
- [ ] Default trade config has correct values:
  - [ ] max_position_size = 1000
  - [ ] max_leverage = 20
  - [ ] margin_mode = CROSSED
  - [ ] sl_percentage = 5.0
  - [ ] tp_percentage = 2.5

---

## Final Verification

### Functionality Test
- [ ] Open deployed frontend in browser
- [ ] Paste a test signal:
```
#BTCUSDT P | LONG 🟢
Entry: 42000 (CMP)
TP 1 → 43050
Stop Loss: 39900 ☠️
```
- [ ] Signal is parsed correctly
- [ ] Trade is placed on Binance (check Binance account)
- [ ] Position appears in Active Positions page
- [ ] Can close position from UI
- [ ] Trade closed on Binance
- [ ] Telegram listener automatically processes messages

### Monitoring Setup
- [ ] Set up log monitoring:
  - [ ] `tail -f /var/log/crypto-backend.out.log`
  - [ ] `tail -f /var/log/crypto-backend.err.log`
- [ ] Check Binance account balance regularly
- [ ] Set up alerts for:
  - [ ] Backend downtime
  - [ ] Large losses
  - [ ] API errors

### Security
- [ ] No `.env` files in Git repository
- [ ] SSH keys secured
- [ ] Binance API keys have IP restrictions
- [ ] Database password is strong
- [ ] JWT secret is random and secure
- [ ] Consider 2FA for all accounts

---

## Live Trading Checklist

⚠️ **BEFORE GOING LIVE**:
- [ ] Understand that `BINANCE_TESTNET=false` means REAL MONEY
- [ ] Start with small position sizes to test
- [ ] Have sufficient balance in Binance account
- [ ] Monitor first few trades closely
- [ ] Understand the risk of leverage trading
- [ ] Have a plan for managing losses
- [ ] Set alerts for position changes
- [ ] Know how to manually close all positions

### Risk Management
- [ ] Default position size is appropriate ($1000 default)
- [ ] Leverage is not too high (20x default)
- [ ] SL percentage is reasonable (5% default)
- [ ] TP percentage is realistic (2.5% default)
- [ ] Understand liquidation risk
- [ ] Have emergency shutdown plan

---

## Troubleshooting Checklist

If something doesn't work:

### Backend Issues
- [ ] Check supervisor status: `supervisorctl status`
- [ ] Check backend logs: `tail -f /var/log/crypto-backend.out.log`
- [ ] Check error logs: `tail -f /var/log/crypto-backend.err.log`
- [ ] Test database connection
- [ ] Verify environment variables
- [ ] Test Binance API connection
- [ ] Check Nginx logs: `tail -f /var/log/nginx/error.log`

### Frontend Issues
- [ ] Check Vercel deployment logs
- [ ] Verify `NEXT_PUBLIC_API_URL` is correct
- [ ] Check browser console for errors
- [ ] Test API endpoint directly
- [ ] Verify CORS configuration
- [ ] Try rebuilding: `vercel --prod`

### Trading Issues
- [ ] Verify Binance API has Futures enabled
- [ ] Check Binance account balance
- [ ] Verify leverage is set correctly
- [ ] Check symbol is correct (BTCUSDT not BTC)
- [ ] Ensure position size is valid
- [ ] Check Binance API status

---

## Maintenance Tasks

### Daily
- [ ] Check open positions
- [ ] Monitor P&L
- [ ] Review logs for errors
- [ ] Verify Telegram listener is running

### Weekly
- [ ] Review all closed trades
- [ ] Check system performance
- [ ] Update dependencies if needed
- [ ] Backup database
- [ ] Review API rate limits

### Monthly
- [ ] Rotate API keys
- [ ] Review and optimize config
- [ ] Update system packages
- [ ] Review security logs
- [ ] Analyze trading performance

---

## Emergency Procedures

### If System Malfunctions
1. Stop accepting new signals:
   - Set `AUTO_EXECUTE_TRADES=false` in `.env`
   - Restart backend
2. Close all positions manually from UI or Binance
3. Check logs to identify issue
4. Fix issue and test thoroughly before re-enabling

### If Large Loss Occurs
1. Close affected position immediately
2. Review what went wrong (SL not hit? Wrong calculation?)
3. Fix issue before resuming trading
4. Consider reducing position size temporarily

### If Backend Goes Down
1. SSH into droplet
2. Check status: `supervisorctl status`
3. Check logs: `tail -f /var/log/crypto-backend.err.log`
4. Restart: `supervisorctl restart crypto-backend`
5. If needed, reboot droplet
6. Monitor closely after restart

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Backend URL**: _______________
**Frontend URL**: _______________

**Notes**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
