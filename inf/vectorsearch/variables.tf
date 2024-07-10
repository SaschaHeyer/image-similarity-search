variable "project" {
  description = "The ID of the GCP project"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "customer" {
  description = "The customer name to be used for naming resources"
  type        = string
}

variable "bucket_name" {
  description = "The name of the existing GCP bucket"
  type        = string
}
