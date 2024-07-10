resource "google_vertex_ai_index" "index" {
  region       = var.region
  display_name = "${var.customer}-index"
  description  = "Index for ${var.customer}"
  metadata {
    contents_delta_uri = "gs://${var.bucket_name}/contents"
    config {
      dimensions           = 2
      shard_size           = "SHARD_SIZE_LARGE"
      distance_measure_type = "COSINE_DISTANCE"
      feature_norm_type     = "UNIT_L2_NORM"
      algorithm_config {
        brute_force_config {}
      }
    }
  }
  index_update_method = "STREAM_UPDATE"
}

resource "google_vertex_ai_index_endpoint_deployed_index" "deployed_index" {
  index_endpoint = google_vertex_ai_index_endpoint.index_endpoint.id
  display_name   = "${var.customer}-deployed-index"
  index          = google_vertex_ai_index.index.id
}

output "index_resource_name" {
  value = google_vertex_ai_index.index.id
}
