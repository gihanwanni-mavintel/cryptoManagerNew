"""Trades router for position and trade management."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import (
    TradeResponse,
    PositionResponse,
    ClosePositionRequest,
    TotalPnlResponse,
    ApiResponse
)
from app.models.database_models import Trade
from app.services.trade_service import TradeService

router = APIRouter(prefix="/api/trades", tags=["Trades"])


@router.get("/positions", response_model=List[PositionResponse])
async def get_active_positions(db: Session = Depends(get_db)):
    """
    Get all active positions from Binance.
    
    Returns positions with:
    - Current entry price
    - Unrealized P&L
    - Stop loss and take profit levels
    - Margin and leverage info
    """
    trade_service = TradeService(db)
    
    # Sync with Binance first
    trade_service.sync_positions_with_binance(user_id=1)
    
    positions = trade_service.get_active_positions(user_id=1)
    return positions


@router.post("/close/{trade_id}")
async def close_position(trade_id: int, db: Session = Depends(get_db)):
    """
    Close an active position.
    
    This will:
    - Cancel all open orders for the symbol
    - Place a market order to close the position
    - Update the trade record with exit details
    """
    trade_service = TradeService(db)
    
    result = trade_service.close_trade(trade_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to close position")
        )
    
    trade = result.get("trade")
    return {
        "success": True,
        "message": "Position closed successfully",
        "trade": {
            "id": trade.id,
            "pair": trade.pair,
            "exit_price": trade.exit_price,
            "pnl": trade.pnl,
            "pnl_percent": trade.pnl_percent
        } if trade else None
    }


@router.get("/pnl", response_model=TotalPnlResponse)
async def get_total_pnl(db: Session = Depends(get_db)):
    """
    Get total P&L across all positions.
    
    Returns:
    - Total unrealized P&L in USD
    - Total P&L percentage
    - Number of open positions
    - Total number of trades
    """
    trade_service = TradeService(db)
    return trade_service.get_total_pnl(user_id=1)


@router.get("/history", response_model=List[TradeResponse])
async def get_trade_history(
    limit: int = 50,
    offset: int = 0,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Get trade history with optional filtering.
    
    Args:
        limit: Number of trades to return
        offset: Pagination offset
        status: Filter by status (OPEN, CLOSED, CANCELLED)
    """
    query = db.query(Trade).filter(Trade.user_id == 1)
    
    if status:
        query = query.filter(Trade.status == status)
    
    trades = query.order_by(Trade.created_at.desc()).offset(offset).limit(limit).all()
    
    return [
        TradeResponse(
            id=trade.id,
            user_id=trade.user_id,
            signal_id=trade.signal_id,
            pair=trade.pair,
            side=trade.side,
            leverage=trade.leverage,
            entry_price=trade.entry_price,
            entry_quantity=trade.entry_quantity,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            status=trade.status,
            binance_order_id=trade.binance_order_id,
            binance_position_id=trade.binance_position_id,
            opened_at=trade.opened_at,
            closed_at=trade.closed_at,
            exit_price=trade.exit_price,
            pnl=trade.pnl,
            pnl_percent=trade.pnl_percent,
            exit_reason=trade.exit_reason,
            created_at=trade.created_at
        )
        for trade in trades
    ]


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """Get a specific trade by ID."""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return TradeResponse(
        id=trade.id,
        user_id=trade.user_id,
        signal_id=trade.signal_id,
        pair=trade.pair,
        side=trade.side,
        leverage=trade.leverage,
        entry_price=trade.entry_price,
        entry_quantity=trade.entry_quantity,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
        status=trade.status,
        binance_order_id=trade.binance_order_id,
        binance_position_id=trade.binance_position_id,
        opened_at=trade.opened_at,
        closed_at=trade.closed_at,
        exit_price=trade.exit_price,
        pnl=trade.pnl,
        pnl_percent=trade.pnl_percent,
        exit_reason=trade.exit_reason,
        created_at=trade.created_at
    )


@router.post("/sync")
async def sync_positions(db: Session = Depends(get_db)):
    """
    Manually sync positions with Binance.
    
    Updates trade statuses based on actual Binance positions.
    """
    trade_service = TradeService(db)
    trade_service.sync_positions_with_binance(user_id=1)
    
    return {"success": True, "message": "Positions synced with Binance"}
