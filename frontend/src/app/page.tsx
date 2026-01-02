'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { signalsApi } from '@/lib/api';
import type { Signal } from '@/types';
import { formatTime, formatPrice } from '@/lib/utils';

export default function TelegramSignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [activeCount, setActiveCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSignals();
    fetchActiveCount();
  }, []);

  const fetchSignals = async () => {
    try {
      const data = await signalsApi.getSignals(50, 0);
      setSignals(data);
    } catch (error) {
      console.error('Error fetching signals:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchActiveCount = async () => {
    try {
      const data = await signalsApi.getActiveCount();
      setActiveCount(data.active);
    } catch (error) {
      console.error('Error fetching active count:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Telegram Signals</h1>
          <p className="text-gray-500">Latest trading signals from your channels</p>
        </div>
        <div className="text-right">
          <span className="text-sm text-gray-500">{activeCount} Active</span>
        </div>
      </div>

      {/* Signals Grid */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading signals...</div>
      ) : signals.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-gray-500">
            No signals yet. Paste a Telegram signal above to get started.
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {signals.map((signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      )}
    </div>
  );
}

function SignalCard({ signal }: { signal: Signal }) {
  const isLong = signal.setup_type === 'LONG';

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-bold text-lg">{signal.pair}</h3>
            <p className="text-xs text-gray-500 uppercase">
              {signal.channel || 'TELEGRAM'}
            </p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${
              isLong
                ? 'bg-gray-900 text-white'
                : 'bg-gray-900 text-white'
            }`}
          >
            <TrendingUp className={`w-3 h-3 ${!isLong && 'rotate-180'}`} />
            {signal.setup_type}
          </span>
        </div>

        <div className="space-y-3">
          <div className="flex justify-between">
            <div>
              <p className="text-xs text-gray-500">Entry</p>
              <p className="font-semibold">${formatPrice(signal.entry)}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Stop Loss</p>
              <p className="font-semibold text-red-500">
                ${formatPrice(signal.stop_loss)}
              </p>
            </div>
          </div>

          <div>
            <p className="text-xs text-gray-500">Take Profit</p>
            <p className="font-semibold text-green-500">
              ${formatPrice(signal.take_profit)}
            </p>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t flex items-center text-xs text-gray-500">
          <Clock className="w-3 h-3 mr-1" />
          {formatTime(signal.timestamp)}
        </div>
      </CardContent>
    </Card>
  );
}
