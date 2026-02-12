import { getToken } from 'next-auth/jwt';
import { NextRequest, NextResponse } from 'next/server';
import { SignJWT } from 'jose';

/**
 * Returns a plain HS256-signed JWT for use when calling the backend.
 *
 * NextAuth session cookies are encrypted (JWE) and can't be verified by the
 * Python backend with plain PyJWT.  Instead, we decode the session here and
 * create a lightweight HS256 JWT containing sub + email that the backend
 * can verify with the same NEXTAUTH_SECRET.
 */
export async function GET(request: NextRequest) {
  const secret = process.env.NEXTAUTH_SECRET;
  if (!secret) {
    return NextResponse.json({ error: 'Server misconfigured (no secret)' }, { status: 500 });
  }

  const decoded = await getToken({
    req: request,
    secret,
    secureCookie: process.env.NODE_ENV === 'production',
  });

  if (!decoded) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Create a plain HS256 JWT the Python backend can verify with jwt.decode()
  const key = new TextEncoder().encode(secret);
  const token = await new SignJWT({
    sub: decoded.sub,
    email: decoded.email,
  })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('1h')
    .sign(key);

  return NextResponse.json({ token });
}
