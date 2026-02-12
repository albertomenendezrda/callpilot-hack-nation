'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { signOut } from 'next-auth/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  CheckCircle2,
  XCircle,
  RefreshCw,
  Zap
} from 'lucide-react';
import { apiClient, WaitlistError, UnauthorizedError } from '@/lib/api-client';

interface Connection {
  name: string;
  status: 'connected' | 'disconnected';
  description: string;
}

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<Record<string, Connection>>({});
  const [loading, setLoading] = useState(true);
  const [unauthorized, setUnauthorized] = useState(false);
  const retryCount = useRef(0);
  const router = useRouter();

  const fetchConnections = async () => {
    try {
      const data = await apiClient.getConnections();
      setConnections((data.connections || {}) as unknown as Record<string, Connection>);
      setUnauthorized(false);
      retryCount.current = 0;
      setLoading(false);
    } catch (error) {
      console.error('Error fetching connections:', error);
      if (error instanceof WaitlistError) {
        await signOut({ redirect: false });
        router.replace('/waitlist');
        return;
      } else if (error instanceof UnauthorizedError) {
        if (retryCount.current < 2) {
          retryCount.current++;
          setTimeout(fetchConnections, 1000);
          return;
        }
        setUnauthorized(true);
      }
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConnections();
  }, []);

  if (loading && !unauthorized) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin mx-auto mb-4 text-black" />
          <p className="text-black/60">Loading connections...</p>
        </div>
      </div>
    );
  }

  if (unauthorized) {
    return (
      <div className="min-h-full flex flex-col bg-white">
        <div className="flex-shrink-0 h-16 flex items-center border-b border-black/10 bg-white" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card className="border-2 border-amber-200 bg-amber-50">
            <CardHeader>
              <CardTitle>Session could not be verified</CardTitle>
              <CardDescription>
                The backend could not verify your sign-in. On the cloud deployment, set <code className="bg-amber-100 px-1 rounded">NEXTAUTH_SECRET</code> on the backend (same as frontend). See <code className="bg-amber-100 px-1 rounded">docs/AUTH_AND_ENV.md</code>.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Button onClick={() => signOut({ callbackUrl: '/auth/signin' })} variant="outline" className="border-amber-300 text-amber-900 hover:bg-amber-100">
                Sign out and try again
              </Button>
              <Button onClick={() => { setUnauthorized(false); fetchConnections(); }} variant="ghost" className="text-amber-900">
                Retry
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full flex flex-col bg-white">
      {/* Header: same height as sidebar (h-16) */}
      <div className="flex-shrink-0 h-16 flex items-center border-b border-black/10 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Zap className="h-6 w-6 text-black" />
            <h1 className="text-2xl font-bold text-black">Connections</h1>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchConnections}
            className="border-black/10"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Main Content: scrollable */}
      <div className="flex-1 min-h-0 overflow-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-black/60 mb-6">
          Manage your API connections and integrations
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(connections).map(([key, connection]) => (
            <Card key={key} className="border-2 border-black/10">
              <CardHeader>
                <div className="flex items-center justify-between mb-2">
                  <CardTitle className="text-lg">{connection.name}</CardTitle>
                  {connection.status === 'connected' ? (
                    <CheckCircle2 className="h-6 w-6 text-green-600" />
                  ) : (
                    <XCircle className="h-6 w-6 text-red-600" />
                  )}
                </div>
                <CardDescription>{connection.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <span
                    className={`text-sm font-medium ${
                      connection.status === 'connected'
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {connection.status === 'connected' ? '● Connected' : '○ Disconnected'}
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-black/10"
                    disabled={connection.status === 'connected'}
                  >
                    {connection.status === 'connected' ? 'Connected' : 'Connect'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        </div>
      </div>
    </div>
  );
}
