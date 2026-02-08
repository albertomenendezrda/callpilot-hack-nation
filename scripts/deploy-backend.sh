#!/bin/bash

# CallPilot Backend Deployment Script
# Deploys the Flask backend to Google Cloud Run

set -e

echo "🚀 Deploying CallPilot Backend to Cloud Run"
echo "============================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it from:"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project is set. Run: gcloud config set project PROJECT_ID"
    exit 1
fi

echo "📦 Project: $PROJECT_ID"
echo ""

# Ask for confirmation
read -p "Deploy backend to $PROJECT_ID? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "🔨 Building and deploying..."
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/../backend"

# Submit build to Cloud Build
gcloud builds submit --config cloudbuild.yaml

echo ""
echo "✅ Deployment complete!"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe callpilot-backend \
    --region us-central1 \
    --format 'value(status.url)')

echo "🌐 Backend URL: $SERVICE_URL"
echo ""
echo "Test the health endpoint:"
echo "curl $SERVICE_URL/health"
echo ""
echo "⚠️  Don't forget to update NEXT_PUBLIC_API_URL in frontend/.env.local"
