variable "project" {
  description = "The ID of the project to deploy to"
  type        = string
}

variable "region" {
  description = "The region to deploy the resources in"
  type        = string
}

variable "service_name" {
  description = "The name of the service"
  type        = string
}

variable "image" {
  description = "The container image to deploy"
  type        = string
}

#variable "index_resource_name" {
#  description = "The resource name of the index"
#  type        = string
#}

#variable "bucket_name" {
#  description = "The name of the bucket"
#  type        = string
#}

variable "customer" {
  description = "Customer identifier"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.customer))
    error_message = "Customer must only contain lowercase letters, numbers, and hyphens"
  }
}

variable "env_vars" {
  description = "Environment variables for the service"
  type        = map(string)
}
