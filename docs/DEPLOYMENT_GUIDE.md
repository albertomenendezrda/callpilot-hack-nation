# CallPilot - Deployment Guide

This guide covers deploying CallPilot to Google Cloud Platform (GCP) for production use.

## Architecture Overview

CallPilot uses the following GCP services:

- **Cloud Run**: Hosts the Flask backend API
- **Cloud Firestore**: Stores booking requests and user data
- **Secret Manager**: Securely stores API keys and credentials
- **Cloud Build**: Automated CI/CD pipeline
- **Firebase Hosting**: Hosts the Next.js frontend (optional)

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Terraform** installed (version 1.0+)
4. **API Keys** from ElevenLabs, Twilio, and Google

## Step 1: Set Up GCP Project

### Create a New Project

```bash
# Set your project ID
export PROJECT_ID="callpilot-prod"

# Create project
gcloud projects create $PROJECT_ID --name="CallPilot Production"

# Set as active project
gcloud config set project $PROJECT_ID

# Link billing account (replace with your billing account ID)
gcloud beta billing projects link $PROJECT_ID \
  --billing-account=YOUR_BILLING_ACCOUNT_ID
```

### Enable Required APIs

```bash
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  places-backend.googleapis.com \
  maps-backend.googleapis.com
```

## Step 2: Configure Terraform

### Initialize Terraform Variables

```bash
cd terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

Update `terraform.tfvars` with your actual values:

```hcl
project_id         = "callpilot-prod"
region             = "us-central1"
firestore_location = "us-central"

# Add your API keys
elevenlabs_api_key      = "your-actual-key"
google_calendar_api_key = "your-actual-key"
google_places_api_key   = "your-actual-key"
google_maps_api_key     = "your-actual-key"
twilio_account_sid      = "your-actual-sid"
twilio_auth_token       = "your-actual-token"
twilio_phone_number     = "+1234567890"
jwt_secret_key          = "generate-random-32-char-string"

# Update after deploying frontend
frontend_url = "https://your-frontend-url.web.app"
```

### Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply infrastructure
terraform apply
```

This creates:
- Firestore database
- Secret Manager secrets
- Service accounts with appropriate permissions

## Step 3: Deploy Backend to Cloud Run

### Option A: Using Deployment Script (Recommended)

```bash
# From project root
./scripts/deploy-backend.sh
```

### Option B: Manual Deployment

```bash
cd backend

# Build and submit to Cloud Build
gcloud builds submit --config cloudbuild.yaml

# The Cloud Build configuration automatically deploys to Cloud Run
```

### Verify Deployment

```bash
# Get the service URL
gcloud run services describe callpilot-backend \
  --region us-central1 \
  --format 'value(status.url)'

# Test health endpoint
curl https://your-backend-url/health
```

## Step 4: Deploy Frontend

### Option A: Firebase Hosting (Recommended)

```bash
cd frontend

# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase project
firebase init hosting

# Update .env.local with backend URL
echo "NEXT_PUBLIC_API_URL=https://your-backend-url" > .env.local

# Build and deploy
npm run build
firebase deploy --only hosting
```

### Option B: Vercel

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL production
```

### Option C: Cloud Run (Frontend as Container)

Create `frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

ENV PORT=3000
EXPOSE 3000

CMD ["npm", "start"]
```

Deploy:

```bash
cd frontend
gcloud builds submit --tag gcr.io/$PROJECT_ID/callpilot-frontend
gcloud run deploy callpilot-frontend \
  --image gcr.io/$PROJECT_ID/callpilot-frontend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

## Step 5: Configure CORS

Update backend CORS settings to allow your frontend domain:

```python
# In backend/app.py
CORS(app, origins=[
    "http://localhost:3000",
    "https://your-frontend-url.web.app",
    "https://your-custom-domain.com"
])
```

Redeploy backend:

```bash
./scripts/deploy-backend.sh
```

## Step 6: Set Up Custom Domain (Optional)

### Backend Domain

```bash
# Map custom domain to Cloud Run
gcloud run domain-mappings create \
  --service callpilot-backend \
  --domain api.callpilot.com \
  --region us-central1
```

