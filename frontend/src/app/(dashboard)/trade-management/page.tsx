'use client';

import React, { useState, useEffect } from 'react';
import { Settings } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { configApi } from '@/lib/api';
import type { TradeConfig } from '@/types';

export default function TradeManagementPage() {
  const [config, setConfig] = useState<TradeConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    max_position_size: 1000,
    max_leverage: 6,
    margin_mode: 'CROSSED' as 'CROSSED' | 'ISOLATED',
  });

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const data = await configApi.getConfig();
      setConfig(data);
      setFormData({
        max_position_size: data.max_position_size || 1000,
        max_leverage: data.max_leverage || 6,
        margin_mode: data.margin_mode || 'CROSSED',
      });
    } catch (error) {
      console.error('Error fetching config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await configApi.updateConfig(formData);
      await fetchConfig();
      alert('Configuration saved successfully!');
    } catch (error) {
      console.error('Error saving config:', error);
      alert('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset to default settings?')) return;
    
    setSaving(true);
    try {
      await configApi.resetConfig();
      await fetchConfig();
      alert('Configuration reset to defaults!');
    } catch (error) {
      console.error('Error resetting config:', error);
      alert('Failed to reset configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: string, value: string | number | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading configuration...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Settings className="w-8 h-8 text-gray-700" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trade Management</h1>
          <p className="text-gray-500">Configure your trading parameters and risk management</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings Form */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Trade Management Settings</CardTitle>
              <p className="text-sm text-gray-500">
                Set your maximum position size, leverage, and take profit exit percentages
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Position Size and Leverage Row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Maximum Position Size ($)
                  </label>
                  <Input
                    type="number"
                    value={formData.max_position_size}
                    onChange={(e) => handleInputChange('max_position_size', parseFloat(e.target.value) || 0)}
                    placeholder="1000"
                  />
                  <p className="text-xs text-gray-500 mt-1">Maximum dollar amount per position</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Maximum Leverage (x)
                  </label>
                  <Input
                    type="number"
                    value={formData.max_leverage}
                    onChange={(e) => handleInputChange('max_leverage', parseInt(e.target.value) || 1)}
                    placeholder="6"
                    min={1}
                    max={125}
                  />
                  <p className="text-xs text-gray-500 mt-1">Maximum leverage multiplier</p>
                </div>
              </div>

              {/* Margin Mode Toggle */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Margin Mode</h3>
                    <p className="text-sm text-gray-500">Cross margin uses entire account balance</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-sm ${formData.margin_mode === 'ISOLATED' ? 'font-medium' : 'text-gray-500'}`}>
                      Isolated
                    </span>
                    <Switch
                      checked={formData.margin_mode === 'CROSSED'}
                      onCheckedChange={(checked) => 
                        handleInputChange('margin_mode', checked ? 'CROSSED' : 'ISOLATED')
                      }
                    />
                    <span className={`text-sm ${formData.margin_mode === 'CROSSED' ? 'font-medium' : 'text-gray-500'}`}>
                      Cross
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <Button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex-1"
                >
                  {saving ? 'Saving...' : 'Save Configuration'}
                </Button>
                <Button
                  onClick={handleReset}
                  disabled={saving}
                  variant="outline"
                >
                  Reset to Defaults
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Current Configuration Display */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Current Configuration</CardTitle>
              <p className="text-sm text-gray-500">Active trading parameters</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-gray-500">Max Position</p>
                <p className="text-2xl font-bold">${config?.max_position_size || 1000}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Max Leverage</p>
                <p className="text-2xl font-bold">{config?.max_leverage || 6}x</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Margin Mode</p>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    config?.margin_mode === 'CROSSED' ? 'bg-purple-500' : 'bg-blue-500'
                  }`} />
                  <p className="text-2xl font-bold">{config?.margin_mode || 'CROSSED'}</p>
                </div>
              </div>
              <div className="pt-4 border-t">
                <p className="text-sm text-gray-500">Status</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                  <span className="text-green-600 font-medium">Valid</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
