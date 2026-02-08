variable "project_id" {
  description = "The GCP project ID where resources will be created"
  type        = string
}

variable "region" {
  description = "The GCP region for Cloud Run and other regional resources"
  type        = string
  default     = "us-central1"
}

variable "firestore_location" {
  description = "The location for Firestore database (must be a multi-region or region)"
  type        = string
  default     = "us-central"
}

variable "elevenlabs_api_key" {
  description = "ElevenLabs API key for voice AI"
  type        = string
  sensitive   = true
}

variable "google_calendar_api_key" {
  description = "Google Calendar API key"
  type        = string
  sensitive   = true
}

variable "google_places_api_key" {
  description = "Google Places API key for provider search"
  type        = string
  sensitive   = true
}

variable "google_maps_api_key" {
  description = "Google Maps API key for distance calculations"
  type        = string
  sensitive   = true
}

variable "twilio_account_sid" {
  description = "Twilio Account SID for phone calls"
  type        = string
  sensitive   = true
}

variable "twilio_auth_token" {
  description = "Twilio Auth Token"
  type        = string
  sensitive   = true
}

variable "twilio_phone_number" {
  description = "Twilio Phone Number for making calls"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "Secret key for JWT token signing"
  type        = string
  sensitive   = true
}

variable "frontend_url" {
  description = "URL of the frontend application for CORS"
  type        = string
  default     = "https://your-frontend-url.web.app"
}
