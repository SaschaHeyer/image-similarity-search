# Image Similarity Search

## Architecture

The architecture can scale to any number of requests and is built on top of 

* Cloud Run 
* Vertex AI Endpoint (It uses the latest state-of-the-art CLIP model for creating embeddings and requires a GPU for good performance)
* Vertex AI Matching Engine

![](images/architecture.png)

## Setup

### Enabled APIs

````
!gcloud services enable run.googleapis.com \
    eventarc.googleapis.com \
    storage.googleapis.com \
    cloudbuild.googleapis.com
````

### Matching Engine 

1. Create Matching Engine Streaming Index
2. Create Matching Engine Endpoint
3. Create Matching Engine Endpoint
4. Deploy Index to Endpoint

more details https://medium.com/google-cloud/all-you-need-to-know-about-google-vertex-ai-matching-engine-3344e85ad565

## Deploy Updater and Query Services

The updater and query Cloud Run services can be deployed automatically using Cloud Build. 
The two folder contain a cloudbuild.yaml.
**Will consider terraform for future versions of this POC**

````
gcloud builds submit --config cloudbuild.yaml
````

## Deploy Embedding Service
The embedding service hosts the CLIP model that uses a GPU for performance and it deployed to Vertex AI.

### Model Artifact
The model artifact is integrated into the Docker container to reduce cold start times and network traffic. 

Download the model locally
````
git lfs install
git clone https://huggingface.co/openai/clip-vit-large-patch14
````

Upload the python artifacts to a Google Cloud Storage location

### Build the serving container using Cloud Build

````
gcloud builds submit --config cloudbuild.yaml
````

### Upload the model / serving container to Vertex AI Model Registry

````
!gcloud ai models upload \
  --container-ports=8080 \
  --container-predict-route="/predict" \
  --container-health-route="/health" \
  --region=us-central1 \
  --display-name=image-similarity-embedding \
  --container-image-uri=gcr.io/sascha-playground-doit/image-similarity-embedding
````

### Create a Vertex AI Endpoint

````
!gcloud ai endpoints create \
  --project=sascha-playground-doit \
  --region=us-central1 \
  --display-name=image-similarity-embedding
````


### Deploy the model to the endpoint
````
!gcloud ai endpoints deploy-model 7365738345634201600 \
  --project=sascha-playground-doit \
  --region=us-central1 \
  --model=8881690002430361600 \
  --traffic-split=0=100 \
  --machine-type="n1-standard-16" \
  --accelerator=type="nvidia-tesla-t4,count=1" \
  --display-name=image-similarity-embedding
````

## Usage

### Add new images to Matching Engine (Vector Database)
To add new images to the vector simply upload them to the bucket that is defined in the updater service. 

### POC UI
The POC contains a UI that is deployed to Cloud Run. It provides an interface to upload an image and shows matching images returned from the index. 

https://image-similarity-ui-xgdxnb6fdq-uc.a.run.app

## Possible Optimization
* Use Google Cloud Vertex AI Image Embedding API instead of the custom build embedding model hosted on Vertex AI
* Use Google Cloud Workflows to orchestrate the Cloud Run Services
* Use Google Cloud Workflows for the Cloud Storage trigger
