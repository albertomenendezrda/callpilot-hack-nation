'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  CheckCircle2,
  XCircle,
  RefreshCw,
  Zap
} from 'lucide-react';

interface Connection {
  name: string;
  status: 'connected' | 'disconnected';
  description: string;
}

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<Record<string, Connection>>({});
  const [loading, setLoading] = useState(true);

  const fetchConnections = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
      const res = await fetch(`${apiUrl}/api/connections`);
      const data = await res.json();
      setConnections(data.connections || {});
      setLoading(false);
    } catch (error) {
      console.error('Error fetching connections:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConnections();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin mx-auto mb-4 text-black" />
          <p className="text-black/60">Loading connections...</p>
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
