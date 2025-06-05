import uvicorn
import os
from fastapi import Request, FastAPI
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

# Initialize Vertex AI and the models
vertexai.init(project='sascha-playground-doit', location="us-central1")

embedding_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
model = GenerativeModel("gemini-2.5-flash-preview-05-20")

app = FastAPI(title="Image Similarity Query Service")

# Initialize the storage client
storage_client = storage.Client()

# TODO: Read this from the env variables
aiplatform.init(
    project=os.environ.get("PROJECT"),
    location='us-central1'
)

# TODO: Read this from the env variables
ENDPOINT_RESOURCE_NAME = "projects/234439745674/locations/us-central1/indexEndpoints/845467267155099648"
index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=ENDPOINT_RESOURCE_NAME)


@app.post('/query')
async def predict(request: Request):
    body = await request.json()

    image_base64 = body.get("image", None)
    text_query = body.get("text", None)
    threshold = body.get("threshold", 0.01)  # Default threshold is 0.01
    reranker_limit = body.get("rerankerLimit", 5)
    enable_gemini_reranker = body.get("enableGeminiReranker", True)  # Default to True (reranker enabled)

    start_time0 = datetime.datetime.now()

    # Get embeddings based on image or text input
    if image_base64:
        image_bytes = base64.b64decode(image_base64)
        image = Image(image_bytes)
        embeddings = embedding_model.get_embeddings(image=image).image_embedding
    elif text_query is not None:
        embeddings = embedding_model.get_embeddings(contextual_text=text_query).text_embedding
    else:
        return JSONResponse(content={"error": "No image or text query provided"}, status_code=400)

    end_time0 = datetime.datetime.now()
    latency_embedding = (end_time0 - start_time0).total_seconds() * 1000

    # Find neighbors using Matching Engine
    start_time = datetime.datetime.now()
    matches = index_endpoint.find_neighbors(
        deployed_index_id="product_similarity_1",
        queries=[embeddings],
        num_neighbors=10,  # Adjust as needed
    )
    end_time = datetime.datetime.now()
    latency_matching = (end_time - start_time).total_seconds() * 1000

    # Format the response
    formatted_response = [{"id": match.id, "similarity": match.distance} for match in matches[0]]
    filtered_matches = [match for match in formatted_response if match['similarity'] >= threshold]

    # Conditional call to Gemini reranker based on the `enable_gemini_reranker` flag
    multimodal_result_json = {}
    if enable_gemini_reranker and filtered_matches:
        parts = []
        for idx, match in enumerate(filtered_matches):
            if idx >= reranker_limit:
                break
            image_uri = f"gs://doit-image-similarity/{match['id']}"
            parts.append(f"({image_uri})")
            parts.append(Part.from_uri(uri=image_uri, mime_type="image/jpeg"))

        prompt = None
        if image_base64:
            prompt = "We have a product database and we need to find similar products. Given the following product images, return the ones that are the same."
        elif text_query is not None:
            prompt = f"We have a product database and we need to find similar products. Given the following product images and search query, return the ones that are the same. search query: {text_query}"

        response_schema = {
            "type": "object",
            "properties": {
                "matching_product_urls": {
                    "type": "array",
                    "items": {"type": "string"}
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

        # Add the prompt to the list of parts
        parts.append(prompt)

        # Call the Gemini model to get reranked results
        start_time2 = datetime.datetime.now()
        responses = model.generate_content(parts, generation_config=generation_config, stream=False)
        end_time2 = datetime.datetime.now()
        latency_multimodal_ranking = (end_time2 - start_time2).total_seconds() * 1000

        multimodal_result = responses.candidates[0].content.parts[0].text

        # Extract JSON content from the multimodal model's response
        json_match = re.search(r'\{.*\}', multimodal_result, re.DOTALL)
        cleaned_result = json_match.group(0) if json_match else '{"error": "Invalid JSON response from multimodal model"}'

        try:
            multimodal_result_json = json.loads(cleaned_result)
        except json.JSONDecodeError:
            multimodal_result_json = {"error": "Invalid JSON response from multimodal model"}

        return JSONResponse(content={
            "formatted_response": formatted_response,
            "multimodal_result": multimodal_result_json,
            "response_times": {
                "embedding": latency_embedding,
                "vector_search": latency_matching,
                "multimodal_re_ranking": latency_multimodal_ranking
            }
        })

    # Return response without Gemini reranking if it's disabled
    return JSONResponse(content={
        "formatted_response": formatted_response,
        "response_times": {
            "embedding": latency_embedding,
            "vector_search": latency_matching
        }
    })


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
