"""
Verify NextAuth JWT from Authorization: Bearer <token> and return user_id (sub claim).
Used to protect API routes and scope data by user.
When WAITLIST_MODE=true, only emails in the allowed_emails table can access protected routes.
"""

import os
import jwt
from functools import wraps
from flask import request, jsonify

# NextAuth signs JWTs with NEXTAUTH_SECRET; backend must use the same to verify.
SECRET = os.getenv('NEXTAUTH_SECRET', '')
WAITLIST_MODE = os.getenv('WAITLIST_MODE', '').lower() in ('1', 'true', 'yes')


def _decode_request_token():
    """Return (user_id, email) from Bearer token or (None, None)."""
    if not SECRET:
        return None, None
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return None, None
    token = auth[7:].strip()
    if not token:
        return None, None
    try:
        payload = jwt.decode(token, SECRET, algorithms=['HS256'])
        return payload.get('sub'), (payload.get('email') or '').strip().lower() or None
    except Exception as e:
        print(f"[auth] JWT decode failed: {e}")
        # Common cause: token is a NextAuth JWE (encrypted), not a plain JWT.
        # The frontend /api/auth/token endpoint should return a plain HS256 JWT.
        parts = token.split('.')
        if len(parts) == 5:
            print("[auth] Token has 5 parts — looks like an encrypted JWE, not a signed JWT.")
            print("[auth] Make sure the frontend /api/auth/token creates a plain HS256 JWT.")
        return None, None


def get_user_id_from_request():
    """
    Read Authorization: Bearer <token>, verify JWT with NEXTAUTH_SECRET, return sub as user_id.
    Returns None if no token, invalid token, or NEXTAUTH_SECRET not set.
    """
    user_id, _ = _decode_request_token()
    return user_id


def require_auth(f):
    """Decorator: require valid JWT; inject user_id as first arg. When WAITLIST_MODE, also require email in allowed_emails."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        user_id, email = _decode_request_token()
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        if WAITLIST_MODE and email:
            import database as db
            if not db.is_email_allowed(email):
                return jsonify({'error': 'Unauthorized', 'code': 'waitlist'}), 403
        return f(user_id, *args, **kwargs)
    return wrapped
