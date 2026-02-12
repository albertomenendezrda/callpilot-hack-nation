'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { signOut } from 'next-auth/react';
import {
  LayoutDashboard,
  Calendar,
  Phone,
  Settings,
  Zap,
  Home,
  PanelLeftClose,
  PanelLeftOpen,
  LogOut,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navigation = [
    {
      name: 'Overview',
      href: '/dashboard',
      icon: LayoutDashboard,
      current: pathname === '/dashboard',
    },
    {
      name: 'AI Chat',
      href: '/dashboard/chat',
      icon: Calendar,
      current: pathname === '/dashboard/chat',
    },
    {
      name: 'Active Tasks',
      href: '/dashboard/tasks',
      icon: Phone,
      current: pathname === '/dashboard/tasks',
    },
    {
      name: 'Connections',
      href: '/dashboard/connections',
      icon: Zap,
      current: pathname === '/dashboard/connections',
    },
    {
      name: 'Settings',
      href: '/dashboard/settings',
      icon: Settings,
      current: pathname === '/dashboard/settings',
    },
  ];

  return (
    <div className="h-screen bg-white flex overflow-hidden">
      {/* Sidebar: fixed position, full height */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-16'
        } fixed left-0 top-0 h-screen border-r border-black/10 bg-white flex flex-col transition-all duration-200 ease-out z-40`}
      >
        {/* Top row: same height as page headers (h-16) for alignment */}
        <div className="flex-shrink-0 h-16 flex items-center justify-center border-b border-black/10">
          <div className={`flex items-center gap-2 w-full ${sidebarOpen ? 'px-4' : 'px-2 justify-center'}`}>
            <button
              type="button"
              onClick={() => setSidebarOpen((o) => !o)}
              className="p-2 rounded-lg text-black/70 hover:bg-black/10 hover:text-black transition-colors flex-shrink-0"
              aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            >
              {sidebarOpen ? (
                <PanelLeftClose className="h-5 w-5" />
              ) : (
                <PanelLeftOpen className="h-5 w-5" />
              )}
            </button>
            {sidebarOpen && (
              <Link href="/" className="flex items-center gap-2 min-w-0">
                <Phone className="h-6 w-6 text-black flex-shrink-0" />
                <span className="text-xl font-bold text-black truncate">CallPilot</span>
              </Link>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 min-h-0 overflow-y-auto px-3 py-4 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`
                  flex items-center ${sidebarOpen ? 'px-3' : 'px-2 justify-center'} py-2 text-sm font-medium rounded-lg transition-colors
                  ${
                    item.current
                      ? 'bg-black text-white'
                      : 'text-black/70 hover:bg-black/5 hover:text-black'
                  }
                `}
                title={!sidebarOpen ? item.name : undefined}
              >
                <Icon className={`h-5 w-5 ${sidebarOpen ? 'mr-3' : ''} flex-shrink-0`} />
                {sidebarOpen && item.name}
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        {sidebarOpen && (
          <div className="flex-shrink-0 p-4 border-t border-black/10 space-y-2">
            <Link href="/">
              <Button
                variant="outline"
                size="sm"
                className="w-full border-black/10"
              >
                <Home className="h-4 w-4 mr-2" />
                Back to Home
              </Button>
            </Link>
            <Button
              variant="ghost"
              size="sm"
              className="w-full text-black/70 hover:text-black hover:bg-black/5"
              onClick={() => signOut({ callbackUrl: '/' })}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Sign out
            </Button>
          </div>
        )}
      </aside>

      {/* Main content: offset by sidebar width, only this area scrolls */}
      <main className={`${sidebarOpen ? 'ml-64' : 'ml-16'} flex-1 h-screen flex flex-col overflow-hidden transition-all duration-200 ease-out`}>
        {children}
      </main>
    </div>
  );
}
