'use client';

import { useEffect } from 'react';
import { apiClient, getAuthToken } from '@/lib/api-client';

/**
 * Ensures the API client sends the auth token with backend requests.
 * Mount this inside SessionProvider so it runs after auth is available.
 */
export function AuthApiProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    apiClient.setAuthTokenGetter(getAuthToken);
  }, []);
  return <>{children}</>;
}
