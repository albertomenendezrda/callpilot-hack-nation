import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

const PROTECTED_PREFIXES = ['/dashboard', '/booking', '/book'];

function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PREFIXES.some((prefix) =>
    pathname === prefix || pathname.startsWith(prefix + '/')
  );
}

/**
 * Protect dashboard and booking routes. Unauthenticated users are redirected to sign-in.
 * Requires NEXTAUTH_SECRET to be set so the JWT can be read.
 */
export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  if (!isProtectedPath(pathname)) {
    return NextResponse.next();
  }

  // NEXTAUTH_SECRET must be set or we cannot verify the session; treat as unauthenticated
  const secret = process.env.NEXTAUTH_SECRET;
  const token = secret
    ? await getToken({
        req: request,
        secret,
        secureCookie: process.env.NODE_ENV === 'production',
      })
    : null;

  if (!token) {
    // In waitlist mode (dev/gated), send unauthenticated users to waitlist instead of sign-in
    const useWaitlist = process.env.NEXT_PUBLIC_WAITLIST_MODE === 'true';
    const signInUrl = new URL(useWaitlist ? '/waitlist' : '/auth/signin', request.url);
    if (!useWaitlist) signInUrl.searchParams.set('callbackUrl', pathname + request.nextUrl.search);
    return NextResponse.redirect(signInUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/booking/:path*',
    '/book',
  ],
};
