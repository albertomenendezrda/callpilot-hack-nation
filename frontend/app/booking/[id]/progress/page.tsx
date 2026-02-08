'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Phone,
  CheckCircle2,
  Clock,
  Loader2,
  MapPin,
  Star,
  ArrowRight,
  Activity
} from 'lucide-react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';

interface CallProgress {
  provider_name: string;
  status: 'pending' | 'calling' | 'completed' | 'failed';
  call_sid?: string;
  rating?: number;
  address?: string;
}

export default function BookingProgressPage() {
  const params = useParams();
  const router = useRouter();
  const bookingId = params.id as string;

  const [status, setStatus] = useState<'processing' | 'completed'>('processing');
  const [callsProgress, setCallsProgress] = useState<CallProgress[]>([]);
  const [completedCount, setCompletedCount] = useState(0);
  const [totalCalls, setTotalCalls] = useState(2);
  const [currentProvider, setCurrentProvider] = useState<string>('');

  useEffect(() => {
    const checkProgress = async () => {
      try {
        const response = await apiClient.getBookingStatus(bookingId);

        if (response.status === 'completed') {
          setStatus('completed');
          // Wait 2 seconds to show completion, then redirect
          setTimeout(() => {
            router.push(`/booking/${bookingId}`);
          }, 2000);
        } else if (response.status === 'processing') {
          // Simulate progress (in production this would come from backend)
          updateProgress();
        }
      } catch (error) {
        console.error('Error checking progress:', error);
      }
    };

    // Initial check
    checkProgress();

    // Poll every 500ms for smoother updates
    const interval = setInterval(checkProgress, 500);

    return () => clearInterval(interval);
  }, [bookingId, router]);

  const updateProgress = () => {
    // Simulate calls progressing
    setCompletedCount((prev) => {
      if (prev < totalCalls) {
        const next = prev + 1;

        // Update current provider being called
        const providers = [
          'Cambridge Dental Associates',
          'Harvard Square Dental'
        ];

        if (next <= providers.length) {
          setCurrentProvider(providers[next - 1]);
        }

        return next;
      }
      return prev;
    });
  };

  const progressPercent = (completedCount / totalCalls) * 100;

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="border-b border-black/10 bg-white sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Phone className="h-6 w-6 text-black" />
              <span className="text-xl font-bold text-black">CallPilot</span>
            </div>
            <Link href="/dashboard">
              <Button variant="outline" size="sm" className="border-black/10">
                Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {status === 'processing' ? (
          <div className="space-y-8">
            {/* Progress Header */}
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-black/5 mb-4">
                <Activity className="h-8 w-8 text-black animate-pulse" />
              </div>
              <h1 className="text-3xl font-bold mb-2 text-black">
                AI Agents Are Calling Providers
              </h1>
              <p className="text-lg text-black/60">
                Making {totalCalls} calls in parallel to find your best appointment options
              </p>
            </div>

            {/* Progress Bar */}
            <Card className="border-2 border-black/10">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Progress</span>
                  <span className="text-2xl font-bold">
                    {completedCount}/{totalCalls}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Progress bar */}
                  <div className="w-full bg-black/5 rounded-full h-4 overflow-hidden">
                    <div
                      className="bg-black h-full transition-all duration-300 ease-out"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>

                  {/* Current activity */}
                  {currentProvider && completedCount < totalCalls && (
                    <div className="flex items-center space-x-3 p-4 bg-black/5 rounded-lg">
                      <div className="flex-shrink-0">
                        <Loader2 className="h-5 w-5 text-black animate-spin" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-black">
                          Currently calling
                        </p>
                        <p className="text-base font-semibold text-black">
                          {currentProvider}
                        </p>
                      </div>
                      <Phone className="h-5 w-5 text-black/40" />
                    </div>
                  )}

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4 pt-4">
                    <div className="text-center p-3 bg-black/5 rounded-lg">
                      <div className="text-2xl font-bold text-black">
                        {completedCount}
                      </div>
                      <div className="text-xs text-black/60">Calls Made</div>
                    </div>
                    <div className="text-center p-3 bg-black/5 rounded-lg">
                      <div className="text-2xl font-bold text-black">
                        {totalCalls - completedCount}
                      </div>
                      <div className="text-xs text-black/60">Remaining</div>
                    </div>
                    <div className="text-center p-3 bg-black/5 rounded-lg">
                      <div className="text-2xl font-bold text-black">
                        ~{Math.ceil((totalCalls - completedCount) * 3)}s
                      </div>
                      <div className="text-xs text-black/60">Est. Time</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* How it works */}
            <Card className="border-2 border-black/10">
              <CardHeader>
                <CardTitle>What's Happening?</CardTitle>
                <CardDescription>
                  Behind the scenes, our AI agents are working for you
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-black text-white flex items-center justify-center text-sm font-bold">
                      1
                    </div>
                    <div>
                      <p className="font-medium text-black">Finding Providers</p>
                      <p className="text-sm text-black/60">
                        Searching for top-rated providers near your location
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-black text-white flex items-center justify-center text-sm font-bold">
                      2
                    </div>
                    <div>
                      <p className="font-medium text-black">Making Calls</p>
                      <p className="text-sm text-black/60">
                        AI voice agents calling each provider to check availability
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-black text-white flex items-center justify-center text-sm font-bold">
                      3
                    </div>
                    <div>
                      <p className="font-medium text-black">Ranking Results</p>
                      <p className="text-sm text-black/60">
                        Scoring options based on availability, rating, and distance
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Live activity feed */}
            <Card className="border-2 border-black/10">
              <CardHeader>
                <CardTitle>Call Activity</CardTitle>
                <CardDescription>Live updates from our AI agents</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {Array.from({ length: completedCount }).map((_, i) => {
                    const providers = [
                      'Cambridge Dental Associates',
                      'Harvard Square Dental',
                      'Central Square Smiles',
                      'Porter Dental Group',
                      'Kendall Dentistry',
                      'Fresh Pond Dental Care',
                      'MIT Dental Clinic',
                      'Inman Square Dental',
                      'Huron Village Dentistry',
                      'North Cambridge Dental',
                      'East Cambridge Dental',
                      'Riverside Dental Care',
                      'Cambridge Family Dentistry',
                      'Harvard Dental Center',
                      'Porter Square Dental'
                    ];

                    return (
                      <div
                        key={i}
                        className="flex items-center justify-between p-3 border border-black/10 rounded-lg animate-in fade-in slide-in-from-left-2"
                      >
                        <div className="flex items-center space-x-3">
                          <CheckCircle2 className="h-5 w-5 text-green-600" />
                          <div>
                            <p className="text-sm font-medium text-black">
                              {providers[i]}
                            </p>
                            <p className="text-xs text-black/50">
                              Call completed • {Math.floor(Math.random() * 45) + 15}s
                            </p>
                          </div>
                        </div>
                        <Star className="h-4 w-4 text-black/30" fill="currentColor" />
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-6">
              <CheckCircle2 className="h-10 w-10 text-green-600" />
            </div>
            <h1 className="text-3xl font-bold mb-3 text-black">
              All Calls Completed!
            </h1>
            <p className="text-lg text-black/60 mb-6">
              Redirecting you to results...
            </p>
            <Loader2 className="h-6 w-6 animate-spin mx-auto text-black/40" />
          </div>
        )}
      </div>
    </div>
  );
}
