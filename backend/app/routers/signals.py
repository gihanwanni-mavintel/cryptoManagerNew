"""Signals router for handling Telegram signal processing."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import (
    TelegramMessageInput, 
    SignalResponse, 
    SignalParseResponse,
    ApiResponse
)
from app.services.trade_service import TradeService

router = APIRouter(prefix="/api/signals", tags=["Signals"])


@router.post("/parse", response_model=SignalParseResponse)
async def parse_telegram_signal(
    message: TelegramMessageInput,
    auto_execute: bool = True,
    db: Session = Depends(get_db)
):
    """
    Parse a Telegram signal message, store it, and optionally execute the trade.
    
    - Extracts trading pair, direction, entry price
    - Calculates SL (5%) and TP (2.5%) from entry
    - Stores in database
    - Optionally executes trade on Binance
    """
    trade_service = TradeService(db)
    
    result = trade_service.process_telegram_message(
        message_input=message,
        user_id=1,  # Default user
        auto_execute=auto_execute
    )
    
    signal_response = None
    trade_response = None
    
    if result.get("signal"):
        signal = result["signal"]
        signal_response = SignalResponse(
            id=signal.id,
            pair=signal.pair,
            setup_type=signal.setup_type,
            entry=signal.entry,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            timestamp=signal.timestamp,
            full_message=signal.full_message,
            channel=signal.channel
        )
    
    if result.get("trade"):
        trade = result["trade"]
        trade_response = {
            "id": trade.id,
            "pair": trade.pair,
            "side": trade.side,
            "status": trade.status,
            "entry_price": trade.entry_price,
            "stop_loss": trade.stop_loss,
            "take_profit": trade.take_profit
        }
    
    return SignalParseResponse(
        success=result.get("success", False),
        signal=signal_response,
        trade=trade_response,
        message=result.get("message", "")
    )


@router.get("", response_model=List[SignalResponse])
async def get_signals(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all parsed signals with pagination."""
    trade_service = TradeService(db)
    signals = trade_service.get_signals(limit=limit, offset=offset)
    
    return [
        SignalResponse(
            id=signal.id,
            pair=signal.pair,
            setup_type=signal.setup_type,
            entry=signal.entry,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            timestamp=signal.timestamp,
            full_message=signal.full_message,
            channel=signal.channel
        )
        for signal in signals
    ]


@router.get("/active/count")
async def get_active_signals_count(db: Session = Depends(get_db)):
    """Get count of signals from today."""
    trade_service = TradeService(db)
    count = trade_service.get_active_signals_count()
    return {"active": count}


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: int, db: Session = Depends(get_db)):
    """Get a specific signal by ID."""
    from app.models.database_models import SignalMessage
    
    signal = db.query(SignalMessage).filter(SignalMessage.id == signal_id).first()
    
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    return SignalResponse(
        id=signal.id,
        pair=signal.pair,
        setup_type=signal.setup_type,
        entry=signal.entry,
        stop_loss=signal.stop_loss,
        take_profit=signal.take_profit,
        timestamp=signal.timestamp,
        full_message=signal.full_message,
        channel=signal.channel
    )


@router.post("/{signal_id}/execute")
async def execute_signal(signal_id: int, db: Session = Depends(get_db)):
    """Execute a trade from an existing signal."""
    trade_service = TradeService(db)
    
    result = trade_service.execute_trade_from_signal(signal_id, user_id=1)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to execute trade")
        )
    
    return {
        "success": True,
        "message": result.get("message"),
        "trade": result.get("trade")
    }
