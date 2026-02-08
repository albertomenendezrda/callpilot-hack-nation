#!/bin/bash

# CallPilot Full Deployment Script
# Deploys both backend (Cloud Run) and frontend (Firebase)

set -e

echo "🚀 CallPilot Full Stack Deployment"
echo "===================================="
echo ""
echo "This will deploy:"
echo "  - Backend to Google Cloud Run"
echo "  - Frontend to Firebase Hosting"
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

# Check if firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "❌ Firebase CLI is not installed."
    echo "Install it with: npm install -g firebase-tools"
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
# Deployment Confirmation
# ============================================

read -p "🚦 Deploy full stack to production? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""

# ============================================
# Backend Deployment
# ============================================

echo "================================================"
echo "📡 STEP 1/2: Deploying Backend to Cloud Run"
echo "================================================"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/../backend"

echo "🔨 Building and deploying backend..."
echo ""

# Submit build to Cloud Build
if gcloud builds submit --config cloudbuild.yaml; then
    echo ""
    echo "✅ Backend deployed successfully!"
    echo ""

    # Get service URL
    BACKEND_URL=$(gcloud run services describe callpilot-backend \
        --region us-central1 \
        --format 'value(status.url)' 2>/dev/null || echo "")

    if [ -n "$BACKEND_URL" ]; then
        echo "🌐 Backend URL: $BACKEND_URL"
        echo ""

        # Update frontend .env.local with backend URL
        cd "$(dirname "$0")/../frontend"

        if [ -f ".env.local" ]; then
            # Backup existing .env.local
            cp .env.local .env.local.backup

            # Update NEXT_PUBLIC_API_URL
            if grep -q "NEXT_PUBLIC_API_URL" .env.local; then
                sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=$BACKEND_URL|" .env.local
                rm .env.local.bak
                echo "✅ Updated frontend .env.local with backend URL"
            else
                echo "NEXT_PUBLIC_API_URL=$BACKEND_URL" >> .env.local
                echo "✅ Added backend URL to frontend .env.local"
            fi
        else
            echo "NEXT_PUBLIC_API_URL=$BACKEND_URL" > .env.local
            echo "✅ Created frontend .env.local with backend URL"
        fi
    fi
else
    echo ""
    echo "❌ Backend deployment failed!"
    exit 1
fi

echo ""

# ============================================
# Frontend Deployment
# ============================================

echo "================================================"
echo "🎨 STEP 2/2: Deploying Frontend to Firebase"
echo "================================================"
echo ""

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
if npm run build; then
    echo ""
    echo "✅ Frontend built successfully!"
    echo ""
else
    echo ""
    echo "❌ Frontend build failed!"
    exit 1
fi

echo "🚀 Deploying to Firebase..."
echo ""

# Deploy to Firebase
if firebase deploy --only hosting; then
    echo ""
    echo "✅ Frontend deployed successfully!"
    echo ""
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
echo "✅ Backend deployed to Cloud Run"
if [ -n "$BACKEND_URL" ]; then
    echo "   URL: $BACKEND_URL"
    echo "   Test: curl $BACKEND_URL/health"
fi
echo ""
echo "✅ Frontend deployed to Firebase Hosting"
echo ""
echo "🔗 Next steps:"
echo "   1. Test your application"
echo "   2. Monitor logs in GCP Console and Firebase Console"
echo "   3. Configure any environment-specific settings"
echo ""
