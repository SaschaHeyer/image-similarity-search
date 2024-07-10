variable "project" {
  description = "The ID of the GCP project"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "bucket_name" {
  description = "The name of the existing GCP bucket"
  type        = string
}

variable "customer" {
  description = "The customer name to be used for naming resources"
  type        = string
}

variable "eventarc_service" {
  description = "Reference to the eventarc service"
  type        = any
}

#variable "cloud_run_service" {
#  description = "The Cloud Run service for the image similarity updater"
#  type        = string
#}
