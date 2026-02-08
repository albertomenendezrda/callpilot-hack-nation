'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Phone,
  Clock,
  CheckCircle2,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  MapPin,
  Star,
  Calendar,
  DollarSign,
  Activity
} from 'lucide-react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';

interface Booking {
  booking_id: string;
  status: string;
  service_type: string;
  location: string;
  timeframe: string;
  created_at: number;
  results: any[];
}

interface Result {
  provider_id: string;
  provider_name: string;
  phone: string;
  address: string;
  rating: number;
  call_status: 'pending' | 'calling' | 'completed' | 'failed';
  distance?: number;
  travel_time?: number;
  availability_date?: string;
  availability_time?: string;
  score?: number;
  has_availability?: boolean;
}

export default function TasksPage() {
  const [allBookings, setAllBookings] = useState<Booking[]>([]);
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  const fetchAllBookings = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
      const res = await fetch(`${apiUrl}/api/dashboard/bookings`);
      const data = await res.json();

      // Sort: processing first, then completed, newest first within each group
      const bookings = (data.bookings || []).sort((a: Booking, b: Booking) => {
        // First, prioritize processing tasks
        if (a.status === 'processing' && b.status !== 'processing') return -1;
        if (a.status !== 'processing' && b.status === 'processing') return 1;

        // Within same status, sort by newest first
        return b.created_at - a.created_at;
      });

      setAllBookings(bookings);

      // Auto-expand processing bookings
      const processing = bookings.filter((b: Booking) => b.status === 'processing');
      const newExpanded = new Set(expandedTasks);
      processing.forEach((b: Booking) => newExpanded.add(b.booking_id));
      setExpandedTasks(newExpanded);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching bookings:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllBookings();

    // Auto-refresh every 2 seconds
    const interval = setInterval(fetchAllBookings, 2000);
    return () => clearInterval(interval);
  }, []);

  const toggleExpand = (bookingId: string) => {
    const newExpanded = new Set(expandedTasks);
    if (newExpanded.has(bookingId)) {
      newExpanded.delete(bookingId);
    } else {
      newExpanded.add(bookingId);
    }
    setExpandedTasks(newExpanded);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'processing':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            Processing
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Completed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {status}
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin mx-auto mb-4 text-black" />
          <p className="text-black/60">Loading tasks...</p>
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
              <Activity className="h-6 w-6 text-black" />
              <h1 className="text-2xl font-bold text-black">All Tasks</h1>
              <span className="text-sm text-black/50">
                ({allBookings.filter(b => b.status === 'processing').length} active)
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchAllBookings}
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
        {allBookings.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircle2 className="h-16 w-16 mx-auto mb-4 text-black/20" />
            <h3 className="text-lg font-semibold text-black mb-2">
              No Tasks Yet
            </h3>
            <p className="text-black/60 mb-6">
              Start by creating your first booking request
            </p>
            <Link href="/dashboard/voice">
              <Button className="bg-black text-white hover:bg-black/90">
                Create New Booking
              </Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {allBookings.map((task) => {
              const isExpanded = expandedTasks.has(task.booking_id);
              const progress = task.results || [];
              const completedCalls = progress.filter((p: Result) => p.call_status === 'completed').length;
              const totalCalls = progress.length;

              return (
                <Card key={task.booking_id} className="border-2 border-black/10 overflow-hidden">
                  {/* Card Header - Always Visible */}
                  <CardHeader
                    className="cursor-pointer hover:bg-black/5 transition-colors"
                    onClick={() => toggleExpand(task.booking_id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3 flex-1">
                        <div className="flex items-center space-x-2">
                          {task.status === 'processing' ? (
                            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                          ) : (
                            <CheckCircle2 className="h-5 w-5 text-green-600" />
                          )}
                          <CardTitle className="capitalize text-xl">
                            {task.service_type.replace('_', ' ')}
                          </CardTitle>
                        </div>
                        {getStatusBadge(task.status)}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-5 w-5" />
                        ) : (
                          <ChevronDown className="h-5 w-5" />
                        )}
                      </Button>
                    </div>
                    <CardDescription className="flex items-center gap-4 mt-2 flex-wrap">
                      <span className="flex items-center">
                        <MapPin className="h-4 w-4 mr-1" />
                        {task.location}
                      </span>
                      <span className="flex items-center">
                        <Calendar className="h-4 w-4 mr-1" />
                        {task.timeframe?.replace('_', ' ') || 'ASAP'}
                      </span>
                      <span className="flex items-center text-xs">
                        <Clock className="h-4 w-4 mr-1" />
                        {new Date(task.created_at * 1000).toLocaleString()}
                      </span>
                    </CardDescription>
                  </CardHeader>

                  {/* Expandable Content */}
                  {isExpanded && (
                    <CardContent className="border-t border-black/10 bg-black/[0.02]">
                      {/* Processing View */}
                      {task.status === 'processing' && (
                        <div className="py-4">
                          <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold flex items-center">
                              <Phone className="h-5 w-5 mr-2" />
                              Live Calling Progress
                            </h3>
                            <div className="text-sm text-black/60">
                              {completedCalls}/{totalCalls} calls completed
                            </div>
                          </div>

                          {/* Progress Bar */}
                          <div className="mb-6">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm font-medium text-black/70">
                                Overall Progress
                              </span>
                              <span className="text-sm font-semibold">
                                {totalCalls > 0 ? Math.round((completedCalls / totalCalls) * 100) : 0}%
                              </span>
                            </div>
                            <div className="w-full bg-black/10 rounded-full h-3 overflow-hidden">
                              <div
                                className="bg-gradient-to-r from-blue-500 to-blue-600 h-full transition-all duration-500"
                                style={{ width: `${totalCalls > 0 ? (completedCalls / totalCalls) * 100 : 0}%` }}
                              />
                            </div>
                          </div>

                          {/* Call List */}
                          <div className="space-y-3">
                            {progress.map((call: Result, idx: number) => (
                              <div
                                key={idx}
                                className="flex items-center justify-between p-4 bg-white rounded-lg border border-black/10"
                              >
                                <div className="flex items-center space-x-3 flex-1">
                                  {call.call_status === 'completed' ? (
                                    <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
                                  ) : call.call_status === 'calling' ? (
                                    <Loader2 className="h-5 w-5 animate-spin text-blue-600 flex-shrink-0" />
                                  ) : call.call_status === 'failed' ? (
                                    <div className="h-5 w-5 rounded-full border-2 border-red-500 flex-shrink-0" />
                                  ) : (
                                    <div className="h-5 w-5 rounded-full border-2 border-black/20 flex-shrink-0" />
                                  )}
                                  <div className="flex-1 min-w-0">
                                    <p className="font-semibold text-sm truncate">
                                      {call.provider_name}
                                    </p>
                                    {call.address && (
                                      <p className="text-xs text-black/50 truncate">{call.address}</p>
                                    )}
                                  </div>
                                </div>
                                <div className="flex items-center space-x-3">
                                  {call.rating && (
                                    <div className="flex items-center text-sm">
                                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500 mr-1" />
                                      <span className="font-medium">{call.rating}</span>
                                    </div>
                                  )}
                                  <div className="text-xs text-black/50">
                                    {call.call_status === 'completed' && '✓ Done'}
                                    {call.call_status === 'calling' && 'Calling...'}
                                    {call.call_status === 'pending' && 'Pending'}
                                    {call.call_status === 'failed' && '✗ Failed'}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Completed View - Results */}
                      {task.status === 'completed' && (
                        <div className="py-4">
                          <h3 className="text-lg font-semibold mb-4 flex items-center">
                            <CheckCircle2 className="h-5 w-5 mr-2 text-green-600" />
                            Booking Results
                          </h3>

                          {task.results && task.results.filter((r: Result) => r.availability_date).length > 0 ? (
                            <div className="space-y-3">
                              {task.results.filter((r: Result) => r.availability_date).slice(0, 5).map((result: any, idx: number) => (
                                <div
                                  key={idx}
                                  className="p-4 rounded-lg border-2 border-black/10 bg-white"
                                >
                                  <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center space-x-2">
                                      <h4 className="font-semibold text-base">
                                        {result.provider_name}
                                      </h4>
                                    </div>
                                    <div className="flex items-center space-x-1">
                                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                                      <span className="font-semibold text-sm">{result.rating}</span>
                                    </div>
                                  </div>

                                  <div className="space-y-2 text-sm">
                                    <div className="flex items-start">
                                      <MapPin className="h-4 w-4 mr-2 mt-0.5 text-black/50" />
                                      <span className="text-black/70">{result.address}</span>
                                    </div>
                                    <div className="flex items-start">
                                      <Calendar className="h-4 w-4 mr-2 mt-0.5 text-black/50" />
                                      <span className="text-black/70">
                                        {result.availability_date} at {result.availability_time}
                                      </span>
                                    </div>
                                    <div className="flex items-start">
                                      <Phone className="h-4 w-4 mr-2 mt-0.5 text-black/50" />
                                      <span className="text-black/70">{result.phone}</span>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="text-center py-8 text-black/50">
                              <p>No providers had availability for this request</p>
                            </div>
                          )}
                        </div>
                      )}
                    </CardContent>
                  )}
                </Card>
              );
            })}
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
