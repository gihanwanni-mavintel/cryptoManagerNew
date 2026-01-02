'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, X, RefreshCw } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { tradesApi } from '@/lib/api';
import type { Position, TotalPnlResponse } from '@/types';
import { formatPrice, formatPnl, formatPercent } from '@/lib/utils';

export default function ActivePositionsPage() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [pnlData, setPnlData] = useState<TotalPnlResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [positionsData, pnl] = await Promise.all([
        tradesApi.getPositions(),
        tradesApi.getTotalPnl(),
      ]);
      setPositions(positionsData);
      setPnlData(pnl);
    } catch (error) {
      console.error('Error fetching positions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await tradesApi.syncPositions();
      await fetchData();
    } catch (error) {
      console.error('Error refreshing:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleClosePosition = async (tradeId: number) => {
    if (!confirm('Are you sure you want to close this position?')) return;

    try {
      const result = await tradesApi.closePosition(tradeId);
      if (result.success) {
        alert('Position closed successfully!');
        fetchData();
      } else {
        alert(`Error: ${result.message}`);
      }
    } catch (error) {
      console.error('Error closing position:', error);
      alert('Failed to close position');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Active Positions</h1>
          <p className="text-gray-500">Monitor and manage your open positions</p>
        </div>
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <div className="text-right">
            <p className="text-sm text-gray-500">Total P&L</p>
            <p
              className={`text-xl font-mono font-bold ${
                (pnlData?.total_pnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'
              }`}
            >
              {formatPnl(pnlData?.total_pnl || 0)}
            </p>
          </div>
        </div>
      </div>

      {/* Positions */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading positions...</div>
      ) : positions.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-gray-500 mb-2">No active positions</p>
            <p className="text-sm text-gray-400">
              Open a position from the Manual Trading tab
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {positions.map((position) => (
            <PositionCard
              key={position.id}
              position={position}
              onClose={handleClosePosition}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function PositionCard({
  position,
  onClose,
}: {
  position: Position;
  onClose: (id: number) => void;
}) {
  const isLong = position.side === 'LONG';
  const isProfitable = position.unrealized_pnl >= 0;

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-bold text-lg">{position.pair}</h3>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`px-2 py-0.5 rounded text-xs font-medium ${
                  isLong
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-700'
                }`}
              >
                {position.side}
              </span>
              <span className="text-xs text-gray-500">
                {position.leverage}x
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="text-gray-400 hover:text-red-500 hover:bg-red-50"
            onClick={() => onClose(position.id)}
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* PnL */}
        <div
          className={`p-3 rounded-lg mb-4 ${
            isProfitable ? 'bg-green-50' : 'bg-red-50'
          }`}
        >
          <p className="text-xs text-gray-500 mb-1">Unrealized P&L</p>
          <div className="flex items-baseline gap-2">
            <span
              className={`text-xl font-bold font-mono ${
                isProfitable ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {formatPnl(position.unrealized_pnl)}
            </span>
            <span
              className={`text-sm ${
                isProfitable ? 'text-green-600' : 'text-red-600'
              }`}
            >
              ({formatPercent(position.unrealized_pnl_percent)})
            </span>
          </div>
        </div>

        {/* Details */}
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Entry Price</span>
            <span className="font-mono">${formatPrice(position.entry_price)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Quantity</span>
            <span className="font-mono">{position.quantity.toFixed(4)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Margin</span>
            <span className="font-mono">${position.margin.toFixed(2)}</span>
          </div>
          {position.stop_loss && (
            <div className="flex justify-between">
              <span className="text-gray-500">Stop Loss</span>
              <span className="font-mono text-red-500">
                ${formatPrice(position.stop_loss)}
              </span>
            </div>
          )}
          {position.take_profit && (
            <div className="flex justify-between">
              <span className="text-gray-500">Take Profit</span>
              <span className="font-mono text-green-500">
                ${formatPrice(position.take_profit)}
              </span>
            </div>
          )}
          {position.liquidation_price && (
            <div className="flex justify-between">
              <span className="text-gray-500">Liquidation</span>
              <span className="font-mono text-orange-500">
                ${formatPrice(position.liquidation_price)}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
