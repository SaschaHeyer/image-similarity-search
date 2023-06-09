import os
import requests
from google.cloud import storage
import base64
from flask import Flask, request
from google.cloud import aiplatform_v1
from google.cloud import aiplatform


app = Flask(__name__)

storage_client = storage.Client()

# TODO read this from the env variables
aiplatform.init(
    project=os.environ.get("PROJECT"),
    location=os.environ.get("REGION")
)

endpoint = aiplatform.Endpoint("projects/234439745674/locations/us-central1/endpoints/7365738345634201600")

# TODO read this from the env variables
INDEX_RESOURCE_NAME = "projects/234439745674/locations/us-central1/indexes/8666289077479276544"

index_client = aiplatform_v1.IndexServiceClient(
    client_options=dict(api_endpoint="{}-aiplatform.googleapis.com".format('us-central1'))
)


@app.route('/', methods=['POST'])
def index():
    print(request.get_json())
    # Gets the GCS bucket name from the CloudEvent header
    # Example: "storage.googleapis.com/projects/_/buckets/my-bucket"
    bucket = request.headers.get('ce-subject')

    print(f"Detected change in Cloud Storage bucket: {bucket}")

    # TODO can be parsed easier by using name and bucket in the request json
    image_path = "/".join(bucket.split("/")[1:])

    print("Image path:", image_path)

    image = read_image_from_storage("doit-image-similarity", image_path)
    image_base64 = base64.b64encode(image).decode()
    
    instances = [{"image": image_base64}]
    
    result = endpoint.predict(instances=instances)
    embedding = result[0][0]['embedding']
    print(embedding)
    print('got embedding')

    insert_datapoints_payload = aiplatform_v1.IndexDatapoint(
      datapoint_id=image_path,
      feature_vector=embedding
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
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