### Frontend Domain (Firebase)

```bash
# Add custom domain in Firebase Console
firebase hosting:channel:deploy production
```

## Step 7: Set Up Monitoring

### Enable Cloud Logging

```bash
# View backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=callpilot-backend" \
  --limit 50 \
  --format json
```

### Set Up Alerts

Create alerting policies in GCP Console:
1. High error rate (> 5% errors)
2. High latency (> 2s response time)
3. Service downtime

## Step 8: Production Checklist

Before going live, verify:

- [ ] All API keys are stored in Secret Manager
- [ ] CORS is properly configured
- [ ] HTTPS is enabled on all endpoints
- [ ] Error logging is working
- [ ] Rate limiting is configured
- [ ] Firestore security rules are set
- [ ] Service accounts have minimum required permissions
- [ ] Monitoring and alerts are active
- [ ] Backup strategy is in place

## Environment Variables Summary

### Backend (Cloud Run)
- `GOOGLE_CLOUD_PROJECT` - Managed by Cloud Run
- API keys - Managed by Secret Manager

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL

## Cost Optimization

### Cloud Run
- Set min instances to 0 for low traffic
- Set max instances based on expected load
- Use appropriate instance class (F2 recommended)

### Firestore
- **One-time: create composite indexes** — After the first deploy using Firestore, create the required indexes so queries (e.g. Active tasks) don’t return “The query requires an index”. From the repo root run:
  ```bash
  ./scripts/create-firestore-indexes.sh
  ```
  Or use the link in the error message to create the index in the Firebase console. Index build can take a few minutes.
- Use document pagination for very large collections
- Archive old booking data if needed

### Cloud Build
- Cache Docker layers
- Use concurrent builds carefully

## Updating the Application

### Backend Updates

```bash
cd backend
git pull origin main
./scripts/deploy-backend.sh
```

### Frontend Updates

```bash
cd frontend
git pull origin main
npm run build
firebase deploy --only hosting
```

## Rollback Procedure

### Backend Rollback

```bash
# List revisions
gcloud run revisions list --service callpilot-backend --region us-central1

# Rollback to previous revision
gcloud run services update-traffic callpilot-backend \
  --region us-central1 \
  --to-revisions REVISION_NAME=100
```

### Frontend Rollback (Firebase)

```bash
firebase hosting:rollback
```

## Security Best Practices

1. **Never commit secrets** - Use Secret Manager
2. **Enable Cloud Armor** - DDoS protection
3. **Implement rate limiting** - Prevent abuse
4. **Use service accounts** - Least privilege principle
5. **Enable audit logging** - Track all changes
6. **Regular security scans** - Use Cloud Security Scanner

## Troubleshooting

### Backend Won't Deploy

Check Cloud Build logs:
```bash
gcloud builds log --region=us-central1 <BUILD_ID>
```

### Secret Manager Access Issues

Verify service account permissions:
```bash
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:callpilot-backend-sa@*"
```

### Frontend Can't Connect to Backend

1. Check CORS configuration
2. Verify NEXT_PUBLIC_API_URL is correct
3. Test backend endpoint directly
4. Check browser console for errors

## CI/CD Pipeline (Advanced)

Set up automated deployments with Cloud Build triggers:

```yaml
# cloudbuild.yaml at repo root
steps:
  # Backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/callpilot-backend', 'backend']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/callpilot-backend']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    args: ['run', 'deploy', 'callpilot-backend', '--image', 'gcr.io/$PROJECT_ID/callpilot-backend']

  # Frontend
  - name: 'node:18'
    dir: 'frontend'
    args: ['npm', 'install']
  - name: 'node:18'
    dir: 'frontend'
    args: ['npm', 'run', 'build']
```

## Support

For deployment issues:
1. Check GCP Console logs
2. Review Cloud Build history
3. Verify Secret Manager access
4. Contact support team

## Next Steps

- Set up CI/CD automation
- Configure domain and SSL
- Implement monitoring dashboards
- Plan scaling strategy
- Review security policies
