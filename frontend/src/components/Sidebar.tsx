'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Radio, 
  TrendingUp, 
  Settings, 
  ChevronLeft,
  User,
  LogOut
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { name: 'Telegram Signals', href: '/', icon: Radio },
  { name: 'Active Positions', href: '/positions', icon: TrendingUp },
  { name: 'Trade Management', href: '/trade-management', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        'flex flex-col h-screen bg-white border-r border-gray-200 transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-gray-200">
        {!collapsed && (
          <h1 className="text-lg font-bold text-gray-900">
            Crypto Position Manager
          </h1>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
                isActive
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              )}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span className="text-sm">{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-2 p-4 text-gray-600 hover:text-gray-900 border-t border-gray-200"
      >
        <ChevronLeft
          className={cn(
            'w-5 h-5 transition-transform',
            collapsed && 'rotate-180'
          )}
        />
        {!collapsed && <span className="text-sm">Collapse</span>}
      </button>
    </aside>
  );
}
