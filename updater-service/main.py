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
    event_data = request.get_json()
    event_type = request.headers.get('ce-type')
    bucket = event_data['bucket']
    name = event_data['name']
    print(f"Detected change in Cloud Storage bucket: {bucket}, file: {name}")

    if event_type == 'google.cloud.storage.object.v1.finalized':
        # Handle new file upload
        image_bytes = read_image_from_storage(bucket, name)
        image = Image(image_bytes)
        model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
        embeddings = model.get_embeddings(image=image)
        print(f"Image Embedding: {embeddings.image_embedding}")

        insert_datapoints_payload = aiplatform_v1.IndexDatapoint(
            datapoint_id=name,
            feature_vector=embeddings.image_embedding
        )
        upsert_request = aiplatform_v1.UpsertDatapointsRequest(
            index=INDEX_RESOURCE_NAME, datapoints=[insert_datapoints_payload]
        )
        index_client.upsert_datapoints(request=upsert_request)
        print('Upsert complete')

    elif event_type == 'google.cloud.storage.object.v1.deleted':
        # Handle file deletion
        remove_datapoints_request = aiplatform_v1.RemoveDatapointsRequest(
            index=INDEX_RESOURCE_NAME, datapoint_ids=[name]
        )
        index_client.remove_datapoints(request=remove_datapoints_request)
        print('Remove complete')

    return (f"Detected change in Cloud Storage bucket: {bucket}, file: {name}", 200)


def read_image_from_storage(bucket_name, file_path):
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    image_bytes = blob.download_as_bytes()
    return image_bytes

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
