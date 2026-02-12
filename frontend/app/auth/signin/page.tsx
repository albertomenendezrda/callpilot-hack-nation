'use client';

import { Suspense, useState } from 'react';
import { signIn } from 'next-auth/react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Phone } from 'lucide-react';

function SignInContent() {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') || '/dashboard';
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGoogleSignIn = () => {
    setError('');
    setLoading(true);
    signIn('google', { callbackUrl });
    setTimeout(() => setLoading(false), 3000);
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-2 border-black/10">
        <CardHeader className="text-center">
          <Link href="/" className="flex items-center justify-center gap-2 mb-2">
            <Phone className="h-8 w-8 text-black" />
            <span className="text-2xl font-bold text-black">CallPilot</span>
          </Link>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>
            Sign in with your Google account to access your dashboard and bookings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">
              {error}
            </p>
          )}

          <Button
            type="button"
            className="w-full bg-black text-white hover:bg-black/90"
            onClick={handleGoogleSignIn}
            disabled={loading}
          >
            {loading ? 'Redirecting...' : 'Continue with Google'}
          </Button>

          <p className="text-center text-sm text-black/50">
            <Link href="/" className="hover:text-black">
              Back to home
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white flex items-center justify-center p-4">
        <p className="text-black/60">Loading...</p>
      </div>
    }>
      <SignInContent />
    </Suspense>
  );
}
