# Project Overview - Crypto Position Manager

## System Architecture

This is a **full-stack cryptocurrency trading automation system** that bridges Telegram trading signals with Binance Futures trading.

### High-Level Flow

```
Telegram Signal → Python Backend → Database → Binance API
                       ↓
                  Next.js UI (Monitor & Control)
```

---

## Component Breakdown

### 1. Backend (Python FastAPI)

**Location**: `backend/`

**Purpose**: Core trading engine that handles signal processing, trade execution, and position management.

#### Key Services

**a) Telegram Listener** (`app/services/telegram_listener.py`)
- Connects to Telegram using Telethon
- Monitors specified group for new messages
- Triggers signal parsing for each message
- Runs continuously in background

**b) Signal Parser** (`app/services/telegram_parser.py`)
- Extracts trading information from message text
- Parses: pair, direction (LONG/SHORT), entry price
- Calculates SL and TP based on percentages:
  - **LONG**: SL = Entry × (1 - 5%), TP = Entry × (1 + 2.5%)
  - **SHORT**: SL = Entry × (1 + 5%), TP = Entry × (1 - 2.5%)
- Returns structured `ParsedSignalData` object

**c) Binance Service** (`app/services/binance_service.py`)
- Handles all Binance API interactions
- Main functions:
  - `open_position()`: Places LIMIT entry + SL + TP orders
  - `close_position()`: Closes position with market order
  - `get_positions()`: Fetches active positions from Binance
  - `set_leverage()`: Sets leverage for symbol
  - `set_margin_type()`: Sets CROSSED or ISOLATED margin
- Uses FAPI (Futures API) endpoints
- Implements request signing for authentication

**d) Trade Service** (`app/services/trade_service.py`)
- Orchestrates the complete trading workflow
- Main flow:
  1. Receives signal (from Telegram or manual input)
  2. Stores raw message in `market_messages` table
  3. Parses signal and stores in `signal_messages` table
  4. Creates trade record in `trades` table
  5. Executes trade on Binance via `BinanceService`
  6. Updates trade record with order IDs and status
- Manages trade configuration (leverage, position size, etc.)
- Syncs database with actual Binance positions

#### API Endpoints

**Signals** (`app/routers/signals.py`)
- `POST /api/signals/parse` - Parse manual signal
- `GET /api/signals` - Get signal history
- `GET /api/signals/active/count` - Get today's signal count

**Trades** (`app/routers/trades.py`)
- `GET /api/trades/positions` - Get active positions
- `POST /api/trades/close/{id}` - Close specific position
- `GET /api/trades/pnl` - Get total P&L
- `POST /api/trades/sync` - Sync with Binance

**Configuration** (`app/routers/config.py`)
- `GET /api/config` - Get trade settings
- `PUT /api/config` - Update settings
- `POST /api/config/reset` - Reset to defaults

#### Database Models

**Models** (`app/models/database_models.py`):
- `User` - User accounts
- `MarketMessage` - Raw Telegram messages
- `SignalMessage` - Parsed signal data
- `Trade` - Trade records with P&L
- `TradeManagementConfig` - User settings

---

### 2. Frontend (Next.js)

**Location**: `frontend/`

**Purpose**: User interface for monitoring signals, positions, and managing configuration.

#### Pages

**a) Home / Manual Trading** (`src/app/page.tsx`)
- Main signal input interface
- Paste Telegram signals manually
- View recent signal history
- Shows active signal count
- Triggers trade execution on submit

**b) Active Positions** (`src/app/positions/page.tsx`)
- Displays all open Binance positions
- Real-time P&L display (absolute and percentage)
- Color-coded position cards (green profit, red loss)
- One-click position close button
- Refresh button to sync with Binance
- Shows position details:
  - Entry price
  - Quantity
  - Leverage
  - Stop Loss
  - Take Profit
  - Liquidation price
  - Current margin

**c) Trade Management** (`src/app/trade-management/page.tsx`)
- Configure trading parameters:
  - Maximum position size (USD)
  - Maximum leverage (1-125x)
  - Margin mode toggle (ISOLATED/CROSSED)
