#!/bin/bash
# Push auth env vars from frontend/.env.local to BOTH Cloud Run frontend and backend.
# Both must use the same NEXTAUTH_SECRET: frontend signs the JWT, backend verifies it.
# Run this when the dashboard shows "Session could not be verified" on the cloud,
# or after any deploy that may have wiped env vars.
#
# Usage: ./scripts/set-backend-auth-secret.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$REPO_ROOT/frontend/.env.local"
REGION="${CLOUD_RUN_REGION:-us-central1}"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE. Add NEXTAUTH_SECRET there first."
  exit 1
fi

# Load vars from frontend/.env.local
set -a
# shellcheck source=/dev/null
source "$ENV_FILE" 2>/dev/null || true
set +a

if [ -z "${NEXTAUTH_SECRET}" ]; then
  echo "NEXTAUTH_SECRET is not set in frontend/.env.local."
  echo "Generate one with: openssl rand -base64 32"
  exit 1
fi

# Strip surrounding quotes (bash source keeps them for values like "foo")
NEXTAUTH_SECRET="${NEXTAUTH_SECRET%\"}"
NEXTAUTH_SECRET="${NEXTAUTH_SECRET#\"}"

echo "Region: $REGION"
echo ""

# --- Backend: only needs NEXTAUTH_SECRET ---
echo "1/2  Setting NEXTAUTH_SECRET on callpilot-backend..."
if gcloud run services update callpilot-backend --region "$REGION" \
  --update-env-vars "NEXTAUTH_SECRET=$NEXTAUTH_SECRET" --quiet; then
  echo "     Backend updated."
else
  echo "     Backend update FAILED. Check gcloud auth and project."
  exit 1
fi

# --- Frontend: needs NEXTAUTH_SECRET + NEXTAUTH_URL + Google OAuth ---
# Get the actual frontend URL for NEXTAUTH_URL
FRONTEND_URL=$(gcloud run services describe callpilot-frontend \
  --region "$REGION" --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$FRONTEND_URL" ]; then
  echo ""
  echo "Could not detect frontend URL. Set NEXTAUTH_URL manually if sign-in fails."
  FRONTEND_URL="${NEXTAUTH_URL:-https://placeholder.run.app}"
fi

echo ""
echo "2/2  Setting auth env vars on callpilot-frontend..."
echo "     NEXTAUTH_URL=$FRONTEND_URL"

FRONTEND_VARS="NEXTAUTH_SECRET=$NEXTAUTH_SECRET,NEXTAUTH_URL=$FRONTEND_URL"
[ -n "${GOOGLE_CLIENT_ID}" ]     && FRONTEND_VARS="$FRONTEND_VARS,GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID"
[ -n "${GOOGLE_CLIENT_SECRET}" ] && FRONTEND_VARS="$FRONTEND_VARS,GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET"

if gcloud run services update callpilot-frontend --region "$REGION" \
  --update-env-vars "$FRONTEND_VARS" --quiet; then
  echo "     Frontend updated."
else
  echo "     Frontend update FAILED."
  exit 1
fi

echo ""
echo "Done. Both services now have NEXTAUTH_SECRET and the frontend has NEXTAUTH_URL=$FRONTEND_URL."
echo ""
echo "IMPORTANT: Sign out and sign in again on the app so a new session JWT is created."
