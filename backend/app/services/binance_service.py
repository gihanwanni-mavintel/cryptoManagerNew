"""Binance Futures API service."""
import hashlib
import hmac
import time
import requests
from decimal import Decimal
from urllib.parse import urlencode
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from loguru import logger
from app.config import settings


@dataclass
class OrderResult:
    """Result of an order operation."""
    success: bool
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    status: Optional[str] = None
    message: Optional[str] = None
    raw_response: Optional[Dict] = None


@dataclass
class PositionInfo:
    """Position information from Binance."""
    symbol: str
    side: str  # LONG or SHORT
    entry_price: float
    quantity: float
    unrealized_pnl: float
    leverage: int
    margin: float
    margin_type: str  # CROSSED or ISOLATED
    liquidation_price: Optional[float] = None
    mark_price: Optional[float] = None
    notional_value: Optional[float] = None


class BinanceService:
    """
    Service for interacting with Binance Futures API.
    
    Uses the FAPI (Futures API) endpoints for:
    - Placing market/limit orders
    - Setting stop loss and take profit
    - Managing leverage and margin mode
    - Fetching positions and account info
    """
    
    # API endpoints
    TESTNET_BASE_URL = "https://testnet.binancefuture.com"
    MAINNET_BASE_URL = "https://fapi.binance.com"
    
    def __init__(self):
        """Initialize Binance service with API credentials."""
        self.api_key = settings.binance_api_key
        self.api_secret = settings.binance_api_secret
        self.testnet = settings.binance_testnet
        self.base_url = self.TESTNET_BASE_URL if self.testnet else self.MAINNET_BASE_URL
        
        logger.info(f"Binance service initialized (testnet: {self.testnet})")
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature for request."""
        logger.debug(f"Query string for signature: {query_string}")
        logger.debug(f"API Secret length: {len(self.api_secret)}")
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        logger.debug(f"Generated signature: {signature}")
        return signature
    
    def _get_headers(self) -> Dict:
        """Get request headers with API key."""
        return {
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        signed: bool = True
    ) -> Dict:
        """
        Make request to Binance API.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether to sign the request

        Returns:
            Response JSON
        """
        url = f"{self.base_url}{endpoint}"
        params = params or {}

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 10000  # Add recvWindow for better reliability

            # Sort parameters alphabetically to ensure consistent signature
            sorted_params = dict(sorted(params.items()))

            # Build query string from sorted parameters
            query_string = urlencode(sorted_params)

            # Generate signature from the query string
            signature = self._generate_signature(query_string)

            # Build final URL with query string and signature
            final_url = f"{url}?{query_string}&signature={signature}"

            try:
                if method == "GET":
                    response = requests.get(final_url, headers=self._get_headers())
                elif method == "POST":
                    response = requests.post(final_url, headers=self._get_headers())
                elif method == "DELETE":
                    response = requests.delete(final_url, headers=self._get_headers())
                else:
                    raise ValueError(f"Invalid HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.error(f"Binance API error: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response: {e.response.text}")
                    try:
                        return e.response.json()
                    except:
                        return {"error": str(e)}
                return {"error": str(e)}
        else:
            # For unsigned requests, use params normally
            try:
                if method == "GET":
                    response = requests.get(url, params=params, headers=self._get_headers())
                elif method == "POST":
                    response = requests.post(url, params=params, headers=self._get_headers())
                elif method == "DELETE":
                    response = requests.delete(url, params=params, headers=self._get_headers())
                else:
                    raise ValueError(f"Invalid HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.error(f"Binance API error: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response: {e.response.text}")
                    try:
                        return e.response.json()
                    except:
                        return {"error": str(e)}
                return {"error": str(e)}
    
    # ==================== Account & Position Methods ====================
    
    def get_account_info(self) -> Dict:
        """Get futures account information."""
        return self._make_request("GET", "/fapi/v2/account")
    
    def get_balance(self) -> float:
        """Get available USDT balance."""
        try:
            account = self.get_account_info()
            for asset in account.get("assets", []):
                if asset["asset"] == "USDT":
                    return float(asset["availableBalance"])
            return 0.0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0
    
    def get_positions(self) -> List[PositionInfo]:
        """Get all open positions."""
        try:
            response = self._make_request("GET", "/fapi/v2/positionRisk")
            positions = []
            
            for pos in response:
                qty = float(pos.get("positionAmt", 0))
                if qty != 0:  # Only include positions with non-zero quantity
                    positions.append(PositionInfo(
                        symbol=pos["symbol"],
                        side="LONG" if qty > 0 else "SHORT",
                        entry_price=float(pos.get("entryPrice", 0)),
                        quantity=abs(qty),
                        unrealized_pnl=float(pos.get("unRealizedProfit", 0)),
                        leverage=int(pos.get("leverage", 1)),
                        margin=float(pos.get("isolatedMargin", 0)) if pos.get("marginType") == "isolated" else float(pos.get("notional", 0)) / int(pos.get("leverage", 1)),
                        margin_type=pos.get("marginType", "").upper(),  # CROSSED or ISOLATED
                        liquidation_price=float(pos.get("liquidationPrice", 0)) if float(pos.get("liquidationPrice", 0)) > 0 else None,
                        mark_price=float(pos.get("markPrice", 0)),
                        notional_value=abs(float(pos.get("notional", 0)))
                    ))
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_position_for_symbol(self, symbol: str) -> Optional[PositionInfo]:
        """Get position for a specific symbol."""
        positions = self.get_positions()
        for pos in positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    # ==================== Order Methods ====================
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for a symbol with validation.

        Args:
            symbol: Trading pair symbol
            leverage: Desired leverage (will be capped at max allowed)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate against maximum allowed leverage
            max_leverage = self.get_max_leverage(symbol)
            if leverage > max_leverage:
                logger.warning(
                    f"Requested leverage {leverage}x exceeds maximum {max_leverage}x for {symbol}. "
                    f"Using {max_leverage}x instead."
                )
                leverage = max_leverage

            params = {
                "symbol": symbol,
                "leverage": leverage
            }
            response = self._make_request("POST", "/fapi/v1/leverage", params)
            logger.info(f"Leverage set to {leverage}x for {symbol}")
            return "leverage" in response
        except Exception as e:
            logger.error(f"Error setting leverage: {e}")
            return False
    
    def set_margin_type(self, symbol: str, margin_type: str) -> bool:
        """
        Set margin type for a symbol.

        Args:
            symbol: Trading pair symbol
            margin_type: CROSSED or ISOLATED
        """
        try:
            params = {
                "symbol": symbol,
                "marginType": margin_type
            }
            response = self._make_request("POST", "/fapi/v1/marginType", params)
            logger.info(f"Margin type set to {margin_type} for {symbol}")
            return True
        except Exception as e:
            # Error code -4046 means margin type is already set or cannot be changed
            if "-4046" in str(e) or "No need to change margin type" in str(e):
                # This means the margin type is already set and there may be existing positions
                # We cannot determine the actual current margin type from the error alone
                logger.warning(
                    f"Cannot change margin type to {margin_type} for {symbol}. "
                    f"Reason: Margin type is already set (possibly due to existing position). "
                    f"To use {margin_type} margin, close all existing {symbol} positions first."
                )
                return True
            # Error code -4067 means there are open orders preventing margin type change
            if "-4067" in str(e) or "Position side cannot be changed" in str(e):
                logger.warning(f"Cannot change margin type for {symbol} due to open orders. Proceeding with existing margin type.")
                return True
            logger.error(f"Error setting margin type: {e}")
            return False
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol trading rules."""
        try:
            response = self._make_request("GET", "/fapi/v1/exchangeInfo", signed=False)
            for s in response.get("symbols", []):
                if s["symbol"] == symbol:
                    return s
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current mark price for a symbol."""
        try:
            params = {"symbol": symbol}
            response = self._make_request("GET", "/fapi/v1/ticker/price", params, signed=False)
            return float(response.get("price", 0))
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return None

    def get_min_notional(self, symbol: str) -> float:
        """
        Get minimum notional value for a symbol from Binance.

        Args:
            symbol: Trading pair symbol

        Returns:
            Minimum notional value in USD (default: 5.0)
        """
        try:
            symbol_info = self.get_symbol_info(symbol)
            if symbol_info:
                for filter in symbol_info.get("filters", []):
                    if filter["filterType"] == "MIN_NOTIONAL":
                        min_notional = float(filter.get("notional", 5.0))
                        logger.debug(f"MIN_NOTIONAL for {symbol}: ${min_notional}")
                        return min_notional
            # Fallback default
            logger.warning(f"MIN_NOTIONAL not found for {symbol}, using default $5.0")
            return 5.0
        except Exception as e:
            logger.error(f"Error getting MIN_NOTIONAL for {symbol}: {e}")
            return 5.0

    def get_max_leverage(self, symbol: str) -> int:
        """
        Get maximum leverage allowed for a symbol from Binance.

        Args:
            symbol: Trading pair symbol

        Returns:
            Maximum leverage (default: 20)
        """
        try:
            # Get leverage brackets for the symbol
            params = {"symbol": symbol}
            response = self._make_request("GET", "/fapi/v1/leverageBracket", params)

            if response and len(response) > 0:
                # Response is a list, find the symbol
                for item in response:
                    if item.get("symbol") == symbol:
                        brackets = item.get("brackets", [])
                        if brackets and len(brackets) > 0:
                            # First bracket contains max leverage
                            max_leverage = int(brackets[0].get("initialLeverage", 20))
                            logger.debug(f"MAX_LEVERAGE for {symbol}: {max_leverage}x")
                            return max_leverage

            # Fallback default
            logger.warning(f"MAX_LEVERAGE not found for {symbol}, using default 20x")
            return 20
        except Exception as e:
            logger.error(f"Error getting MAX_LEVERAGE for {symbol}: {e}")
            return 20

    def calculate_quantity(
        self,
        symbol: str,
        position_size_usd: float,
        leverage: int,
        entry_price: float = None
    ) -> Optional[float]:
        """
        Calculate order quantity based on position size and leverage.

        Args:
            symbol: Trading pair symbol
            position_size_usd: Position size in USD (this is the MARGIN, not notional value)
            leverage: Leverage to use
            entry_price: Optional entry price (if not provided, uses current price)

        Returns:
            Quantity to order
        """
        try:
            # Use provided entry price or fetch current price
            price = entry_price if entry_price else self.get_current_price(symbol)
            if not price:
                return None

            # Get symbol info for precision
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return None

            # Calculate quantity for futures with leverage
            # Notional value = Margin × Leverage
            # Quantity = Notional value / Price
            notional_value = position_size_usd * leverage
            quantity = notional_value / price

            logger.info(f"Position calculation: Margin=${position_size_usd}, Leverage={leverage}x, Notional=${notional_value:.2f}, Price=${price}, Quantity={quantity:.2f}")

            # Round to symbol precision
            quantity_precision = 3  # Default
            for filter in symbol_info.get("filters", []):
                if filter["filterType"] == "LOT_SIZE":
                    # Use original string value to avoid float conversion issues
                    # e.g., stepSize="1" should give 0 decimals, not 1
                    step_decimal = Decimal(filter["stepSize"])
                    quantity_precision = abs(step_decimal.as_tuple().exponent)
                    break

            quantity = round(quantity, quantity_precision)
            return quantity

        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            return None
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reduce_only: bool = False
    ) -> OrderResult:
        """
        Place a market order.
        
        Args:
            symbol: Trading pair symbol
            side: BUY or SELL
            quantity: Order quantity
            reduce_only: Whether this is a close-only order
            
        Returns:
            OrderResult with order details
        """
        try:
            params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": quantity
            }
            
            if reduce_only:
                params["reduceOnly"] = "true"
            
            response = self._make_request("POST", "/fapi/v1/order", params)
            
            if "orderId" in response:
                return OrderResult(
                    success=True,
                    order_id=str(response["orderId"]),
                    client_order_id=response.get("clientOrderId"),
                    symbol=response["symbol"],
                    side=response["side"],
                    quantity=float(response["origQty"]),
                    price=float(response.get("avgPrice", 0)),
                    status=response["status"],
                    raw_response=response
                )
            else:
                return OrderResult(
                    success=False,
                    message=response.get("msg", "Unknown error"),
                    raw_response=response
                )
                
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return OrderResult(success=False, message=str(e))
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
        reduce_only: bool = False
    ) -> OrderResult:
        """
        Place a limit order.
        
        Args:
            symbol: Trading pair symbol
            side: BUY or SELL
            quantity: Order quantity
            price: Limit price
            time_in_force: GTC (Good Till Cancel), IOC, FOK
            reduce_only: Whether this is a close-only order
            
        Returns:
            OrderResult with order details
        """
        try:
            # Get symbol info for price precision
            symbol_info = self.get_symbol_info(symbol)
            price_precision = 2  # Default
            if symbol_info:
                for filter in symbol_info.get("filters", []):
                    if filter["filterType"] == "PRICE_FILTER":
                        # Use original string value to avoid float conversion issues
                        tick_decimal = Decimal(filter["tickSize"])
                        price_precision = abs(tick_decimal.as_tuple().exponent)
                        break

            # Round price to symbol precision
            formatted_price = round(price, price_precision)
            
            params = {
                "symbol": symbol,
                "side": side,
                "type": "LIMIT",
                "quantity": quantity,
                "price": formatted_price,
                "timeInForce": time_in_force
            }
            
            if reduce_only:
                params["reduceOnly"] = "true"
            
            response = self._make_request("POST", "/fapi/v1/order", params)
            
            if "orderId" in response:
                return OrderResult(
                    success=True,
                    order_id=str(response["orderId"]),
                    client_order_id=response.get("clientOrderId"),
                    symbol=response["symbol"],
                    side=response["side"],
                    quantity=float(response["origQty"]),
                    price=float(response.get("price", formatted_price)),
                    status=response["status"],
                    raw_response=response
                )
            else:
                return OrderResult(
                    success=False,
                    message=response.get("msg", "Unknown error"),
                    raw_response=response
                )
                
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return OrderResult(success=False, message=str(e))
    
    def place_stop_loss(
        self,
        symbol: str,
        side: str,
        stop_price: float,
        quantity: float
    ) -> OrderResult:
        """
        Place a stop loss order using Binance Futures Algo Order API.
        As of Dec 2025, STOP_MARKET orders must use /fapi/v1/algoOrder endpoint.

        Args:
            symbol: Trading pair symbol
            side: BUY (for short) or SELL (for long)
            stop_price: Stop loss trigger price
            quantity: Order quantity
        """
        try:
            # Round stop price to appropriate precision
            symbol_info = self.get_symbol_info(symbol)
            price_precision = 2
            if symbol_info:
                for filter in symbol_info.get("filters", []):
                    if filter["filterType"] == "PRICE_FILTER":
                        # Use original string value to avoid float conversion issues
                        tick_decimal = Decimal(filter["tickSize"])
                        price_precision = abs(tick_decimal.as_tuple().exponent)
                        break

            stop_price = round(stop_price, price_precision)

            # Check minimum notional value (Binance requires >= $5)
            notional = quantity * stop_price
            if notional < 5.0:
                logger.warning(f"Stop loss notional ${notional:.2f} is below minimum $5. Consider increasing position size or leverage.")
                # Use reduceOnly instead to bypass minimum notional check
                params = {
                    "algoType": "CONDITIONAL",
                    "symbol": symbol,
                    "side": side,
                    "type": "STOP_MARKET",
                    "triggerPrice": stop_price,
                    "quantity": quantity,
                    "workingType": "MARK_PRICE",
                    "reduceOnly": "true"
                }
            else:
                # Parameters for Algo Order API
                # Use quantity instead of closePosition to avoid -4509 error
                params = {
                    "algoType": "CONDITIONAL",
                    "symbol": symbol,
                    "side": side,
                    "type": "STOP_MARKET",
                    "triggerPrice": stop_price,
                    "quantity": quantity,
                    "workingType": "MARK_PRICE"
                }

            # Use Algo Order endpoint
            response = self._make_request("POST", "/fapi/v1/algoOrder", params)

            if "algoId" in response:
                return OrderResult(
                    success=True,
                    order_id=str(response["algoId"]),
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=stop_price,
                    status="NEW",
                    raw_response=response
                )
            else:
                return OrderResult(
                    success=False,
                    message=response.get("msg", "Unknown error"),
                    raw_response=response
                )

        except Exception as e:
            logger.error(f"Error placing stop loss: {e}")
            return OrderResult(success=False, message=str(e))
    
    def place_take_profit(
        self,
        symbol: str,
        side: str,
        take_profit_price: float,
        quantity: float
    ) -> OrderResult:
        """
        Place a take profit order using Binance Futures Algo Order API.
        As of Dec 2025, TAKE_PROFIT_MARKET orders must use /fapi/v1/algoOrder endpoint.

        Args:
            symbol: Trading pair symbol
            side: BUY (for short) or SELL (for long)
            take_profit_price: Take profit trigger price
            quantity: Order quantity
        """
        try:
            # Round price to appropriate precision
            symbol_info = self.get_symbol_info(symbol)
            price_precision = 2
            if symbol_info:
                for filter in symbol_info.get("filters", []):
                    if filter["filterType"] == "PRICE_FILTER":
                        # Use original string value to avoid float conversion issues
                        tick_decimal = Decimal(filter["tickSize"])
                        price_precision = abs(tick_decimal.as_tuple().exponent)
                        break

            take_profit_price = round(take_profit_price, price_precision)

            # Check minimum notional value (Binance requires >= $5)
            notional = quantity * take_profit_price
            if notional < 5.0:
                logger.warning(f"Take profit notional ${notional:.2f} is below minimum $5. Consider increasing position size or leverage.")
                # Use reduceOnly instead to bypass minimum notional check
                params = {
                    "algoType": "CONDITIONAL",
                    "symbol": symbol,
                    "side": side,
                    "type": "TAKE_PROFIT_MARKET",
                    "triggerPrice": take_profit_price,
                    "quantity": quantity,
                    "workingType": "MARK_PRICE",
                    "reduceOnly": "true"
                }
            else:
                # Parameters for Algo Order API
                # Use quantity instead of closePosition to avoid -4509 error
                params = {
                    "algoType": "CONDITIONAL",
                    "symbol": symbol,
                    "side": side,
                    "type": "TAKE_PROFIT_MARKET",
                    "triggerPrice": take_profit_price,
                    "quantity": quantity,
                    "workingType": "MARK_PRICE"
                }

            # Use Algo Order endpoint
            response = self._make_request("POST", "/fapi/v1/algoOrder", params)

            if "algoId" in response:
                return OrderResult(
                    success=True,
                    order_id=str(response["algoId"]),
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=take_profit_price,
                    status="NEW",
                    raw_response=response
                )
            else:
                # Handle specific error codes
                error_code = response.get("code")
                error_msg = response.get("msg", "Unknown error")

                if error_code == -2021:
                    # Order would immediately trigger - market moved past TP
                    logger.warning(f"TP order would trigger immediately at {take_profit_price}. Market likely moved past TP already.")
                    return OrderResult(
                        success=False,
                        message=f"TP skipped: Market moved past target price ({error_msg})",
                        raw_response=response
                    )

                return OrderResult(
                    success=False,
                    message=error_msg,
                    raw_response=response
                )

        except Exception as e:
            logger.error(f"Error placing take profit: {e}")
            return OrderResult(success=False, message=str(e))
    
    def open_position(
        self,
        symbol: str,
        side: str,  # LONG or SHORT
        position_size_usd: float,
        leverage: int,
        margin_type: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        time_in_force: str = "GTC"
    ) -> Dict[str, Any]:
        """
        Open a complete position with LIMIT entry order and SL/TP.
        
        Args:
            symbol: Trading pair symbol
            side: LONG or SHORT
            position_size_usd: Position size in USD
            leverage: Leverage to use
            margin_type: CROSSED or ISOLATED
            entry_price: Limit entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            time_in_force: Time in force for limit order (GTC, IOC, FOK)
            
        Returns:
            Dict with order results
        """
        results = {
            "success": False,
            "entry_order": None,
            "sl_order": None,
            "tp_order": None,
            "message": ""
        }

        try:
            # Step 0: Check for existing open position to prevent duplicates
            existing_position = self.get_position_for_symbol(symbol)
            if existing_position and existing_position.quantity > 0:
                # Check if existing position has different margin type
                if existing_position.margin_type != margin_type:
                    error_msg = (
                        f"Cannot open {margin_type} position for {symbol}. "
                        f"Existing {existing_position.margin_type} position detected "
                        f"({existing_position.quantity} contracts, ${existing_position.notional_value:.2f} notional). "
                        f"Binance does not allow changing margin type with open positions. "
                        f"Please close the existing position first, then new trades will use {margin_type} margin."
                    )
                    logger.error(error_msg)
                    results["message"] = error_msg
                    return results

                # Same margin type but position exists
                error_msg = (
                    f"Position already exists for {symbol}. "
                    f"Current position: {existing_position.quantity} {existing_position.side} contracts "
                    f"(${existing_position.notional_value:.2f} notional, {existing_position.margin_type} margin). "
                    f"Close existing position before opening a new one."
                )
                logger.warning(error_msg)
                results["message"] = error_msg
                return results

            # Step 1: Set leverage
            if not self.set_leverage(symbol, leverage):
                results["message"] = "Failed to set leverage"
                return results

            # Step 2: Set margin type
            self.set_margin_type(symbol, margin_type)
            
            # Step 3: Calculate quantity using entry price
            quantity = self.calculate_quantity(symbol, position_size_usd, leverage, entry_price)
            if not quantity:
                results["message"] = "Failed to calculate quantity"
                return results

            # Step 3.5: Validate minimum notional value BEFORE placing any orders
            entry_notional = quantity * entry_price
            # Get dynamic MIN_NOTIONAL from Binance and add small buffer
            base_min_notional = self.get_min_notional(symbol)
            MIN_NOTIONAL = base_min_notional + 0.10  # Add $0.10 buffer to avoid edge cases

            if entry_notional <= MIN_NOTIONAL:
                min_position_size = (MIN_NOTIONAL / leverage) + 0.01  # Add small buffer
                min_leverage = int((MIN_NOTIONAL / position_size_usd) + 1)  # Round up

                error_msg = (
                    f"Order rejected: Notional value ${entry_notional:.2f} is at or below minimum ${MIN_NOTIONAL:.2f}. "
                    f"Current settings: Margin=${position_size_usd}, Leverage={leverage}x, Entry=${entry_price}. "
                    f"To fix: Increase position size to at least ${min_position_size:.2f} "
                    f"OR increase leverage to at least {min_leverage}x."
                )
                logger.error(error_msg)
                results["message"] = error_msg
                return results

            logger.info(f"Notional check passed: ${entry_notional:.2f} > ${MIN_NOTIONAL:.2f}")

            # Step 4: Place LIMIT entry order
            entry_side = "BUY" if side == "LONG" else "SELL"
            entry_result = self.place_limit_order(
                symbol=symbol,
                side=entry_side,
                quantity=quantity,
                price=entry_price,
                time_in_force=time_in_force
            )
            results["entry_order"] = entry_result
            
            if not entry_result.success:
                results["message"] = f"Entry order failed: {entry_result.message}"
                return results
            
            # Use ordered quantity for SL/TP
            order_quantity = entry_result.quantity
            
            # Step 5: Place stop loss
            sl_side = "SELL" if side == "LONG" else "BUY"
            sl_result = self.place_stop_loss(symbol, sl_side, stop_loss, order_quantity)
            results["sl_order"] = sl_result
            
            # Step 6: Place take profit
            tp_result = self.place_take_profit(symbol, sl_side, take_profit, order_quantity)
            results["tp_order"] = tp_result
            
            results["success"] = True
            results["message"] = "Limit order placed successfully with SL/TP"
            
            return results
            
        except Exception as e:
            logger.error(f"Error opening position: {e}")
            results["message"] = str(e)
            return results
    
    def close_position(self, symbol: str, side: str = None) -> OrderResult:
        """
        Close a position for a symbol.
        
        Args:
            symbol: Trading pair symbol
            side: LONG or SHORT (if not provided, will detect from position)
        """
        try:
            # Get current position
            position = self.get_position_for_symbol(symbol)
            if not position:
                return OrderResult(success=False, message="No position found")
            
            # Determine close side
            close_side = "SELL" if position.side == "LONG" else "BUY"
            
            # Cancel all open orders for this symbol first
            self.cancel_all_orders(symbol)
            
            # Place market close order
            return self.place_market_order(
                symbol=symbol,
                side=close_side,
                quantity=position.quantity,
                reduce_only=True
            )
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return OrderResult(success=False, message=str(e))
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for a symbol."""
        try:
            params = {"symbol": symbol}
            response = self._make_request("DELETE", "/fapi/v1/allOpenOrders", params)
            logger.info(f"Cancelled all orders for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            return False
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get all open orders."""
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
            return self._make_request("GET", "/fapi/v1/openOrders", params)
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return []


# Test function
def test_binance_service():
    """Test Binance service connection."""
    service = BinanceService()
    
    print("Testing Binance connection...")
    print(f"Testnet mode: {service.testnet}")
    
    # Test getting balance
    balance = service.get_balance()
    print(f"Available balance: {balance} USDT")
    
    # Test getting positions
    positions = service.get_positions()
    print(f"Open positions: {len(positions)}")
    for pos in positions:
        print(f"  {pos.symbol}: {pos.side} {pos.quantity} @ {pos.entry_price}")
    
    # Test getting price
    price = service.get_current_price("BTCUSDT")
    print(f"BTC price: {price}")


if __name__ == "__main__":
    test_binance_service()
