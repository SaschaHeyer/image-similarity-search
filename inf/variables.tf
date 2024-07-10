variable "project" {
  description = "The ID of the GCP project"
  type        = string
  default     = "sascha-playground-doit"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "customer" {
  description = "The customer name to be used for naming resources"
  type        = string
}