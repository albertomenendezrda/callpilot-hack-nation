#!/bin/bash

# CallPilot - Setup Script
# This script helps set up the development environment

set -e

echo "🚀 CallPilot - Setup Script"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "⚠️  gcloud CLI is not installed. Install it from: https://cloud.google.com/sdk/docs/install"
    echo "You can continue for local development, but you won't be able to deploy to GCP."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Prerequisites check passed"
echo ""

# Backend setup
echo "📦 Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your API credentials"
fi

cd ..

echo "✅ Backend setup complete"
echo ""

# Frontend setup
echo "📦 Setting up frontend..."
cd frontend

# Install dependencies
echo "Installing Node dependencies..."
npm install --silent

# Create .env.local file if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local file from template..."
    cp .env.local.example .env.local
    echo "⚠️  Please edit frontend/.env.local with your API URL"
fi

cd ..

echo "✅ Frontend setup complete"
echo ""

# Summary
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit backend/.env with your API credentials:"
echo "   - ELEVENLABS_API_KEY"
echo "   - GOOGLE_CALENDAR_API_KEY"
echo "   - GOOGLE_PLACES_API_KEY"
echo "   - GOOGLE_MAPS_API_KEY"
echo "   - TWILIO_ACCOUNT_SID"
echo "   - TWILIO_AUTH_TOKEN"
echo "   - TWILIO_PHONE_NUMBER"
echo ""
echo "2. Edit frontend/.env.local:"
echo "   - NEXT_PUBLIC_API_URL (default: http://localhost:8080)"
echo ""
echo "3. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "4. Start the frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "5. Open your browser:"
echo "   http://localhost:3000"
echo ""
echo "📖 For more details, see docs/QUICKSTART.md"
echo "🚀 To deploy to production, see docs/DEPLOYMENT_GUIDE.md"
