import os
import requests
from google.cloud import storage
from flask import Flask, request
from google.cloud import aiplatform_v1
from google.cloud import aiplatform
import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel

# Initialize Vertex AI and AI Platform with environment variables
vertexai.init(project=os.getenv('PROJECT'), location=os.getenv('REGION'))

app = Flask(__name__)

storage_client = storage.Client()

# Initialize AI Platform with environment variables
aiplatform.init(
    project=os.getenv("PROJECT"),
    location=os.getenv("REGION")
)

# Read INDEX_RESOURCE_NAME from environment variables
INDEX_RESOURCE_NAME = os.getenv("INDEX_RESOURCE_NAME")

index_client = aiplatform_v1.IndexServiceClient(
    client_options=dict(api_endpoint="{}-aiplatform.googleapis.com".format(os.getenv('REGION')))
)

@app.route('/', methods=['POST'])
def index():
    print(request.get_json())
    bucket = request.headers.get('ce-subject')
    print(f"Detected change in Cloud Storage bucket: {bucket}")

    image_path = "/".join(bucket.split("/")[1:])
    print("Image path:", image_path)

    image_bytes = read_image_from_storage(os.getenv("BUCKET_NAME"), image_path)
    
    image = Image(image_bytes)
    model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
    embeddings = model.get_embeddings(image=image)
    print(f"Image Embedding: {embeddings.image_embedding}")

    insert_datapoints_payload = aiplatform_v1.IndexDatapoint(
      datapoint_id=image_path,
      feature_vector=embeddings.image_embedding
    )
    upsert_request = aiplatform_v1.UpsertDatapointsRequest(
      index=INDEX_RESOURCE_NAME, datapoints=[insert_datapoints_payload]
    )

    index_client.upsert_datapoints(request=upsert_request)
    print('upsert complete')

    return (f"Detected change in Cloud Storage bucket: {bucket}", 200)

def read_image_from_storage(bucket_name, file_path):
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    image_bytes = blob.download_as_bytes()
    return image_bytes

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
