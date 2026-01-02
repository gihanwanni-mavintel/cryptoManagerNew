"""Trade service for orchestrating signal processing and trade execution."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from app.models.database_models import (
    MarketMessage, SignalMessage, Trade, TradeManagementConfig
)
from app.models.schemas import (
    TelegramMessageInput, ParsedSignal, TradeResponse, PositionResponse
)
from app.services.telegram_parser import TelegramParser
from app.services.binance_service import BinanceService
from app.config import settings


class TradeService:
    """
    Service for managing the complete trading workflow:
    1. Parse Telegram signals
    2. Store signals in database
    3. Execute trades on Binance
    4. Track positions and P&L
    """
    
    def __init__(self, db: Session):
        """Initialize trade service with database session."""
        self.db = db
        self.binance = BinanceService()
        self.parser = TelegramParser()
    
    def get_config(self, user_id: int = 1) -> TradeManagementConfig:
        """Get trade configuration for user."""
        config = self.db.query(TradeManagementConfig).filter(
            TradeManagementConfig.user_id == user_id
        ).first()
        
        if not config:
            # Create default config
            config = TradeManagementConfig(
                user_id=user_id,
                margin_mode=settings.default_margin_mode,
                max_leverage=settings.default_leverage,
                max_position_size=settings.default_position_size,
                sl_percentage=settings.default_sl_percentage,
                tp_percentage=settings.default_tp_percentage
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        
        return config
    
    def update_config(
        self, 
        user_id: int, 
        margin_mode: str = None,
        max_leverage: float = None,
        max_position_size: float = None,
        sl_percentage: float = None,
        tp_percentage: float = None,
        auto_execute_trades: bool = None
    ) -> TradeManagementConfig:
        """Update trade configuration."""
        config = self.get_config(user_id)
        
        if margin_mode is not None:
            config.margin_mode = margin_mode
        if max_leverage is not None:
            config.max_leverage = max_leverage
        if max_position_size is not None:
            config.max_position_size = max_position_size
        if sl_percentage is not None:
            config.sl_percentage = sl_percentage
            self.parser.sl_percentage = sl_percentage
        if tp_percentage is not None:
            config.tp_percentage = tp_percentage
            self.parser.tp_percentage = tp_percentage
        if auto_execute_trades is not None:
            config.auto_execute_trades = auto_execute_trades
        
        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)
        
        return config
    
    def reset_config(self, user_id: int) -> TradeManagementConfig:
        """Reset configuration to defaults."""
        config = self.get_config(user_id)
        
        config.margin_mode = settings.default_margin_mode
        config.max_leverage = settings.default_leverage
        config.max_position_size = settings.default_position_size
        config.sl_percentage = settings.default_sl_percentage
        config.tp_percentage = settings.default_tp_percentage
        config.auto_execute_trades = True
        config.updated_at = datetime.utcnow()
        
        self.parser.sl_percentage = settings.default_sl_percentage
        self.parser.tp_percentage = settings.default_tp_percentage
        
        self.db.commit()
        self.db.refresh(config)
        
        return config
    
    def process_telegram_message(
        self, 
        message_input: TelegramMessageInput,
        user_id: int = 1,
        auto_execute: bool = True
    ) -> Dict[str, Any]:
        """
        Process a Telegram message: parse, store, and optionally execute trade.
        
        Args:
            message_input: Raw Telegram message input
            user_id: User ID for the trade
            auto_execute: Whether to automatically execute the trade
            
        Returns:
            Dict with signal, trade, and execution results
        """
        result = {
            "success": False,
            "signal": None,
            "trade": None,
            "message": ""
        }
        
        try:
            # Get user config
            config = self.get_config(user_id)
            
            # Update parser with current SL/TP percentages
            self.parser.sl_percentage = float(config.sl_percentage)
            self.parser.tp_percentage = float(config.tp_percentage)
            
            # Step 1: Store raw message
            market_message = MarketMessage(
                sender=message_input.sender,
                text=message_input.text,
                timestamp=datetime.utcnow()
            )
            self.db.add(market_message)
            self.db.commit()
            
            # Step 2: Parse the message
            parsed = self.parser.parse_message(message_input.text)
            if not parsed:
                result["message"] = "Failed to parse signal from message"
                return result
            
            # Step 3: Store parsed signal
            signal = SignalMessage(
                pair=parsed.pair,
                setup_type=parsed.setup_type,
                entry=parsed.entry,
                stop_loss=parsed.stop_loss,
                take_profit=parsed.take_profit,
                full_message=message_input.text,
                channel=message_input.channel,
                timestamp=datetime.utcnow()
            )
            self.db.add(signal)
            self.db.commit()
            self.db.refresh(signal)
            
            result["signal"] = signal
            
            # Step 4: Execute trade if auto_execute is enabled
            if auto_execute and config.auto_execute_trades:
                trade_result = self.execute_trade_from_signal(signal.id, user_id)
                result["trade"] = trade_result.get("trade")
                result["execution_result"] = trade_result
                result["success"] = trade_result.get("success", False)
                result["message"] = trade_result.get("message", "Trade executed")
            else:
                result["success"] = True
                result["message"] = "Signal parsed and stored successfully"
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing Telegram message: {e}")
            result["message"] = str(e)
            return result
    
    def execute_trade_from_signal(
        self, 
        signal_id: int, 
        user_id: int = 1
    ) -> Dict[str, Any]:
        """
        Execute a trade based on a stored signal.
        
        Args:
            signal_id: ID of the signal to trade
            user_id: User ID for the trade
            
        Returns:
            Dict with trade and execution results
        """
        result = {
            "success": False,
            "trade": None,
            "message": ""
        }
        
        try:
            # Get signal
            signal = self.db.query(SignalMessage).filter(
                SignalMessage.id == signal_id
            ).first()
            
            if not signal:
                result["message"] = "Signal not found"
                return result
            
            # Get config
            config = self.get_config(user_id)

            # Execute on Binance FIRST (before creating database record)
            binance_result = self.binance.open_position(
                symbol=signal.pair,
                side=signal.setup_type,
                position_size_usd=float(config.max_position_size),
                leverage=int(config.max_leverage),
                margin_type=config.margin_mode,
                entry_price=signal.entry,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit
            )

            # Only create trade record if Binance order was successful
            if binance_result["success"]:
                entry_order = binance_result.get("entry_order")

                # Determine initial status based on order status
                order_status = entry_order.status if entry_order else "PENDING"
                if order_status == "FILLED":
                    initial_status = "OPEN"
                    opened_at = datetime.utcnow()
                elif order_status in ["NEW", "PARTIALLY_FILLED"]:
                    initial_status = "PENDING"
                    opened_at = None
                else:
                    initial_status = "OPEN"
                    opened_at = datetime.utcnow()

                # Create trade record with Binance order details
                trade = Trade(
                    user_id=user_id,
                    signal_id=signal.id,
                    pair=signal.pair,
                    side=signal.setup_type,
                    leverage=int(config.max_leverage),
                    entry_price=entry_order.price if entry_order else signal.entry,
                    entry_quantity=entry_order.quantity if entry_order else None,
                    binance_order_id=entry_order.order_id if entry_order else None,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    tp=signal.take_profit,
                    status=initial_status,
                    opened_at=opened_at,
                    created_at=datetime.utcnow()
                )
                self.db.add(trade)
                self.db.commit()
                self.db.refresh(trade)

                result["success"] = True
                result["trade"] = trade
                result["message"] = f"Limit order placed successfully (Status: {trade.status})"
                result["binance_result"] = {
                    "entry_order_id": entry_order.order_id if entry_order else None,
                    "order_status": order_status,
                    "sl_order": binance_result.get("sl_order"),
                    "tp_order": binance_result.get("tp_order")
                }
            else:
                # Binance order failed - do NOT create trade record
                result["success"] = False
                result["trade"] = None
                result["message"] = binance_result.get("message", "Trade execution failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            result["message"] = str(e)
            return result
    
    def close_trade(self, trade_id: int) -> Dict[str, Any]:
        """
        Close an open trade.
        
        Args:
            trade_id: ID of the trade to close
            
        Returns:
            Dict with close result
        """
        result = {
            "success": False,
            "trade": None,
            "message": ""
        }
        
        try:
            # Get trade
            trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
            
            if not trade:
                result["message"] = "Trade not found"
                return result
            
            if trade.status != "OPEN":
                result["message"] = f"Trade is not open (status: {trade.status})"
                return result
            
            # Close on Binance
            close_result = self.binance.close_position(trade.pair, trade.side)
            
            if close_result.success:
                # Update trade record
                trade.status = "CLOSED"
                trade.closed_at = datetime.utcnow()
                trade.exit_price = close_result.price
                trade.exit_reason = "MANUAL"
                
                # Calculate P&L
                if trade.entry_price and close_result.price:
                    if trade.side == "LONG":
                        pnl_percent = ((close_result.price - trade.entry_price) / trade.entry_price) * 100
                    else:  # SHORT
                        pnl_percent = ((trade.entry_price - close_result.price) / trade.entry_price) * 100
                    
                    trade.pnl_percent = pnl_percent
                    if trade.entry_quantity:
                        trade.pnl = (pnl_percent / 100) * trade.entry_quantity * trade.entry_price
                
                self.db.commit()
                self.db.refresh(trade)
                
                result["success"] = True
                result["trade"] = trade
                result["message"] = "Trade closed successfully"
            else:
                result["message"] = close_result.message
            
            return result
            
        except Exception as e:
            logger.error(f"Error closing trade: {e}")
            result["message"] = str(e)
            return result
    
    def get_active_positions(self, user_id: int = 1) -> List[PositionResponse]:
        """
        Get all active positions from Binance, matched with database records.
        
        Args:
            user_id: User ID to filter positions
            
        Returns:
            List of active positions with full details
        """
        positions = []
        
        try:
            # Get positions from Binance
            binance_positions = self.binance.get_positions()
            
            # Get open trades from database
            db_trades = self.db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.status == "OPEN"
            ).all()
            
            # Create position responses
            for pos in binance_positions:
                # Find matching trade in database
                matching_trade = None
                for trade in db_trades:
                    if trade.pair == pos.symbol:
                        matching_trade = trade
                        break
                
                # Calculate P&L percentage
                if pos.entry_price > 0 and pos.mark_price:
                    if pos.side == "LONG":
                        pnl_percent = ((pos.mark_price - pos.entry_price) / pos.entry_price) * 100 * pos.leverage
                    else:
                        pnl_percent = ((pos.entry_price - pos.mark_price) / pos.entry_price) * 100 * pos.leverage
                else:
                    pnl_percent = 0
                
                position = PositionResponse(
                    id=matching_trade.id if matching_trade else 0,
                    pair=pos.symbol,
                    side=pos.side,
                    entry_price=pos.entry_price,
                    quantity=pos.quantity,
                    leverage=pos.leverage,
                    stop_loss=matching_trade.stop_loss if matching_trade else None,
                    take_profit=matching_trade.take_profit if matching_trade else None,
                    unrealized_pnl=pos.unrealized_pnl,
                    unrealized_pnl_percent=pnl_percent,
                    margin=pos.margin,
                    liquidation_price=pos.liquidation_price,
                    opened_at=matching_trade.opened_at if matching_trade else None,
                    status="OPEN"
                )
                positions.append(position)
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting active positions: {e}")
            return []
    
    def get_total_pnl(self, user_id: int = 1) -> Dict[str, Any]:
        """
        Calculate total P&L from all positions.
        
        Args:
            user_id: User ID to calculate P&L for
            
        Returns:
            Dict with total P&L info
        """
        try:
            positions = self.get_active_positions(user_id)
            
            total_pnl = sum(pos.unrealized_pnl for pos in positions)
            total_margin = sum(pos.margin for pos in positions)
            
            # Calculate overall P&L percentage
            if total_margin > 0:
                total_pnl_percent = (total_pnl / total_margin) * 100
            else:
                total_pnl_percent = 0
            
            # Get historical trades
            closed_trades = self.db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.status == "CLOSED"
            ).count()
            
            return {
                "total_pnl": total_pnl,
                "total_pnl_percent": total_pnl_percent,
                "open_positions": len(positions),
                "total_trades": closed_trades + len(positions)
            }
            
        except Exception as e:
            logger.error(f"Error calculating total P&L: {e}")
            return {
                "total_pnl": 0,
                "total_pnl_percent": 0,
                "open_positions": 0,
                "total_trades": 0
            }
    
    def get_signals(
        self, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[SignalMessage]:
        """Get recent signals."""
        return self.db.query(SignalMessage).order_by(
            SignalMessage.timestamp.desc()
        ).offset(offset).limit(limit).all()
    
    def get_active_signals_count(self) -> int:
        """Get count of signals from today."""
        from datetime import date
        today = date.today()
        return self.db.query(SignalMessage).filter(
            SignalMessage.timestamp >= today
        ).count()
    
    def sync_positions_with_binance(self, user_id: int = 1):
        """
        Sync database trades with actual Binance positions.
        Updates status for trades that have been closed externally.
        """
        try:
            # Get all open trades from database
            db_trades = self.db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.status == "OPEN"
            ).all()
            
            # Get actual positions from Binance
            binance_positions = self.binance.get_positions()
            binance_symbols = {pos.symbol for pos in binance_positions}
            
            # Update trades that are no longer open on Binance
            for trade in db_trades:
                if trade.pair not in binance_symbols:
                    # Position was closed (by SL, TP, or liquidation)
                    trade.status = "CLOSED"
                    trade.closed_at = datetime.utcnow()
                    
                    # Try to determine exit reason
                    current_price = self.binance.get_current_price(trade.pair)
                    if current_price:
                        if trade.side == "LONG":
                            if trade.stop_loss and current_price <= trade.stop_loss:
                                trade.exit_reason = "SL_HIT"
                            elif trade.take_profit and current_price >= trade.take_profit:
                                trade.exit_reason = "TP_HIT"
                            else:
                                trade.exit_reason = "UNKNOWN"
                        else:  # SHORT
                            if trade.stop_loss and current_price >= trade.stop_loss:
                                trade.exit_reason = "SL_HIT"
                            elif trade.take_profit and current_price <= trade.take_profit:
                                trade.exit_reason = "TP_HIT"
                            else:
                                trade.exit_reason = "UNKNOWN"
                        
                        trade.exit_price = current_price
            
            self.db.commit()
            logger.info("Positions synced with Binance")
            
        except Exception as e:
            logger.error(f"Error syncing positions: {e}")
