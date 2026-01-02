"""Main FastAPI application."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.routers import signals_router, trades_router, config_router, auth_router
from app.database import engine, Base, SessionLocal
from app.config import settings

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Global reference to telegram processor
telegram_processor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global telegram_processor
    
    logger.info("Starting Crypto Position Manager API")
    logger.info(f"Binance Testnet Mode: {settings.binance_testnet}")
    logger.info(f"Auto Execute Trades: {settings.auto_execute_trades}")
    logger.info(f"Default Position Size: ${settings.default_position_size}")
    
    # Start Telegram listener if configured
    if settings.telegram_session_string and settings.telegram_group_id:
        logger.info("Starting Telegram listener...")
        try:
            from app.services.telegram_listener import TelegramSignalProcessor
            telegram_processor = TelegramSignalProcessor(db_session_factory=SessionLocal)
            # Run in background task
            asyncio.create_task(telegram_processor.start())
            logger.info("Telegram listener task created")
        except Exception as e:
            logger.error(f"Failed to start Telegram listener: {e}")
    else:
        logger.warning("Telegram listener not configured (missing session string or group ID)")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Crypto Position Manager API")
    if telegram_processor:
        await telegram_processor.stop()


# Create FastAPI app with lifespan
app = FastAPI(
    title="Crypto Position Manager API",
    description="""
    A comprehensive crypto trading API for:
    - Parsing Telegram trading signals (manual and automatic)
    - Executing trades on Binance Futures
    - Managing positions and P&L
    - Configuring trade parameters
    
    Telegram listener automatically monitors configured groups for signals.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "https://localhost:3000",
        "https://crypto-manager-new.vercel.app",
        "http://crypto-manager-new.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(signals_router)
app.include_router(trades_router)
app.include_router(config_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Crypto Position Manager API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "telegram_listener": telegram_processor.listener.is_running() if telegram_processor else False
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "binance_testnet": settings.binance_testnet,
        "telegram_listener": telegram_processor.listener.is_running() if telegram_processor else False,
        "auto_execute": settings.auto_execute_trades,
        "position_size": settings.default_position_size
    }


@app.get("/api/telegram/status")
async def telegram_status():
    """Get Telegram listener status."""
    if telegram_processor:
        return {
            "enabled": True,
            "running": telegram_processor.listener.is_running(),
            "group_id": settings.telegram_group_id
        }
    return {
        "enabled": False,
        "running": False,
        "group_id": None
    }


# App init file
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
