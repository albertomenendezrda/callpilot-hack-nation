#!/bin/bash

# CallPilot Full Deployment Script
# Deploys infrastructure and applications

set -e

# Get the repository root directory (parent of scripts directory)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🚀 CallPilot Full Stack Deployment"
echo "===================================="
echo ""
echo "This will deploy:"
echo "  - Infrastructure (Terraform)"
echo "  - Backend to Google Cloud Run"
echo "  - Frontend to Google Cloud Run"
echo ""

# ============================================
# Prerequisites Check
# ============================================

echo "🔍 Checking prerequisites..."
echo ""

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install it from:"
    echo "https://www.terraform.io/downloads"
    exit 1
fi

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
# Infrastructure Deployment
# ============================================

echo "================================================"
echo "🏗️  STEP 1/3: Deploying Infrastructure (Terraform)"
echo "================================================"
echo ""

# Navigate to terraform directory
cd "$REPO_ROOT/terraform"

echo "🔧 Initializing Terraform..."
echo ""

# Initialize Terraform (safe to run multiple times)
terraform init

echo ""
echo "📋 Planning infrastructure changes..."
echo ""

# Run terraform plan
terraform plan -out=tfplan

echo ""
read -p "🚦 Apply these infrastructure changes? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Infrastructure deployment cancelled"
    rm -f tfplan
    exit 0
fi

echo ""
echo "🔨 Applying infrastructure changes..."
echo ""

# Apply the plan
if terraform apply tfplan; then
    echo ""
    echo "✅ Infrastructure deployed successfully!"
    echo ""
    rm -f tfplan
else
    echo ""
    echo "❌ Infrastructure deployment failed!"
    rm -f tfplan
    exit 1
fi

echo ""

# ============================================
# Backend Deployment
# ============================================

echo "================================================"
echo "📡 STEP 2/3: Deploying Backend to Cloud Run"
echo "================================================"
echo ""

# Navigate to backend directory
cd "$REPO_ROOT/backend"

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
        cd "$REPO_ROOT/frontend"

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
echo "🎨 STEP 3/3: Deploying Frontend to Cloud Run"
echo "================================================"
echo ""

# Navigate to frontend directory
cd "$REPO_ROOT/frontend"

# Update cloudbuild.yaml with backend URL if available
if [ -n "$BACKEND_URL" ]; then
    echo "📝 Updating frontend Cloud Build config with backend URL..."
    sed -i.bak "s|NEXT_PUBLIC_API_URL=.*'|NEXT_PUBLIC_API_URL=$BACKEND_URL'|g" cloudbuild.yaml
    rm cloudbuild.yaml.bak
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
echo "✅ Infrastructure deployed (Terraform)"
echo "   - Secret Manager secrets configured"
echo "   - IAM permissions configured"
echo "   - Cloud Run services configured"
echo ""
echo "✅ Backend deployed to Cloud Run"
if [ -n "$BACKEND_URL" ]; then
    echo "   URL: $BACKEND_URL"
    echo "   Test: curl $BACKEND_URL/health"
fi
echo ""
echo "✅ Frontend deployed to Cloud Run"
if [ -n "$FRONTEND_URL" ]; then
    echo "   URL: $FRONTEND_URL"
fi
echo ""
echo "🔗 Next steps:"
echo "   1. Test your application at $FRONTEND_URL"
echo "   2. Monitor logs in GCP Console"
echo "   3. Verify secrets in Secret Manager"
echo "   4. Check Cloud Run service configurations"
echo ""
