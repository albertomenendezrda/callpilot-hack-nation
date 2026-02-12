#!/bin/bash

# CallPilot Full Deployment Script
# Deploys infrastructure and applications
#
# Usage: ./deploy-all.sh [--yes|-y]
#   --yes, -y   Skip all confirmation prompts (non-interactive/CI)

set -e

# Parse --yes / -y flag
AUTO_APPROVE=false
for arg in "$@"; do
  case "$arg" in
    --yes|-y) AUTO_APPROVE=true; shift ;;
  esac
done

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

if [ "$AUTO_APPROVE" != "true" ]; then
  read -p "🚦 Deploy full stack to production? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
  fi
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

if [ "$AUTO_APPROVE" != "true" ]; then
  echo ""
  read -p "🚦 Apply these infrastructure changes? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Infrastructure deployment cancelled"
    rm -f tfplan
    exit 0
  fi
fi

echo ""
echo "🔨 Applying infrastructure changes..."
echo ""

# Apply the plan
if terraform apply -input=false tfplan; then
    echo ""
    echo '✅ Infrastructure deployed successfully!'
    echo ""
    rm -f tfplan
else
    echo ""
    echo '❌ Infrastructure deployment failed!'
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
    echo '✅ Backend deployed successfully!'
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

        # Backend must have the same NEXTAUTH_SECRET to verify JWTs; push from frontend/.env.local
        if [ -f ".env.local" ]; then
            set -a
            # shellcheck source=/dev/null
            source .env.local 2>/dev/null || true
            set +a
        fi

        # Also read backend/.env for backend-specific vars (waitlist, Resend, admin, etc.)
        if [ -f "$REPO_ROOT/backend/.env" ]; then
            set -a
            # shellcheck source=/dev/null
            source "$REPO_ROOT/backend/.env" 2>/dev/null || true
            set +a
        fi

        BACKEND_ENV_VARS=""
        [ -n "${NEXTAUTH_SECRET}" ]  && BACKEND_ENV_VARS="NEXTAUTH_SECRET=$NEXTAUTH_SECRET"
        [ -n "${WAITLIST_MODE}" ]    && BACKEND_ENV_VARS="${BACKEND_ENV_VARS:+$BACKEND_ENV_VARS,}WAITLIST_MODE=$WAITLIST_MODE"
        [ -n "${ADMIN_SECRET}" ]     && BACKEND_ENV_VARS="${BACKEND_ENV_VARS:+$BACKEND_ENV_VARS,}ADMIN_SECRET=$ADMIN_SECRET"
        [ -n "${RESEND_API_KEY}" ]   && BACKEND_ENV_VARS="${BACKEND_ENV_VARS:+$BACKEND_ENV_VARS,}RESEND_API_KEY=$RESEND_API_KEY"
        [ -n "${WAITLIST_FROM_EMAIL}" ] && BACKEND_ENV_VARS="${BACKEND_ENV_VARS:+$BACKEND_ENV_VARS,}WAITLIST_FROM_EMAIL=$WAITLIST_FROM_EMAIL"

        if [ -n "$BACKEND_ENV_VARS" ]; then
            echo "🔐 Pushing env vars to backend (auth + waitlist)..."
            if gcloud run services update callpilot-backend --region us-central1 --update-env-vars "$BACKEND_ENV_VARS" --quiet; then
                echo "✅ Backend env vars updated"
            else
                echo "⚠️  Failed to update backend env vars. Run manually:"
                echo "    gcloud run services update callpilot-backend --region us-central1 --update-env-vars \"$BACKEND_ENV_VARS\""
            fi
        else
            echo "⚠️  Add NEXTAUTH_SECRET to frontend/.env.local and re-run deploy so the backend can verify logins"
        fi
    fi
else
    echo ""
    echo '❌ Backend deployment failed!'
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
    echo '✅ Frontend deployed successfully!'
    echo ""

    # Get frontend service URL
    FRONTEND_URL=$(gcloud run services describe callpilot-frontend \
        --region us-central1 \
        --format 'value(status.url)' 2>/dev/null || echo "")

    if [ -n "$FRONTEND_URL" ]; then
        echo "🌐 Frontend URL: $FRONTEND_URL"
        echo ""

        # Load auth vars from frontend/.env.local so we can push them to Cloud Run (no need to export)
        if [ -f ".env.local" ]; then
            set -a
            # shellcheck source=/dev/null
            source .env.local 2>/dev/null || true
            set +a
        fi

        # Set auth env vars on Cloud Run so Google sign-in works (NEXTAUTH_URL must match frontend URL)
        echo "🔐 Updating frontend auth env vars (NEXTAUTH_URL=$FRONTEND_URL)..."
        FRONTEND_ENV_VARS="NEXT_PUBLIC_API_URL=$BACKEND_URL,NEXTAUTH_URL=$FRONTEND_URL"
        [ -n "${NEXTAUTH_SECRET}" ]            && FRONTEND_ENV_VARS="$FRONTEND_ENV_VARS,NEXTAUTH_SECRET=$NEXTAUTH_SECRET"
        [ -n "${GOOGLE_CLIENT_ID}" ]           && FRONTEND_ENV_VARS="$FRONTEND_ENV_VARS,GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID"
        [ -n "${GOOGLE_CLIENT_SECRET}" ]       && FRONTEND_ENV_VARS="$FRONTEND_ENV_VARS,GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET"
        [ -n "${NEXT_PUBLIC_WAITLIST_MODE}" ]   && FRONTEND_ENV_VARS="$FRONTEND_ENV_VARS,NEXT_PUBLIC_WAITLIST_MODE=$NEXT_PUBLIC_WAITLIST_MODE"
        if gcloud run services update callpilot-frontend --region us-central1 --update-env-vars "$FRONTEND_ENV_VARS" --quiet; then
            echo "✅ Frontend env vars updated"
        else
            echo "⚠️  Could not update frontend env vars. Run manually:"
            echo "    gcloud run services update callpilot-frontend --region us-central1 --update-env-vars \"$FRONTEND_ENV_VARS\""
        fi
        if [ -z "${NEXTAUTH_SECRET}" ] || [ -z "${GOOGLE_CLIENT_ID}" ] || [ -z "${GOOGLE_CLIENT_SECRET}" ]; then
            echo ""
            echo "⚠️  Google sign-in will not work until the frontend service has:"
            echo "    NEXTAUTH_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET"
            echo "    Add them to frontend/.env.local and re-run this script, or run the gcloud command below."
            echo "    In Google Cloud Console → APIs & Credentials → your OAuth client, add redirect URI:"
            echo "    $FRONTEND_URL/api/auth/callback/google"
            echo ""
        fi
    fi
else
    echo ""
    echo '❌ Frontend deployment failed!'
    exit 1
fi

# ============================================
# Deployment Summary
# ============================================

echo ""
echo "================================================"
echo '🎉 DEPLOYMENT COMPLETE!'
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
