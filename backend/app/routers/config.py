"""Configuration router for trade management settings."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import TradeConfigResponse, TradeConfigUpdate
from app.services.trade_service import TradeService

router = APIRouter(prefix="/api/config", tags=["Configuration"])


@router.get("", response_model=TradeConfigResponse)
async def get_config(db: Session = Depends(get_db)):
    """
    Get current trade management configuration.
    
    Returns settings for:
    - Margin mode (CROSSED/ISOLATED)
    - Maximum leverage
    - Maximum position size
    - Stop loss percentage
    - Take profit percentage
    - Auto-execute toggle
    """
    trade_service = TradeService(db)
    config = trade_service.get_config(user_id=1)
    
    return TradeConfigResponse(
        id=config.id,
        user_id=config.user_id,
        margin_mode=config.margin_mode,
        max_leverage=float(config.max_leverage),
        max_position_size=float(config.max_position_size),
        sl_percentage=float(config.sl_percentage),
        tp_percentage=float(config.tp_percentage),
        auto_execute_trades=config.auto_execute_trades,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.put("", response_model=TradeConfigResponse)
async def update_config(
    config_update: TradeConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Update trade management configuration.
    
    All fields are optional - only provided fields will be updated.
    Changes affect all future trades.
    """
    trade_service = TradeService(db)
    
    config = trade_service.update_config(
        user_id=1,
        margin_mode=config_update.margin_mode,
        max_leverage=config_update.max_leverage,
        max_position_size=config_update.max_position_size,
        sl_percentage=config_update.sl_percentage,
        tp_percentage=config_update.tp_percentage,
        auto_execute_trades=config_update.auto_execute_trades
    )
    
    return TradeConfigResponse(
        id=config.id,
        user_id=config.user_id,
        margin_mode=config.margin_mode,
        max_leverage=float(config.max_leverage),
        max_position_size=float(config.max_position_size),
        sl_percentage=float(config.sl_percentage),
        tp_percentage=float(config.tp_percentage),
        auto_execute_trades=config.auto_execute_trades,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.post("/reset", response_model=TradeConfigResponse)
async def reset_config(db: Session = Depends(get_db)):
    """
    Reset configuration to default values.
    
    Defaults:
    - Margin mode: CROSSED
    - Max leverage: 20x
    - Max position size: $1000
    - SL percentage: 5%
    - TP percentage: 2.5%
    - Auto-execute: enabled
    """
    trade_service = TradeService(db)
    config = trade_service.reset_config(user_id=1)
    
    return TradeConfigResponse(
        id=config.id,
        user_id=config.user_id,
        margin_mode=config.margin_mode,
        max_leverage=float(config.max_leverage),
        max_position_size=float(config.max_position_size),
        sl_percentage=float(config.sl_percentage),
        tp_percentage=float(config.tp_percentage),
        auto_execute_trades=config.auto_execute_trades,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.get("/defaults")
async def get_defaults():
    """Get default configuration values."""
    from app.config import settings
    
    return {
        "margin_mode": settings.default_margin_mode,
        "max_leverage": settings.default_leverage,
        "max_position_size": settings.default_position_size,
        "sl_percentage": settings.default_sl_percentage,
        "tp_percentage": settings.default_tp_percentage,
        "auto_execute_trades": True
    }
