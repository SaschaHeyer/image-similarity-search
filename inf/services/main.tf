provider "google" {
  project = var.project
}

resource "google_project_service" "run" {
  service = "run.googleapis.com"
  project = var.project
}

resource "google_project_service" "eventarc" {
  service = "eventarc.googleapis.com"
  project = var.project
}

resource "google_project_service" "storage" {
  service = "storage.googleapis.com"
  project = var.project
}

resource "google_project_service" "cloudbuild" {
  service = "cloudbuild.googleapis.com"
  project = var.project
}

resource "google_project_service" "aiplatform" {
  service = "aiplatform.googleapis.com"
  project = var.project
}

output "eventarc_service" {
  value = google_project_service.eventarc
}
