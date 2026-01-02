"""Routers package."""
from app.routers.signals import router as signals_router
from app.routers.trades import router as trades_router
from app.routers.config import router as config_router
from app.routers.auth import router as auth_router

__all__ = ["signals_router", "trades_router", "config_router", "auth_router"]
