"""SQLAlchemy database models."""
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean, 
    DateTime, Numeric, Text, ForeignKey, CheckConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False, default="USER")
    
    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'USER')", name="users_role_check"),
    )
    
    # Relationships
    trades = relationship("Trade", back_populates="user")
    config = relationship("TradeManagementConfig", back_populates="user", uselist=False)


class MarketMessage(Base):
    """Raw Telegram messages storage."""
    __tablename__ = "market_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(Text)
    text = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class SignalMessage(Base):
    """Parsed trading signals."""
    __tablename__ = "signal_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pair = Column(String(255))
    setup_type = Column(String(255))  # LONG or SHORT
    entry = Column(Numeric(20, 8))  # Changed from Float for precision
    stop_loss = Column(Numeric(20, 8))  # Changed from Float for precision
    take_profit = Column(Numeric(20, 8))  # Changed from Float for precision
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    full_message = Column(Text)
    channel = Column(String(255))

    # Relationships
    trades = relationship("Trade", back_populates="signal")


class Trade(Base):
    """Trade records."""
    __tablename__ = "trades"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    signal_id = Column(BigInteger, ForeignKey("signal_messages.id"))
    pair = Column(String(255), nullable=False)
    side = Column(String(255), nullable=False)  # BUY or SELL
    leverage = Column(Integer, default=20)
    entry_price = Column(Numeric(20, 8))  # Changed from Float for precision
    entry_quantity = Column(Numeric(20, 8))  # Changed from Float for precision
    stop_loss = Column(Numeric(20, 8))  # Changed from Float for precision
    take_profit = Column(Numeric(20, 8))  # Changed from Float for precision
    tp = Column(Numeric(20, 8))  # Alias for take_profit - Changed from Float
    status = Column(String(255), default="PENDING")  # PENDING, OPEN, CLOSED, CANCELLED
    binance_order_id = Column(String(255))
    binance_position_id = Column(String(255))
    opened_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    exit_price = Column(Numeric(20, 8))  # Changed from Float for precision
    pnl = Column(Numeric(20, 8))  # Changed from Float for precision
    pnl_percent = Column(Numeric(10, 4))  # Changed from Float - percentage needs less precision
    exit_reason = Column(String(255))  # TP_HIT, SL_HIT, MANUAL, LIQUIDATION
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="trades")
    signal = relationship("SignalMessage", back_populates="trades")


class TradeManagementConfig(Base):
    """Trade management configuration per user."""
    __tablename__ = "trade_management_config"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=False)
    margin_mode = Column(String(255), nullable=False, default="CROSSED")  # CROSSED or ISOLATED
    max_leverage = Column(Numeric(5, 2), nullable=False, default=20.00)
    max_position_size = Column(Numeric(15, 2), nullable=False, default=1000.00)
    sl_percentage = Column(Numeric(5, 2), nullable=False, default=5.00)
    tp_percentage = Column(Numeric(5, 2), nullable=False, default=2.50)
    auto_execute_trades = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="config")
