'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { User, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { authApi } from '@/lib/api';

export default function Header() {
  const router = useRouter();
  const [username, setUsername] = useState('User');

  useEffect(() => {
    // Get current user info
    const fetchUser = async () => {
      try {
        const user = await authApi.getCurrentUser();
        setUsername(user.username);
      } catch (error) {
        console.error('Error fetching user:', error);
      }
    };
    fetchUser();
  }, []);

  const handleLogout = () => {
    // Clear token from localStorage
    localStorage.removeItem('token');

    // Redirect to login page
    router.push('/login');
  };

  return (
    <header className="flex items-center justify-end h-16 px-6 bg-white border-b border-gray-200">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" className="flex items-center gap-2">
          <User className="w-4 h-4" />
          <span>{username}</span>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="flex items-center gap-2 hover:text-red-600"
          onClick={handleLogout}
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </Button>
      </div>
    </header>
  );
}
