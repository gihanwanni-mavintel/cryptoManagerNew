// Signal types
export interface Signal {
  id: number;
  pair: string;
  setup_type: 'LONG' | 'SHORT';
  entry: number;
  stop_loss: number;
  take_profit: number;
  timestamp: string;
  full_message?: string;
  channel?: string;
}

// Trade types
export interface Trade {
  id: number;
  user_id?: number;
  signal_id?: number;
  pair: string;
  side: 'LONG' | 'SHORT' | 'BUY' | 'SELL';
  leverage: number;
  entry_price?: number;
  entry_quantity?: number;
  stop_loss?: number;
  take_profit?: number;
  status: 'PENDING' | 'OPEN' | 'CLOSED' | 'CANCELLED';
  binance_order_id?: string;
  binance_position_id?: string;
  opened_at?: string;
  closed_at?: string;
  exit_price?: number;
  pnl?: number;
  pnl_percent?: number;
  exit_reason?: string;
  created_at?: string;
}

// Position types
export interface Position {
  id: number;
  pair: string;
  side: 'LONG' | 'SHORT';
  entry_price: number;
  quantity: number;
  leverage: number;
  stop_loss?: number;
  take_profit?: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  margin: number;
  liquidation_price?: number;
  opened_at?: string;
  status: string;
}

// Config types
export interface TradeConfig {
  id: number;
  user_id: number;
  margin_mode: 'CROSSED' | 'ISOLATED';
  max_leverage: number;
  max_position_size: number;
  sl_percentage: number;
  tp_percentage: number;
  auto_execute_trades: boolean;
  created_at: string;
  updated_at: string;
}

export interface TradeConfigUpdate {
  margin_mode?: 'CROSSED' | 'ISOLATED';
  max_leverage?: number;
  max_position_size?: number;
  sl_percentage?: number;
  tp_percentage?: number;
  auto_execute_trades?: boolean;
}

// API response types
export interface SignalParseResponse {
  success: boolean;
  signal?: Signal;
  trade?: Trade;
  message: string;
}

export interface TotalPnlResponse {
  total_pnl: number;
  total_pnl_percent: number;
  open_positions: number;
  total_trades: number;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
}

// Input types
export interface TelegramMessageInput {
  text: string;
  sender?: string;
  channel?: string;
}
