#!/bin/bash

# CallPilot Frontend Deployment Script
# Deploys the Next.js frontend to Firebase Hosting

set -e

echo "🚀 Deploying CallPilot Frontend to Firebase"
echo "==========================================="
echo ""

# Check if firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "❌ Firebase CLI is not installed."
    echo "Install it with: npm install -g firebase-tools"
    exit 1
fi

# Navigate to frontend directory
cd "$(dirname "$0")/../frontend"

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "❌ .env.local file not found. Please create it with:"
    echo "NEXT_PUBLIC_API_URL=https://your-backend-url"
    exit 1
fi

echo "📦 Building frontend..."
echo ""

# Build the application
npm run build

echo ""
echo "🚀 Deploying to Firebase..."
echo ""

# Deploy to Firebase
firebase deploy --only hosting

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Your frontend is now live!"
