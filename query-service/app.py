import uvicorn
import os
from fastapi import Request, FastAPI, Response
from fastapi.responses import JSONResponse
import base64
import datetime
import json  # Import the json module
import re  # Import the regex module

from google.cloud import aiplatform
from google.cloud import storage  # Import the storage client

import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig


vertexai.init(project='sascha-playground-doit', location="us-central1")

embedding_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
model = GenerativeModel("gemini-1.5-pro-001")

app = FastAPI(title="Image Similarity Query Service")

# Initialize the storage client
storage_client = storage.Client()

# TODO read this from the env variables
aiplatform.init(
    project=os.environ.get("PROJECT"),
    location='us-central1'
)

# TODO read this from the env variables
ENDPOINT_RESOURCE_NAME = "projects/234439745674/locations/us-central1/indexEndpoints/845467267155099648"
index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=ENDPOINT_RESOURCE_NAME)

@app.post('/query')
async def predict(request: Request):
    body = await request.json()
    
    image_base64 = body.get("image", None)
    text_query = body.get("text", None)
    threshold = body.get("threshold", 0.01)  # Default threshold is 0.7
    reranker_limit = body.get("rerankerLimit", 5)

    start_time0 = datetime.datetime.now() 
    if image_base64:
        image_bytes = base64.b64decode(image_base64)
        image = Image(image_bytes)
    
        embeddings = embedding_model.get_embeddings(image=image)
        embeddings = embeddings.image_embedding
        
    elif text_query is not None:
        embeddings = embedding_model.get_embeddings(contextual_text=text_query)
        embeddings = embeddings.text_embedding
    end_time0 = datetime.datetime.now()
    time_diff = (end_time0 - start_time0)
    latency_embedding = time_diff.total_seconds() * 1000
    
    
    start_time = datetime.datetime.now()
    matches = index_endpoint.find_neighbors(
        deployed_index_id="product_similarity_1",
        queries=[embeddings],
        num_neighbors=10, #TODO add this as parameter
    )
    
    end_time = datetime.datetime.now()
    time_diff = (end_time - start_time)
    latency_matching = time_diff.total_seconds() * 1000

    formated_response = []
    for match in matches[0]:
        formated_response.append({"id": match.id, "similarity": match.distance})

    # Filter matches based on threshold
    filtered_matches = [match for match in formated_response if match['similarity'] >= threshold]

    # Prepare images and text for multimodal model if matches exceed threshold
    if len(filtered_matches) > 0:
        parts = []
        for idx, match in enumerate(filtered_matches):
            if idx >= reranker_limit:  
                break
            # Use GCS URI directly
            image_uri = f"gs://doit-image-similarity/{match['id']}"
            parts.append(f"({image_uri})")
            parts.append(Part.from_uri(uri=image_uri, mime_type="image/jpeg"))

        prompt = None

        if image_base64:
            prompt = f"""We have a product database and we need to find similar products. Given the following product images, return the ones that are the same.
            """
        elif text_query is not None:
            prompt = f"""We have a product database and we need to find similar products. Given the following product images and search query, return the ones that are the same.
            search query: {text_query}
            """

        response_schema= {
            "type": "object",
            "properties": {
                "matching_product_urls": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["matching_product_urls"]
        }

        generation_config = GenerationConfig(
            temperature=1.0,
            max_output_tokens=8192,
            response_mime_type="application/json",
            response_schema=response_schema
        )

        # Add prompt as the final part in the parts list
        parts.append(prompt)
    
        
        start_time2 = datetime.datetime.now()
        responses = model.generate_content(
            parts,
            generation_config=generation_config,
            stream=False,
        )
        
        end_time2 = datetime.datetime.now()
        time_diff = (end_time2 - start_time2)
        latency_multimodal_ranking = time_diff.total_seconds() * 1000
        print(f'latency_multimodal_ranking {latency_multimodal_ranking}')
        
        multimodal_result = responses.candidates[0].content.parts[0].text
        
        # Use regex to extract JSON content between the first '{' and the last '}'
        json_match = re.search(r'\{.*\}', multimodal_result, re.DOTALL)
        if json_match:
            cleaned_result = json_match.group(0)
        else:
            cleaned_result = '{"error": "Invalid JSON response from multimodal model"}'

        # Try to parse the cleaned_result as JSON
        try:
            multimodal_result_json = json.loads(cleaned_result)
        except json.JSONDecodeError:
            multimodal_result_json = {"error": "Invalid JSON response from multimodal model"}

       

        return JSONResponse(content={
            "formatted_response": formated_response,
            "multimodal_result": multimodal_result_json,
            "response_times": {
                "embedding": latency_embedding,
                "vector_search": latency_matching,
                "multimodal_re_ranking": latency_multimodal_ranking
            }
        })

    return JSONResponse(content={
        "formatted_response": formated_response,
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
