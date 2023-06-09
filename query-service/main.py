import uvicorn
import os
from fastapi import Request, FastAPI, Response
from fastapi.responses import JSONResponse
import requests
from google.cloud import aiplatform

app = FastAPI(title="Image Similarity Query Service")


# TODO read this from the env variables
aiplatform.init(
    project='sascha-playground-doit',
    location='us-central1'
)

# TODO read this from the env variables
endpoint = aiplatform.Endpoint("projects/234439745674/locations/us-central1/endpoints/7365738345634201600")


@app.post('/query')
async def predict(request: Request):
    print('image received')
    body = await request.json()
    print(body)

    image_base64 = body["image"]
    instances = [{"image": image_base64}]
    
    result = endpoint.predict(instances=instances)
    embedding = result[0][0]['embedding']
    print(embedding)

    # TODO read this from the env variables
    ENDPOINT_RESOURCE_NAME = "projects/234439745674/locations/us-central1/indexEndpoints/2199120012575244288"
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=ENDPOINT_RESOURCE_NAME)

    matches = index_endpoint.match(
      deployed_index_id="image_similarity_vpc",
      queries=[embedding],
      num_neighbors=10
    )

    print('got matches')

    formated_response = []
    for match in matches[0]:
      formated_response.append({"id": match.id, "similarity": match.distance})

    return formated_response