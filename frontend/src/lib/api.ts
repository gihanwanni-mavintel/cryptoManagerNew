import axios from 'axios';
import type {
  Signal,
  Position,
  TradeConfig,
  TradeConfigUpdate,
  SignalParseResponse,
  TotalPnlResponse,
  TelegramMessageInput,
  Trade,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Signals API
export const signalsApi = {
  parseSignal: async (
    message: TelegramMessageInput,
    autoExecute: boolean = true
  ): Promise<SignalParseResponse> => {
    const response = await api.post(`/api/signals/parse?auto_execute=${autoExecute}`, message);
    return response.data;
  },

  getSignals: async (limit: number = 50, offset: number = 0): Promise<Signal[]> => {
    const response = await api.get(`/api/signals?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  getSignal: async (signalId: number): Promise<Signal> => {
    const response = await api.get(`/api/signals/${signalId}`);
    return response.data;
  },

  getActiveCount: async (): Promise<{ active: number }> => {
    const response = await api.get('/api/signals/active/count');
    return response.data;
  },

  executeSignal: async (signalId: number): Promise<{ success: boolean; message: string; trade?: Trade }> => {
    const response = await api.post(`/api/signals/${signalId}/execute`);
    return response.data;
  },
};

// Trades API
export const tradesApi = {
  getPositions: async (): Promise<Position[]> => {
    const response = await api.get('/api/trades/positions');
    return response.data;
  },

  closePosition: async (tradeId: number): Promise<{ success: boolean; message: string; trade?: Trade }> => {
    const response = await api.post(`/api/trades/close/${tradeId}`);
    return response.data;
  },

  getTotalPnl: async (): Promise<TotalPnlResponse> => {
    const response = await api.get('/api/trades/pnl');
    return response.data;
  },

  getHistory: async (limit: number = 50, offset: number = 0, status?: string): Promise<Trade[]> => {
    let url = `/api/trades/history?limit=${limit}&offset=${offset}`;
    if (status) {
      url += `&status=${status}`;
    }
    const response = await api.get(url);
    return response.data;
  },

  syncPositions: async (): Promise<{ success: boolean; message: string }> => {
    const response = await api.post('/api/trades/sync');
    return response.data;
  },
};

// Config API
export const configApi = {
  getConfig: async (): Promise<TradeConfig> => {
    const response = await api.get('/api/config');
    return response.data;
  },

  updateConfig: async (config: TradeConfigUpdate): Promise<TradeConfig> => {
    const response = await api.put('/api/config', config);
    return response.data;
  },

  resetConfig: async (): Promise<TradeConfig> => {
    const response = await api.post('/api/config/reset');
    return response.data;
  },

  getDefaults: async (): Promise<TradeConfigUpdate & { auto_execute_trades: boolean }> => {
    const response = await api.get('/api/config/defaults');
    return response.data;
  },
};

// Auth API
export const authApi = {
  login: async (username: string, password: string): Promise<{ access_token: string; token_type: string }> => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  register: async (username: string, password: string): Promise<{ message: string; user: { id: number; username: string; role: string } }> => {
    const response = await api.post('/api/auth/register', { username, password });
    return response.data;
  },

  getCurrentUser: async (): Promise<{ id: number; username: string; role: string }> => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },
};

// Add auth interceptor for adding token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