- Save/Reset configuration
- Displays current active settings

#### API Client (`src/lib/api.ts`)

Provides type-safe API calls:
```typescript
signalsApi.parseSignal()
signalsApi.getSignals()
tradesApi.getPositions()
tradesApi.closePosition()
configApi.getConfig()
configApi.updateConfig()
```

---

### 3. Database (PostgreSQL via Neon)

**Provider**: Neon Cloud (serverless PostgreSQL)

#### Schema

**users**
- Stores user accounts
- Default: admin/admin123 (hashed)

**market_messages**
- Raw Telegram messages
- Fields: sender, text, timestamp
- Used for audit trail

**signal_messages**
- Parsed signal data
- Fields: pair, setup_type, entry, stop_loss, take_profit, channel
- Links to original message

**trades**
- Trade execution records
- Fields: pair, side, leverage, entry_price, quantity, stop_loss, take_profit
- Status tracking: PENDING → OPEN → CLOSED
- P&L calculation stored
- Links to signal and Binance order IDs

**trade_management_config**
- Per-user trading settings
- Default values used for all trades
- Updatable via UI

---

## Trading Logic Deep Dive

### Signal Reception

**Automatic (Telegram)**:
1. Telethon client connects using session string
2. Monitors group ID for new messages
3. On message received:
   - Extract text content
   - Pass to `TelegramParser.parse_message()`
   - If parsed successfully → create trade

**Manual (UI)**:
1. User pastes signal text
2. Frontend sends to `/api/signals/parse`
3. Backend parses and creates trade
4. Returns success/failure to UI

### Order Execution Sequence

When a valid signal is processed:

```
1. Parse Signal
   ↓
2. Store in Database (signal_messages)
   ↓
3. Get User Config (leverage, position size, margin mode)
   ↓
4. Create Trade Record (status: PENDING)
   ↓
5. Binance: Set Leverage
   ↓
6. Binance: Set Margin Type
   ↓
7. Calculate Quantity (position_size / entry_price)
   ↓
8. Place LIMIT Entry Order (at signal entry price)
   ↓
9. Place Stop Loss Order (STOP_MARKET, reduceOnly)
   ↓
10. Place Take Profit Order (TAKE_PROFIT_MARKET, reduceOnly)
    ↓
11. Update Trade Record (status: OPEN/PENDING based on fill)
    ↓
12. Return Result to User
```

### Position Lifecycle

**States**:
- `PENDING` - LIMIT order placed but not filled yet
- `OPEN` - Position active on Binance
- `CLOSED` - Position closed (manual, SL hit, TP hit)
- `CANCELLED` - Order/trade cancelled

**Closing Methods**:
1. **Manual**: User clicks close button → Market order
2. **Stop Loss Hit**: Binance triggers SL order automatically
3. **Take Profit Hit**: Binance triggers TP order automatically
4. **Liquidation**: Binance force-closes (extreme price move)

**Syncing**:
- Frontend polls `/api/trades/positions` periodically
- Backend queries Binance `/fapi/v2/positionRisk`
- Matches DB trades with Binance positions
- Updates status for externally closed positions

---

## Configuration Management

### Default Settings

Set via environment variables (`backend/.env`):
```
DEFAULT_LEVERAGE=20
DEFAULT_POSITION_SIZE=1000
DEFAULT_SL_PERCENTAGE=5.0
DEFAULT_TP_PERCENTAGE=2.5
DEFAULT_MARGIN_MODE=CROSSED
```

### Runtime Updates

User can change via Trade Management UI:
- Position size
- Leverage
- Margin mode

Changes are:
1. Saved to `trade_management_config` table
2. Applied to all future trades
3. Existing positions not affected

---

## Security Features

### API Authentication

**Binance**:
- Uses API key + secret
- HMAC SHA256 signature on all requests
- Timestamp validation to prevent replay attacks

**Telegram**:
- Session-based authentication
- Pre-authenticated session string

