'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ArrowLeft,
  MapPin,
  Star,
  Clock,
  Phone,
  CheckCircle2,
  Loader2,
  Calendar,
  Navigation,
} from 'lucide-react';
import Link from 'next/link';
import { apiClient, BookingStatus, BookingResult } from '@/lib/api-client';

export default function BookingClient({ id }: { id: string }) {
  const router = useRouter();
  const bookingId = id;

  const [status, setStatus] = useState<BookingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (!bookingId) return;

    // Poll for booking status
    const pollStatus = async () => {
      try {
        await apiClient.pollBookingStatus(
          bookingId,
          (updatedStatus) => {
            setStatus(updatedStatus);
            setLoading(false);
          },
          120000 // 2 minute timeout
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get booking status');
        setLoading(false);
      }
    };

    pollStatus();
  }, [bookingId]);

  const handleConfirm = async (providerId: string) => {
    setConfirming(true);
    try {
      const confirmation = await apiClient.confirmBooking(bookingId, providerId);
      // Redirect to success page
      router.push(`/booking/${bookingId}/success`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to confirm booking');
      setConfirming(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-16 w-16 animate-spin mx-auto mb-4 text-black" />
          <h2 className="text-2xl font-bold text-black mb-2">Calling Providers...</h2>
          <p className="text-black/60">
            Our AI agents are calling multiple providers simultaneously
          </p>
          <p className="text-sm text-black/50 mt-4">This usually takes 30-60 seconds</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">😞</div>
          <h2 className="text-2xl font-bold text-black mb-2">Something went wrong</h2>
          <p className="text-black/60 mb-6">{error}</p>
          <Link href="/book">
            <Button className="bg-black text-white hover:bg-black/90">Try Again</Button>
          </Link>
        </div>
      </div>
    );
  }

  if (status?.status === 'failed') {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">😔</div>
          <h2 className="text-2xl font-bold text-black mb-2">No Appointments Available</h2>
          <p className="text-black/60 mb-6">
            We couldn't find any available appointments matching your criteria. Try adjusting your
            search.
          </p>
          <Link href="/book">
            <Button className="bg-black text-white hover:bg-black/90">Search Again</Button>
          </Link>
        </div>
      </div>
    );
  }

  const results = status?.results || [];

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <nav className="border-b border-black/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Link href="/book">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              New Search
            </Button>
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-black text-white mb-4">
            <CheckCircle2 className="h-8 w-8" />
          </div>
          <h1 className="text-4xl font-bold mb-4 text-black">
            Found {results.length} Available Appointments
          </h1>
          <p className="text-lg text-black/60">
            Ranked by earliest availability, ratings, and distance
          </p>
        </div>

        {/* Results */}
        <div className="space-y-4">
          {results.map((result, index) => (
            <Card
              key={result.provider_id}
              className={`border-2 transition-all hover:shadow-lg ${
                index === 0
                  ? 'border-black bg-black/5'
                  : 'border-black/10 hover:border-black/30'
              }`}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      {index === 0 && (
                        <span className="px-2 py-1 bg-black text-white text-xs font-bold rounded">
                          BEST MATCH
                        </span>
                      )}
                      <span className="text-sm text-black/60">Rank #{index + 1}</span>
                    </div>
                    <CardTitle className="text-2xl">{result.provider_name}</CardTitle>
                    <CardDescription className="flex items-center mt-2 space-x-4 text-base">
                      <span className="flex items-center">
                        <Star className="h-4 w-4 mr-1 fill-black" />
                        {result.rating.toFixed(1)} rating
                      </span>
                      <span className="flex items-center">
                        <MapPin className="h-4 w-4 mr-1" />
                        {result.distance.toFixed(1)} mi
                      </span>
                      <span className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {result.travel_time} min
                      </span>
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-black">{result.score}</div>
                    <div className="text-xs text-black/60">match score</div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Address */}
                  <div>
                    <p className="text-sm font-medium text-black mb-1">Address</p>
                    <p className="text-black/70">{result.address}</p>
                  </div>

                  {/* Availability */}
                  <div>
                    <p className="text-sm font-medium text-black mb-1">
                      Earliest Availability
                    </p>
                    <div className="flex items-center space-x-4">
                      <span className="flex items-center text-black/70">
                        <Calendar className="h-4 w-4 mr-2" />
                        {result.availability_date}
                      </span>
                      <span className="flex items-center text-black/70">
                        <Clock className="h-4 w-4 mr-2" />
                        {result.availability_time}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-3 pt-4">
                    <Button
                      className="flex-1 bg-black text-white hover:bg-black/90"
                      onClick={() => handleConfirm(result.provider_id)}
                      disabled={confirming}
                    >
                      {confirming ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Booking...
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="mr-2 h-4 w-4" />
                          Book This Appointment
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      className="border-2 border-black/10 hover:border-black/30"
                      asChild
                    >
                      <a href={`tel:${result.phone}`}>
                        <Phone className="mr-2 h-4 w-4" />
                        Call Direct
                      </a>
                    </Button>
                    <Button
                      variant="outline"
                      className="border-2 border-black/10 hover:border-black/30"
                      asChild
                    >
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(result.address)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Navigation className="h-4 w-4" />
                      </a>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* No Results */}
        {results.length === 0 && status?.status === 'completed' && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-2xl font-bold text-black mb-2">No results yet</h3>
            <p className="text-black/60">
              Still searching for available appointments...
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
