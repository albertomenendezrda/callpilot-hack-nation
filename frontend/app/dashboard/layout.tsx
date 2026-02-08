'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  LayoutDashboard,
  Calendar,
  Phone,
  Settings,
  Zap,
  Home,
  Mic,
  PanelLeftClose,
  PanelLeftOpen,
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
      name: 'Voice AI',
      href: '/dashboard/voice',
      icon: Mic,
      current: pathname === '/dashboard/voice',
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
      {/* Sidebar: fixed width when open, narrow strip when closed; top aligns with main */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-14'
        } flex-shrink-0 border-r border-black/10 bg-white flex flex-col transition-[width] duration-200 ease-out overflow-hidden`}
      >
        {/* Top row: same height as page headers (h-16) for alignment */}
        <div className="flex-shrink-0 h-16 flex items-center border-b border-black/10">
          <div className="flex items-center gap-2 w-full px-3">
            <button
              type="button"
              onClick={() => setSidebarOpen((o) => !o)}
              className="p-2 rounded-lg text-black/70 hover:bg-black/10 hover:text-black transition-colors"
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
        {sidebarOpen && (
          <>
            <nav className="flex-1 min-h-0 overflow-y-auto px-3 py-4 space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`
                      flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors
                      ${
                        item.current
                          ? 'bg-black text-white'
                          : 'text-black/70 hover:bg-black/5 hover:text-black'
                      }
                    `}
                  >
                    <Icon className="h-5 w-5 mr-3 flex-shrink-0" />
                    {item.name}
                  </Link>
                );
              })}
            </nav>

            {/* Bottom section */}
            <div className="flex-shrink-0 p-4 border-t border-black/10">
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
            </div>
          </>
        )}
      </aside>

      {/* Main content: only this area scrolls */}
      <main className="flex-1 min-h-0 flex flex-col overflow-auto">
        {children}
      </main>
    </div>
  );
}