### Data Protection

- Environment variables never committed (`.gitignore`)
- Database passwords in connection string only
- JWT tokens for future auth (structure present)

### Trade Safety

- `reduceOnly` flag on SL/TP prevents over-trading
- Leverage limits enforced (1-125x)
- Position size limits prevent over-exposure

---

## Error Handling

### Backend

**Binance Errors**:
- API errors logged with full details
- Returns error codes to frontend
- Common errors:
  - Insufficient balance
  - Invalid symbol
  - Leverage not allowed
  - Margin type mismatch

**Database Errors**:
- Connection retries
- Transaction rollback on failures
- Logs detailed errors

**Telegram Errors**:
- Auto-reconnect on disconnect
- Session validation
- Message parsing failures logged

### Frontend

**User Feedback**:
- Alert dialogs for errors
- Loading states during operations
- Confirmation prompts for risky actions

**API Errors**:
- Try-catch on all API calls
- Console logging for debugging
- User-friendly error messages

---

## Performance Optimizations

### Backend

- Connection pooling for database
- Async operations for Telegram listener
- Caching of symbol info from Binance
- Efficient SQL queries with indexes

### Frontend

- SWR for data fetching (caching + revalidation)
- Optimistic UI updates
- Lazy loading of components
- Minimized re-renders

---

## Monitoring & Logging

### Backend Logs

**Via Loguru**:
- Colored console output
- Structured log format
- Levels: INFO, WARNING, ERROR

**Important Events Logged**:
- Signal received and parsed
- Trade execution (success/failure)
- Binance API calls
- Position opens/closes
- Telegram connection status

**Production**:
- Logs to `/var/log/crypto-backend.out.log`
- Errors to `/var/log/crypto-backend.err.log`
- Rotated by Supervisor

### Frontend Logs

- Console logs in development
- Error boundaries for crash handling
- Vercel deployment logs

---

## Deployment Architecture

### Development

```
Localhost:3000 (Next.js) ←→ Localhost:8000 (FastAPI) ←→ Neon Cloud DB
                                    ↓
                            Binance FAPI (Live)
                                    ↓
                            Telegram API
```

### Production

```
Vercel (Frontend) ←→ Digital Ocean Droplet (Backend) ←→ Neon Cloud DB
                              ↓
                      Nginx (Reverse Proxy)
                              ↓
                      Supervisor (Process Manager)
                              ↓
                      Uvicorn (FastAPI Server)
                              ↓
                      [Binance FAPI | Telegram API]
```

**Components**:
- **Vercel**: Static hosting for Next.js frontend
- **Digital Ocean**: Ubuntu 22.04 droplet running backend
- **Nginx**: Reverse proxy, handles SSL
- **Supervisor**: Keeps backend running, auto-restart
- **Uvicorn**: ASGI server for FastAPI

---

## File Structure

```
crypto_position_manager/
├── backend/
│   ├── app/
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── models/           # Database models
│   │   ├── config.py         # Settings
│   │   ├── database.py       # DB connection
│   │   └── main.py           # FastAPI app
│   ├── requirements.txt      # Python deps
│   └── .env.example         # Environment template
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── lib/             # Utilities
│   │   └── types/           # TypeScript types
│   ├── package.json         # Node deps
│   └── .env.example        # Environment template
│
├── README.md               # Main documentation
├── SETUP.md               # Setup instructions
├── QUICKSTART.md          # Quick reference
├── DEPLOYMENT_CHECKLIST.md # Pre-deploy checks
├── PROJECT_OVERVIEW.md    # This file
└── .gitignore            # Git ignore rules
```

---

## Development Workflow

### Adding a New Feature

1. **Backend**:
   - Add/modify service in `app/services/`
   - Create API endpoint in `app/routers/`
   - Update database model if needed
   - Test via `/docs` Swagger UI

2. **Frontend**:
   - Add API function in `src/lib/api.ts`
   - Create/update page in `src/app/`
   - Add types in `src/types/`
   - Test in browser

