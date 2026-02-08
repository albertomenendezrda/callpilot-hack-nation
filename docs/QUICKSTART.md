# CallPilot - Quick Start Guide

This guide will help you set up CallPilot locally for development.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js 18+** and npm
- **Python 3.11+**
- **Git**
- **Google Cloud SDK** (gcloud CLI) - [Install here](https://cloud.google.com/sdk/docs/install)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd callpilot
```

### 2. Run Setup Script

We provide an automated setup script that configures both frontend and backend:

```bash
chmod +x setup.sh
./setup.sh
```

This script will:
- Check prerequisites
- Set up Python virtual environment
- Install backend dependencies
- Install frontend dependencies
- Create environment file templates

### 3. Configure Environment Variables

#### Backend Configuration

Edit `backend/.env`:

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-dev-secret-key

# ElevenLabs API
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Google APIs
GOOGLE_CALENDAR_API_KEY=your-google-calendar-api-key
GOOGLE_PLACES_API_KEY=your-google-places-api-key
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# Twilio Configuration
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

**Getting API Keys:**

- **ElevenLabs**: Sign up at [elevenlabs.io](https://elevenlabs.io) and get your API key from the dashboard
- **Google APIs**:
  - Go to [Google Cloud Console](https://console.cloud.google.com)
  - Enable Calendar API, Places API, and Maps API
  - Create API credentials
- **Twilio**:
  - Sign up at [twilio.com](https://twilio.com)
  - Get your Account SID, Auth Token, and phone number

#### Frontend Configuration

Edit `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### 4. Start the Backend

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

The backend will start at http://localhost:8080

### 5. Start the Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

The frontend will start at http://localhost:3000

### 6. Test the Application

Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **Backend Health Check**: http://localhost:8080/health

## Development Workflow

### Making Changes

1. **Frontend**: Edit files in `frontend/app` and `frontend/components`
   - Changes hot-reload automatically
   - Use `npm run lint` to check for errors

2. **Backend**: Edit files in `backend/`
   - Restart the Flask server after changes
   - Use `pytest` to run tests (when added)

### Project Structure

```
callpilot/
├── frontend/           # Next.js application
│   ├── app/           # Pages and layouts
│   ├── components/    # React components
│   └── lib/           # Utilities
├── backend/           # Flask API
│   ├── services/      # Business logic
│   ├── models/        # Data models
│   └── app.py         # Main application
├── terraform/         # Infrastructure as code
├── docs/             # Documentation
└── scripts/          # Deployment scripts
```

## Common Issues

### Port Already in Use

If you get "port already in use" errors:

```bash
# Kill process on port 8080 (backend)
lsof -ti:8080 | xargs kill -9

# Kill process on port 3000 (frontend)
lsof -ti:3000 | xargs kill -9
```

### Python Dependencies Error

If pip install fails:

```bash
# Upgrade pip
pip install --upgrade pip

# Try installing again
pip install -r backend/requirements.txt
```

### Node Modules Error

If npm install fails:

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

- Read the [Deployment Guide](DEPLOYMENT_GUIDE.md) to deploy to production
- Check the [API Documentation](API.md) for backend endpoints
- Review the [Architecture Guide](ARCHITECTURE.md) for system design

## Getting Help

- Check existing issues on GitHub
- Read the main [README.md](../README.md)
- Contact the team for support

## Development Tips

1. **Use TypeScript strictly** - Run `npm run lint` frequently
2. **Test API endpoints** - Use Postman or curl to test backend endpoints
3. **Check logs** - Backend logs appear in the terminal where you ran `python app.py`
4. **Hot reload** - Frontend changes appear instantly; backend requires restart
