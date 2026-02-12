'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Phone,
  Calendar,
  Clock,
  TrendingUp,
  Activity,
  MapPin,
  RefreshCw,
  PhoneCall
} from 'lucide-react';
import Link from 'next/link';
import { signOut } from 'next-auth/react';
import { apiClient, WaitlistError, UnauthorizedError } from '@/lib/api-client';

interface DashboardStats {
  total_bookings: number;
  completed: number;
  processing: number;
  total_calls_made: number;
  success_rate: number;
}

interface Booking {
  booking_id: string;
  status: string;
  service_type: string;
  location: string;
  created_at: number;
  results: any[];
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [unauthorized, setUnauthorized] = useState(false);
  const [backendAuthConfigured, setBackendAuthConfigured] = useState<boolean | null>(null);
  const retryCount = useRef(0);
  const router = useRouter();

  const fetchDashboardData = async () => {
    try {
      const [statsData, bookingsData] = await Promise.all([
        apiClient.getDashboardStats(),
        apiClient.getDashboardBookings(),
      ]);
      setStats(statsData.stats);
      setBookings((bookingsData.bookings || []) as unknown as Booking[]);
      setUnauthorized(false);
      retryCount.current = 0;
      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      if (error instanceof WaitlistError) {
        // Redirect waitlist users away — they shouldn't see the dashboard at all
        await signOut({ redirect: false });
        router.replace('/waitlist');
        return;
      } else if (error instanceof UnauthorizedError) {
        // On first load the token may not be ready yet; retry once silently
        if (retryCount.current < 2) {
          retryCount.current++;
          setTimeout(fetchDashboardData, 1000);
          return;
        }
        setUnauthorized(true);
      }
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'processing':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  if (loading && !unauthorized) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin mx-auto mb-4 text-black" />
          <p className="text-black/60">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const checkBackendAuth = async () => {
    setBackendAuthConfigured(null);
    const base = process.env.NEXT_PUBLIC_API_URL || '';
    if (!base) return;
    try {
      const res = await fetch(`${base.replace(/\/$/, '')}/api/debug/auth-configured`);
      const data = await res.json().catch(() => ({}));
      setBackendAuthConfigured(Boolean((data as { auth_configured?: boolean }).auth_configured));
    } catch {
      setBackendAuthConfigured(false);
    }
  };

  if (unauthorized) {
    return (
      <div className="h-full flex flex-col bg-white overflow-hidden">
        <div className="flex-shrink-0 h-16 flex items-center border-b border-black/10 bg-white" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card className="border-2 border-amber-200 bg-amber-50">
            <CardHeader>
              <CardTitle>Session could not be verified</CardTitle>
              <CardDescription>
                The backend could not verify your sign-in. On the <strong>cloud deployment</strong>, the backend gets env from gcloud, not from <code className="bg-amber-100 px-1 rounded">backend/.env</code>. Run <code className="bg-amber-100 px-1 rounded">./scripts/set-backend-auth-secret.sh</code> to push <code className="bg-amber-100 px-1 rounded">NEXTAUTH_SECRET</code> to both Cloud Run services, then sign out and sign in again. See <code className="bg-amber-100 px-1 rounded">docs/AUTH_AND_ENV.md</code>.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <div className="flex flex-wrap gap-2">
                <Button onClick={() => signOut({ callbackUrl: '/auth/signin' })} variant="outline" className="border-amber-300 text-amber-900 hover:bg-amber-100">
                  Sign out and try again
                </Button>
                <Button onClick={() => { setUnauthorized(false); fetchDashboardData(); }} variant="ghost" className="text-amber-900">
                  Retry
                </Button>
                <Button onClick={checkBackendAuth} variant="ghost" size="sm" className="text-amber-800">
                  {backendAuthConfigured === null ? 'Check if backend has secret' : 'Re-check backend'}
                </Button>
              </div>
              {backendAuthConfigured !== null && (
                <p className="text-sm text-amber-900">
                  Backend reports: <strong>{backendAuthConfigured ? 'auth configured (secret is set)' : 'auth not configured (NEXTAUTH_SECRET missing on Cloud Run)'}</strong>
                  {!backendAuthConfigured && ' → Run ./scripts/set-backend-auth-secret.sh and redeploy backend if needed.'}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white overflow-hidden">
      {/* Header: same height as sidebar top (h-16) so they align */}
      <div className="flex-shrink-0 h-16 flex items-center border-b border-black/10 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-black">Dashboard Overview</h1>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchDashboardData}
              className="border-black/10"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content: scrollable */}
      <div className="flex-1 min-h-0 overflow-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="border-2 border-black/10">
            <CardHeader className="pb-3">
              <CardDescription>Total Bookings</CardDescription>
              <CardTitle className="text-4xl">{stats?.total_bookings || 0}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-black/60">
                <Activity className="h-4 w-4 mr-1" />
                All time
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-black/10">
            <CardHeader className="pb-3">
              <CardDescription>Calls Made</CardDescription>
              <CardTitle className="text-4xl">{stats?.total_calls_made || 0}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-black/60">
                <PhoneCall className="h-4 w-4 mr-1" />
                AI voice calls
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-black/10">
            <CardHeader className="pb-3">
              <CardDescription>Success Rate</CardDescription>
              <CardTitle className="text-4xl">
                {stats?.success_rate ? stats.success_rate.toFixed(0) : 0}%
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-black/60">
                <TrendingUp className="h-4 w-4 mr-1" />
                Completed bookings
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-black/10">
            <CardHeader className="pb-3">
              <CardDescription>Processing</CardDescription>
              <CardTitle className="text-4xl">{stats?.processing || 0}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-black/60">
                <Clock className="h-4 w-4 mr-1" />
                Active now
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Bookings */}
        <Card className="border-2 border-black/10">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Calendar className="h-5 w-5 mr-2" />
              Recent Bookings
            </CardTitle>
            <CardDescription>
              Latest booking requests and their status
            </CardDescription>
          </CardHeader>
          <CardContent>
            {bookings.length === 0 ? (
              <div className="text-center py-12">
                <Phone className="h-12 w-12 mx-auto mb-4 text-black/20" />
                <p className="text-black/60 mb-4">No bookings yet</p>
                <Link href="/book">
                  <Button className="bg-black text-white hover:bg-black/90">
                    Create First Booking
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {bookings.map((booking) => (
                  <div
                    key={booking.booking_id}
                    className="border-2 border-black/5 rounded-lg p-4 hover:border-black/20 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="font-semibold text-black capitalize">
                            {booking.service_type.replace('_', ' ')}
                          </span>
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                              booking.status
                            )}`}
                          >
                            {booking.status}
                          </span>
                        </div>
                        <div className="flex items-center text-sm text-black/60 space-x-4">
                          <span className="flex items-center">
                            <MapPin className="h-4 w-4 mr-1" />
                            {booking.location}
                          </span>
                          <span className="flex items-center">
                            <Clock className="h-4 w-4 mr-1" />
                            {formatDate(booking.created_at)}
                          </span>
                          {booking.results && booking.results.length > 0 && (
                            <span className="flex items-center">
                              <Phone className="h-4 w-4 mr-1" />
                              {booking.results.length} calls made
                            </span>
                          )}
                        </div>
                      </div>
                      {booking.status === 'completed' && (
                        <Link href={`/booking/${booking.booking_id}`}>
                          <Button size="sm" variant="outline" className="border-black/10">
                            View Results
                          </Button>
                        </Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Last Update */}
        <div className="mt-6 text-center text-sm text-black/50">
          Last updated: {lastUpdate.toLocaleTimeString()}
          <span className="mx-2">•</span>
          Auto-refreshes every 5 seconds
        </div>
        </div>
      </div>
    </div>
  );
}
