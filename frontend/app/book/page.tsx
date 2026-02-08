'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function BookPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to voice AI immediately
    router.replace('/dashboard/chat');
  }, [router]);

  return (
    <div className="min-h-screen bg-white flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-black" />
        <p className="text-black/60">Redirecting to AI Chat...</p>
      </div>
    </div>
  );
}
