#!/bin/bash
# Create Firestore composite indexes required by CallPilot (bookings and tasks queries).
# Run once per project. Index creation can take a few minutes; the app will work after they're built.
#
# Usage: ./scripts/create-firestore-indexes.sh [PROJECT_ID]
# If PROJECT_ID is omitted, uses: gcloud config get-value project

set -e

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null)}"
if [ -z "$PROJECT_ID" ]; then
  echo "Usage: ./scripts/create-firestore-indexes.sh [PROJECT_ID]"
  echo "Or set default project: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

echo "Creating Firestore composite indexes for project: $PROJECT_ID"
echo ""

# 1) Bookings: filter by user_id, order by created_at (Active tasks / dashboard)
echo "1/3  bookings: user_id + created_at"
gcloud firestore indexes composite create \
  --project="$PROJECT_ID" \
  --database="(default)" \
  --collection-group=bookings \
  --field-config=field-path=user_id,order=ascending \
  --field-config=field-path=created_at,order=descending \
  --quiet || true

# 2) Bookings: filter by status, order by created_at (webhook lookup)
echo "2/3  bookings: status + created_at"
gcloud firestore indexes composite create \
  --project="$PROJECT_ID" \
  --database="(default)" \
  --collection-group=bookings \
  --field-config=field-path=status,order=ascending \
  --field-config=field-path=created_at,order=descending \
  --quiet || true

# 3) Tasks: filter by user_id, order by updated_at (dashboard tasks list)
echo "3/3  tasks: user_id + updated_at"
gcloud firestore indexes composite create \
  --project="$PROJECT_ID" \
  --database="(default)" \
  --collection-group=tasks \
  --field-config=field-path=user_id,order=ascending \
  --field-config=field-path=updated_at,order=descending \
  --quiet || true

echo ""
echo "Done. Indexes may take a few minutes to finish building."
echo "Check status: https://console.cloud.google.com/firestore/indexes?project=$PROJECT_ID"
