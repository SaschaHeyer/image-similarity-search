provider "google" {
  project = var.project
  region  = var.region
}

resource "google_service_account" "eventarc_service_account" {
  account_id   = "similarity-${var.customer}"
  display_name = "Eventarc Service Account"
  project      = var.project
}

resource "google_project_iam_member" "eventarc_sa_invoker" {
  project = var.project
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.eventarc_service_account.email}"
}

resource "google_project_iam_member" "eventarc_sa_receiver" {
  project = var.project
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${google_service_account.eventarc_service_account.email}"
}

resource "google_project_iam_member" "eventarc_sa_token_creator" {
  project = var.project
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${google_service_account.eventarc_service_account.email}"
}

resource "google_eventarc_trigger" "image_similarity_updater" {
  name     = "similarity-updater-${var.customer}"
  location = var.region

  depends_on = [
    google_service_account.eventarc_service_account,
    google_project_iam_member.eventarc_sa_invoker,
    google_project_iam_member.eventarc_sa_receiver,
    google_project_iam_member.eventarc_sa_token_creator,
    #var.cloud_run_service
  ]

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  matching_criteria {
    attribute = "bucket"
    value     = var.bucket_name
  }

  service_account = google_service_account.eventarc_service_account.email

  destination {
    cloud_run_service {
      service = "similarity-updater-${var.customer}"
      region  = var.region
    }
  }
}


