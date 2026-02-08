#!/bin/bash

# CallPilot Frontend Deployment Script
# Deploys frontend to Google Cloud Run

set -e

# Get the repository root directory (parent of scripts directory)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🎨 CallPilot Frontend Deployment"
echo "================================="
echo ""

# ============================================
# Prerequisites Check
# ============================================

echo "🔍 Checking prerequisites..."
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it from:"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current GCP project
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project is set. Run: gcloud config set project PROJECT_ID"
    exit 1
fi

echo "✅ All prerequisites met"
echo "📦 GCP Project: $PROJECT_ID"
echo ""

# ============================================
# Get Backend URL (optional)
# ============================================

# Try to get the backend URL from Cloud Run
BACKEND_URL=$(gcloud run services describe callpilot-backend \
    --region us-central1 \
    --format 'value(status.url)' 2>/dev/null || echo "")

if [ -n "$BACKEND_URL" ]; then
    echo "🔗 Found backend URL: $BACKEND_URL"
else
    echo "⚠️  Backend not found. Frontend will use URL from cloudbuild.yaml"
fi

echo ""

# ============================================
# Deployment Confirmation
# ============================================

read -p "🚦 Deploy frontend to Cloud Run? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""

# ============================================
# Frontend Deployment
# ============================================

echo "================================================"
echo "🎨 Deploying Frontend to Cloud Run"
echo "================================================"
echo ""

# Navigate to frontend directory
cd "$REPO_ROOT/frontend"

# Update cloudbuild.yaml with backend URL if available
if [ -n "$BACKEND_URL" ]; then
    echo "📝 Updating frontend Cloud Build config with backend URL..."
    sed -i.bak "s|NEXT_PUBLIC_API_URL=.*'|NEXT_PUBLIC_API_URL=$BACKEND_URL'|g" cloudbuild.yaml
    rm cloudbuild.yaml.bak
    echo "✅ Updated cloudbuild.yaml"
    echo ""
fi

echo "🔨 Building and deploying frontend..."
echo ""

# Submit build to Cloud Build
if gcloud builds submit --config cloudbuild.yaml; then
    echo ""
    echo "✅ Frontend deployed successfully!"
    echo ""

    # Get frontend service URL
    FRONTEND_URL=$(gcloud run services describe callpilot-frontend \
        --region us-central1 \
        --format 'value(status.url)' 2>/dev/null || echo "")

    if [ -n "$FRONTEND_URL" ]; then
        echo "🌐 Frontend URL: $FRONTEND_URL"
        echo ""
    fi
else
    echo ""
    echo "❌ Frontend deployment failed!"
    exit 1
fi

# ============================================
# Deployment Summary
# ============================================

echo ""
echo "================================================"
echo "🎉 DEPLOYMENT COMPLETE!"
echo "================================================"
echo ""
echo "✅ Frontend deployed to Cloud Run"
if [ -n "$FRONTEND_URL" ]; then
    echo "   URL: $FRONTEND_URL"
fi
echo ""
if [ -n "$BACKEND_URL" ]; then
    echo "✅ Connected to backend"
    echo "   URL: $BACKEND_URL"
    echo ""
fi
echo "🔗 Next steps:"
echo "   1. Test your application at $FRONTEND_URL"
echo "   2. Monitor logs: gcloud run logs read callpilot-frontend --region us-central1"
echo "   3. Check service status: gcloud run services describe callpilot-frontend --region us-central1"
echo ""