3. **Deploy**:
   - Backend: Push to server, restart Supervisor
   - Frontend: `vercel --prod`

### Testing a Signal

**Test Message Format**:
```
#BTCUSDT P | LONG 🟢
Entry: 42000 (CMP)
TP 1 → 43050
Stop Loss: 39900 ☠️
```

**What Happens**:
1. Parser extracts: `BTCUSDT`, `LONG`, `42000`
2. Calculates: SL = 39,900 (5% below), TP = 43,050 (2.5% above)
3. Creates LIMIT buy order at 42,000
4. Creates STOP_MARKET sell at 39,900
5. Creates TAKE_PROFIT_MARKET sell at 43,050
6. Waits for LIMIT order to fill
7. Shows position in UI

---

## Common Customizations

### Change SL/TP Percentages

**Via UI**: Trade Management page
**Via Code**: Update `DEFAULT_SL_PERCENTAGE` and `DEFAULT_TP_PERCENTAGE` in `.env`

### Change Position Size

**Via UI**: Trade Management page
**Via Code**: Update `DEFAULT_POSITION_SIZE` in `.env`

### Add New Signal Format

Edit `app/services/telegram_parser.py`:
- Update regex patterns
- Modify `parse_message()` method
- Test with new format

### Change Order Type (LIMIT → MARKET)

Edit `app/services/binance_service.py`:
- In `open_position()`, replace `place_limit_order()` with `place_market_order()`

---

## Troubleshooting Guide

### Signal Not Parsing

**Check**:
1. Does message contain pair symbol? (e.g., BTCUSDT)
2. Does it have direction? (LONG or SHORT)
3. Is entry price present?
4. Check backend logs for parser errors

### Order Not Executing

**Check**:
1. Binance account balance sufficient?
2. API has Futures trading enabled?
3. Symbol exists on Binance Futures?
4. Leverage within limits?
5. Check `binance_service.py` logs

### Position Not Showing

**Check**:
1. Order filled on Binance? (may be pending)
2. Database updated? (check `trades` table)
3. Frontend syncing? (click Refresh)
4. CORS errors in browser console?

### Telegram Listener Stopped

**Check**:
1. Session string valid?
2. Group ID correct?
3. Backend running? (`supervisorctl status`)
4. Check logs: `tail -f /var/log/crypto-backend.out.log`

---

## Future Enhancements

**Potential Features**:
- Multiple TP levels (TP1, TP2, TP3, TP4)
- Trailing stop loss
- Position size based on account percentage
- Multi-user support with authentication
- Trade history analytics
- Profit/loss charts
- Email/SMS notifications
- Backtesting engine
- Mobile app

**Architecture Improvements**:
- WebSocket for real-time updates
- Redis caching for performance
- Separate worker processes
- Rate limiting
- Better error recovery

---

## Technical Decisions

### Why FastAPI?
- Fast async support
- Auto-generated API docs
- Type hints for validation
- Easy WebSocket support (future)

### Why Next.js?
- Server-side rendering
- File-based routing
- TypeScript support
- Easy Vercel deployment

### Why Neon (not self-hosted DB)?
- Serverless (pay per use)
- Auto-scaling
- Built-in backups
- No maintenance

### Why LIMIT orders?
- Respect signal entry price
- Better price execution
- Can cancel if price moves away
- Market orders may have slippage

### Why 20x leverage default?
- Balance between risk and return
- Common in crypto futures
- User can adjust
- Lower than max (125x) for safety

---

## Key Takeaways

1. **Signal Flow**: Telegram → Parser → Database → Binance → UI
2. **Order Type**: LIMIT entry at signal price + STOP and TP orders
3. **SL/TP Logic**: Fixed percentages (5% SL, 2.5% TP)
4. **Position Size**: Fixed USD amount ($1000 default)
5. **Deployment**: Vercel (frontend) + Digital Ocean (backend)
6. **Risk**: LIVE trading with real money - use carefully!

---

**Built with ❤️ for automated crypto trading**
