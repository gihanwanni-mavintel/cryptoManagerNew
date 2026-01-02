"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SetupType(str, Enum):
    """Trade direction enum."""
    LONG = "LONG"
    SHORT = "SHORT"


class TradeStatus(str, Enum):
    """Trade status enum."""
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class MarginMode(str, Enum):
    """Margin mode enum."""
    CROSSED = "CROSSED"
    ISOLATED = "ISOLATED"


# User schemas
class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str
    password: str
    role: str = "USER"


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    role: str
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


# Signal schemas
class TelegramMessageInput(BaseModel):
    """Schema for raw Telegram message input."""
    text: str
    sender: Optional[str] = "TELEGRAM"
    channel: Optional[str] = "Unknown"


class ParsedSignal(BaseModel):
    """Schema for parsed signal data."""
    pair: str
    setup_type: SetupType
    entry: float
    stop_loss: float
    take_profit: float
    full_message: str
    channel: Optional[str] = None


class SignalCreate(BaseModel):
    """Schema for creating a signal."""
    pair: str
    setup_type: str
    entry: float
    stop_loss: float
    take_profit: float
    full_message: Optional[str] = None
    channel: Optional[str] = None


class SignalResponse(BaseModel):
    """Schema for signal response."""
    id: int
    pair: str
    setup_type: str
    entry: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    full_message: Optional[str] = None
    channel: Optional[str] = None
    
    class Config:
        from_attributes = True


# Trade schemas
class TradeCreate(BaseModel):
    """Schema for creating a trade."""
    signal_id: int
    pair: str
    side: str
    leverage: int = 20
    entry_price: float
    entry_quantity: float
    stop_loss: float
    take_profit: float


class TradeResponse(BaseModel):
    """Schema for trade response."""
    id: int
    user_id: Optional[int] = None
    signal_id: Optional[int] = None
    pair: str
    side: str
    leverage: int
    entry_price: Optional[float] = None
    entry_quantity: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str
    binance_order_id: Optional[str] = None
    binance_position_id: Optional[str] = None
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    exit_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    """Schema for active position response (from Binance)."""
    id: int
    pair: str
    side: str  # LONG or SHORT
    entry_price: float
    quantity: float
    leverage: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float
    unrealized_pnl_percent: float
    margin: float
    liquidation_price: Optional[float] = None
    opened_at: Optional[datetime] = None
    status: str
    
    class Config:
        from_attributes = True


class ClosePositionRequest(BaseModel):
    """Schema for closing a position."""
    trade_id: int
    close_type: str = "MARKET"  # MARKET or LIMIT
    limit_price: Optional[float] = None


# Trade config schemas
class TradeConfigUpdate(BaseModel):
    """Schema for updating trade configuration."""
    margin_mode: Optional[str] = None
    max_leverage: Optional[float] = None
    max_position_size: Optional[float] = None
    sl_percentage: Optional[float] = None
    tp_percentage: Optional[float] = None
    auto_execute_trades: Optional[bool] = None


class TradeConfigResponse(BaseModel):
    """Schema for trade configuration response."""
    id: int
    user_id: int
    margin_mode: str
    max_leverage: float
    max_position_size: float
    sl_percentage: float
    tp_percentage: float
    auto_execute_trades: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# API response schemas
class ApiResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool
    message: str
    data: Optional[dict] = None


class SignalParseResponse(BaseModel):
    """Response from signal parsing."""
    success: bool
    signal: Optional[SignalResponse] = None
    trade: Optional[TradeResponse] = None
    message: str


class TotalPnlResponse(BaseModel):
    """Total P&L response."""
    total_pnl: float
    total_pnl_percent: float
    open_positions: int
    total_trades: int
