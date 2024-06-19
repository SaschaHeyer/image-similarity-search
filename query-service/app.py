import uvicorn
import os
from fastapi import Request, FastAPI, Response
from fastapi.responses import JSONResponse
import requests
import base64
import datetime

from google.cloud import aiplatform_v1
from google.cloud import aiplatform


import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel

vertexai.init(project='sascha-playground-doit', location="us-central1")

model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")

app = FastAPI(title="Image Similarity Query Service")




# TODO read this from the env variables
aiplatform.init(
    project=os.environ.get("PROJECT"),
    location='us-central1'
)

index_client = aiplatform_v1.IndexServiceClient(
    client_options=dict(api_endpoint="{}-aiplatform.googleapis.com".format(os.environ.get("PROJECT")))
)

# TODO read this from the env variables
ENDPOINT_RESOURCE_NAME = "projects/234439745674/locations/us-central1/indexEndpoints/845467267155099648"
index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=ENDPOINT_RESOURCE_NAME)


@app.post('/query')
async def predict(request: Request):
    print('image received')
    body = await request.json()
    print(body)

    image_base64 = body["image"]
    #instances = [{"image": image_base64}]
    
    #result = endpoint.predict(instances=instances)
    #embedding = result[0][0]['embedding']
    
    #print(embedding)
    
    

 
    #matches = index_endpoint.match(
    #  deployed_index_id="image_similarity_vpc",
    #  queries=[embedding],
    #  num_neighbors=20
    #)

    #print('got matches')

    #formated_response = []
    #for match in matches[0]:
    #  formated_response.append({"id": match.id, "similarity": match.distance})

    #return formated_response
    
    #image_bytes = read_image_from_storage("doit-image-similarity", image_path)
    #image_base64 = base64.b64encode(image).decode()
    image_bytes = base64.b64decode(image_base64)
    
    image = Image(image_bytes)
   
    embeddings = model.get_embeddings(
        image=image
    )
    print(f"Image Embedding: {embeddings.image_embedding}")
    
    start_time = datetime.datetime.now()
    #matches = index_endpoint.match(
    #  deployed_index_id="product_similarity_1",
    #  queries=[embeddings.image_embedding],
    #  num_neighbors=10
    #)
    
    matches = index_endpoint.find_neighbors(
        deployed_index_id="product_similarity_1",
        queries=[embeddings.image_embedding],
        num_neighbors=10,
    )
    print(matches)

    
    end_time = datetime.datetime.now()

    time_diff = (end_time - start_time)
    latency_matching = time_diff.total_seconds() * 1000
    print(f'latency matching {latency_matching}')

    formated_response = []
    for match in matches[0]:
      formated_response.append({"id": match.id, "similarity": match.distance})

    return formated_response