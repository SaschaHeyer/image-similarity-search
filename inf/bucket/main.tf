provider "google" {
  project = var.project
  region  = var.region
}

resource "google_storage_bucket" "bucket" {
  name                        = "image-similarity-search-${var.customer}"
  location                    = var.region
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_object" "data" {
  name   = "contents/data.json"
  bucket = google_storage_bucket.bucket.name
  content = <<EOF
{"id": "00000", "embedding": [0.5, 1.0]}
EOF
}

output "bucket_name" {
  value = google_storage_bucket.bucket.name
}
