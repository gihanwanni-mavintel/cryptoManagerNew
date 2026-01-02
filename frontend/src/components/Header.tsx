'use client';

import React from 'react';
import { User, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Header() {
  return (
    <header className="flex items-center justify-end h-16 px-6 bg-white border-b border-gray-200">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" className="flex items-center gap-2">
          <User className="w-4 h-4" />
          <span>Admin</span>
        </Button>
        <Button variant="ghost" size="sm" className="flex items-center gap-2">
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </Button>
      </div>
    </header>
  );
}
