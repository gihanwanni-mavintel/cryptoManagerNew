"""Telegram message parser service."""
import re
from typing import Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class ParsedSignalData:
    """Data class for parsed signal information."""
    pair: str
    setup_type: str  # LONG or SHORT
    entry: float
    stop_loss: float
    take_profit: float
    original_sl: Optional[float] = None
    original_tp: Optional[float] = None


class TelegramParser:
    """
    Parser for Telegram trading signal messages.
    
    Supports formats like:
    #METUSDT P | LONG 🟢
    Entry: 0.2515 (CMP)
    TP 1 → 0.2573
    Stop Loss: 0.25 ☠️
    """
    
    # Regex patterns for parsing
    PAIR_PATTERN = r'#?([A-Z0-9]+(?:USDT|BUSD|BTC|ETH)\.?P?)'
    DIRECTION_PATTERN = r'(LONG|SHORT)\s*[🟢🔴]?'
    ENTRY_PATTERN = r'Entry[:\s]*\$?(\d+\.?\d*)'
    STOP_LOSS_PATTERN = r'(?:Stop\s*Loss|SL)[:\s]*\$?(\d+\.?\d*)'
    TAKE_PROFIT_PATTERN = r'(?:Take\s*Profit|TP|TP\s*\d)[:\s→]*\$?(\d+\.?\d*)'
    
    def __init__(self, sl_percentage: float = 5.0, tp_percentage: float = 2.5):
        """
        Initialize parser with default SL/TP percentages.
        
        Args:
            sl_percentage: Default stop loss percentage (default 5%)
            tp_percentage: Default take profit percentage (default 2.5%)
        """
        self.sl_percentage = sl_percentage
        self.tp_percentage = tp_percentage
    
    def parse_message(self, message: str) -> Optional[ParsedSignalData]:
        """
        Parse a Telegram trading signal message.
        
        Args:
            message: Raw Telegram message text
            
        Returns:
            ParsedSignalData if parsing successful, None otherwise
        """
        try:
            logger.info(f"Parsing message: {message[:100]}...")
            
            # Extract trading pair
            pair = self._extract_pair(message)
            if not pair:
                logger.warning("Could not extract trading pair from message")
                return None
            
            # Extract direction (LONG/SHORT)
            direction = self._extract_direction(message)
            if not direction:
                logger.warning("Could not extract direction from message")
                return None
            
            # Extract entry price
            entry = self._extract_entry(message)
            if not entry:
                logger.warning("Could not extract entry price from message")
                return None
            
            # Extract original SL and TP from message (if present)
            original_sl = self._extract_stop_loss(message)
            original_tp = self._extract_take_profit(message)
            
            # Calculate SL and TP based on entry and direction
            stop_loss, take_profit = self._calculate_sl_tp(entry, direction)
            
            logger.info(f"Parsed signal: {pair} {direction} @ {entry}, SL: {stop_loss}, TP: {take_profit}")
            
            return ParsedSignalData(
                pair=pair,
                setup_type=direction,
                entry=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                original_sl=original_sl,
                original_tp=original_tp
            )
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None
    
    def _extract_pair(self, message: str) -> Optional[str]:
        """Extract trading pair from message."""
        # Try to find hashtag format first
        match = re.search(self.PAIR_PATTERN, message.upper())
        if match:
            pair = match.group(1)
            # Clean up the pair - remove .P suffix if present (for perpetual futures)
            if pair.endswith('.P'):
                pair = pair[:-2]  # Remove last 2 characters (.P)
            elif pair.endswith('P') and not pair.endswith('USDT'):
                # Only remove trailing P if it's not part of the symbol name
                # e.g., "METUSDT.P" -> "METUSDT" but "PERPUSDT" stays "PERPUSDT"
                pair = pair[:-1]
            return pair
        return None
    
    def _extract_direction(self, message: str) -> Optional[str]:
        """Extract trade direction (LONG/SHORT) from message."""
        match = re.search(self.DIRECTION_PATTERN, message.upper())
        if match:
            return match.group(1)
        
        # Alternative detection based on emojis
        if '🟢' in message and 'LONG' not in message.upper():
            return 'LONG'
        if '🔴' in message and 'SHORT' not in message.upper():
            return 'SHORT'
        
        return None
    
    def _extract_entry(self, message: str) -> Optional[float]:
        """Extract entry price from message."""
        match = re.search(self.ENTRY_PATTERN, message, re.IGNORECASE)
        if match:
            return float(match.group(1))

        # Alternative pattern: look for CMP (Current Market Price)
        cmp_pattern = r'(\d+\.?\d*)\s*\(?CMP\)?'
        match = re.search(cmp_pattern, message, re.IGNORECASE)
        if match:
            return float(match.group(1))

        return None
    
    def _extract_stop_loss(self, message: str) -> Optional[float]:
        """Extract stop loss from message (if specified)."""
        match = re.search(self.STOP_LOSS_PATTERN, message, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None
    
    def _extract_take_profit(self, message: str) -> Optional[float]:
        """Extract take profit from message (if specified)."""
        # Find all TP values and return the first one
        matches = re.findall(self.TAKE_PROFIT_PATTERN, message, re.IGNORECASE)
        if matches:
            return float(matches[0])
        return None
    
    def _calculate_sl_tp(self, entry: float, direction: str) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit based on entry price and direction.
        
        For LONG:
            - SL = Entry × (1 - sl_percentage/100)
            - TP = Entry × (1 + tp_percentage/100)
        
        For SHORT:
            - SL = Entry × (1 + sl_percentage/100)
            - TP = Entry × (1 - tp_percentage/100)
        
        Args:
            entry: Entry price
            direction: LONG or SHORT
            
        Returns:
            Tuple of (stop_loss, take_profit)
        """
        sl_multiplier = self.sl_percentage / 100
        tp_multiplier = self.tp_percentage / 100
        
        if direction == "LONG":
            stop_loss = round(entry * (1 - sl_multiplier), 8)
            take_profit = round(entry * (1 + tp_multiplier), 8)
        else:  # SHORT
            stop_loss = round(entry * (1 + sl_multiplier), 8)
            take_profit = round(entry * (1 - tp_multiplier), 8)
        
        return stop_loss, take_profit
    
    def update_percentages(self, sl_percentage: float = None, tp_percentage: float = None):
        """Update SL/TP percentage settings."""
        if sl_percentage is not None:
            self.sl_percentage = sl_percentage
        if tp_percentage is not None:
            self.tp_percentage = tp_percentage


# Test function
def test_parser():
    """Test the parser with sample messages."""
    parser = TelegramParser()
    
    test_messages = [
        """#METUSDT P | LONG 🟢
Entry: 0.2515 (CMP) 
TP 1 → 0.2573
TP 2 → 0.2580
Stop Loss: 0.25 ☠️""",
        
        """#METUSDT P | SHORT 🔴
Entry: 0.2515 (CMP) 
TP 1 → 0.2400
Stop Loss: 0.26 ☠️""",
        
        """#BTCUSDT LONG 🟢
Entry: 42000
TP: 43000
SL: 41000"""
    ]
    
    for msg in test_messages:
        result = parser.parse_message(msg)
        print(f"\nMessage: {msg[:50]}...")
        print(f"Result: {result}")


if __name__ == "__main__":
    test_parser()
