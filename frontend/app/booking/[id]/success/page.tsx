'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle2, Calendar, Home, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function SuccessPage() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="max-w-2xl w-full">
        <Card className="border-2 border-black/10 text-center">
          <CardContent className="pt-12 pb-12">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-black text-white mb-6">
              <CheckCircle2 className="h-10 w-10" />
            </div>

            <h1 className="text-4xl font-bold text-black mb-4">Booking Confirmed!</h1>

            <p className="text-xl text-black/70 mb-8">
              Your appointment has been successfully booked. You'll receive a confirmation email
              shortly.
            </p>

            <div className="bg-black/5 rounded-lg p-6 mb-8">
              <h3 className="font-semibold text-black mb-4">What's Next?</h3>
              <div className="space-y-3 text-left">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-black text-white flex items-center justify-center text-sm font-bold">
                    1
                  </div>
                  <p className="text-black/70">
                    Check your email for appointment confirmation and details
                  </p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-black text-white flex items-center justify-center text-sm font-bold">
                    2
                  </div>
                  <p className="text-black/70">
                    The appointment has been added to your calendar
                  </p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-black text-white flex items-center justify-center text-sm font-bold">
                    3
                  </div>
                  <p className="text-black/70">
                    You'll receive a reminder 24 hours before your appointment
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/">
                <Button size="lg" className="bg-black text-white hover:bg-black/90">
                  <Home className="mr-2 h-5 w-5" />
                  Back to Home
                </Button>
              </Link>
              <Link href="/book">
                <Button
                  size="lg"
                  variant="outline"
                  className="border-2 border-black/10 hover:border-black/30"
                >
                  Book Another
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            </div>

            <div className="mt-8 pt-8 border-t border-black/10">
              <p className="text-sm text-black/60">
                Need to reschedule or cancel?
                <br />
                Contact us at{' '}
                <a href="mailto:support@callpilot.com" className="text-black underline">
                  support@callpilot.com
                </a>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
