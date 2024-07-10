provider "google" {
  project = var.project
  region  = var.region
}

/* module "services" {
  source  = "./services"
  project = var.project
}

module "bucket" {
  source     = "./bucket"
  project    = var.project
  region     = var.region
  customer   = var.customer
}

module "vectorsearch" {
  source     = "./vectorsearch"
  project    = var.project
  region     = var.region
  customer   = var.customer
  bucket_name = module.bucket.bucket_name
} */

module "image_similarity_updater" {
  source              = "./cloudrun"
  project             = var.project
  region              = var.region
  service_name        = "similarity-updater"
  image               = "gcr.io/${var.project}/image-similarity-updater"
  customer            = var.customer
  env_vars            = {
    #INDEX_RESOURCE_NAME = module.vectorsearch.index_resource_name
    #BUCKET_NAME         = module.bucket.bucket_name
    #ADDITIONAL_VAR      = "value1"
  }
}

module "image_similarity_ui" {
  source              = "./cloudrun"
  project             = var.project
  region              = var.region
  service_name        = "similarity-ui"
  image               = "gcr.io/${var.project}/image-similarity-ui"
  customer            = var.customer
  env_vars            = {
    #ADDITIONAL_VAR      = "value1"
  }
}

module "image_similarity_query" {
  source              = "./cloudrun"
  project             = var.project
  region              = var.region
  service_name        = "similarity-query"
  image               = "gcr.io/${var.project}/image-similarity-query"
  customer            = var.customer
  env_vars            = {
    #ADDITIONAL_VAR      = "value1"
  }
}


#module "eventarc" {
#  source      = "./eventarc"
#  project     = var.project
#  region      = var.region
#  bucket_name = module.bucket.bucket_name
#  customer    = var.customer
#  eventarc_service = module.services.eventarc_service
#}