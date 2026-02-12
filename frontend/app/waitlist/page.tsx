'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Phone } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export default function WaitlistPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/waitlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), email: email.trim() }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError((data as { error?: string }).error || 'Something went wrong');
        setLoading(false);
        return;
      }
      setDone(true);
    } catch {
      setError('Could not reach the server. Try again later.');
    }
    setLoading(false);
  };

  if (done) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-2 border-black/10">
          <CardHeader className="text-center">
            <Link href="/" className="flex items-center justify-center gap-2 mb-2">
              <Phone className="h-8 w-8 text-black" />
              <span className="text-2xl font-bold text-black">CallPilot</span>
            </Link>
            <CardTitle>You're on the list</CardTitle>
            <CardDescription>
              We've received your signup. Check your email for confirmation. We'll add you to the user pool soon.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Link href="/">
              <Button variant="outline" className="w-full border-black/10">
                Back to home
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-2 border-black/10">
        <CardHeader className="text-center">
          <Link href="/" className="flex items-center justify-center gap-2 mb-2">
            <Phone className="h-8 w-8 text-black" />
            <span className="text-2xl font-bold text-black">CallPilot</span>
          </Link>
          <CardTitle>Join the waitlist</CardTitle>
          <CardDescription>
            Enter your name and email. We'll send a confirmation and add you to the user pool when ready.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">
              {error}
            </p>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            <Input
              type="text"
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="border-black/10"
            />
            <Input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="border-black/10"
            />
            <Button
              type="submit"
              className="w-full bg-black text-white hover:bg-black/90"
              disabled={loading}
            >
              {loading ? 'Submitting...' : 'Join waitlist'}
            </Button>
          </form>

          <p className="text-center text-sm text-black/50">
            Already have access?{' '}
            <Link href="/auth/signin" className="font-medium text-black hover:underline">
              Sign in with Google
            </Link>
          </p>

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
