terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "places-backend.googleapis.com",
    "maps-backend.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Create Firestore database for storing booking requests
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.required_apis]
}

# Secret Manager secrets
resource "google_secret_manager_secret" "elevenlabs_api_key" {
  secret_id = "elevenlabs-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "elevenlabs_api_key" {
  secret      = google_secret_manager_secret.elevenlabs_api_key.id
  secret_data = var.elevenlabs_api_key
}

resource "google_secret_manager_secret" "google_calendar_api_key" {
  secret_id = "google-calendar-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "google_calendar_api_key" {
  secret      = google_secret_manager_secret.google_calendar_api_key.id
  secret_data = var.google_calendar_api_key
}

resource "google_secret_manager_secret" "google_places_api_key" {
  secret_id = "google-places-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "google_places_api_key" {
  secret      = google_secret_manager_secret.google_places_api_key.id
  secret_data = var.google_places_api_key
}

resource "google_secret_manager_secret" "google_maps_api_key" {
  secret_id = "google-maps-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "google_maps_api_key" {
  secret      = google_secret_manager_secret.google_maps_api_key.id
  secret_data = var.google_maps_api_key
}

resource "google_secret_manager_secret" "twilio_account_sid" {
  secret_id = "twilio-account-sid"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "twilio_account_sid" {
  secret      = google_secret_manager_secret.twilio_account_sid.id
  secret_data = var.twilio_account_sid
}

resource "google_secret_manager_secret" "twilio_auth_token" {
  secret_id = "twilio-auth-token"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "twilio_auth_token" {
  secret      = google_secret_manager_secret.twilio_auth_token.id
  secret_data = var.twilio_auth_token
}

resource "google_secret_manager_secret" "twilio_phone_number" {
  secret_id = "twilio-phone-number"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "twilio_phone_number" {
  secret      = google_secret_manager_secret.twilio_phone_number.id
  secret_data = var.twilio_phone_number
}

resource "google_secret_manager_secret" "jwt_secret_key" {
  secret_id = "jwt-secret-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "jwt_secret_key" {
  secret      = google_secret_manager_secret.jwt_secret_key.id
  secret_data = var.jwt_secret_key
}

# Service account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "callpilot-backend-sa"
  display_name = "CallPilot Backend Service Account"
  description  = "Service account for CallPilot Cloud Run service"

  depends_on = [google_project_service.required_apis]
}

# Grant Secret Manager access to service account
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each = toset([
    "elevenlabs-api-key",
    "google-calendar-api-key",
    "google-places-api-key",
    "google-maps-api-key",
    "twilio-account-sid",
    "twilio-auth-token",
    "twilio-phone-number",
    "jwt-secret-key",
  ])

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"

  depends_on = [
    google_secret_manager_secret.elevenlabs_api_key,
    google_secret_manager_secret.google_calendar_api_key,
    google_secret_manager_secret.google_places_api_key,
    google_secret_manager_secret.google_maps_api_key,
    google_secret_manager_secret.twilio_account_sid,
    google_secret_manager_secret.twilio_auth_token,
    google_secret_manager_secret.twilio_phone_number,
    google_secret_manager_secret.jwt_secret_key,
  ]
}

# Grant Firestore access to service account
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Note: Cloud Run service is managed by deployment scripts
# Run ./scripts/deploy-backend.sh to deploy the backend to Cloud Run
