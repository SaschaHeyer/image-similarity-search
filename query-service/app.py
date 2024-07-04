import uvicorn
import os
from fastapi import Request, FastAPI, Response
from fastapi.responses import JSONResponse
import base64
import datetime
import json  # Import the json module
import re  # Import the regex module

from google.cloud import aiplatform_v1
from google.cloud import aiplatform
from google.cloud import storage  # Import the storage client

import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models

vertexai.init(project='sascha-playground-doit', location="us-central1")

model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
gen_model = GenerativeModel("gemini-1.5-flash-001")

app = FastAPI(title="Image Similarity Query Service")

# Initialize the storage client
storage_client = storage.Client()

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
    print("QEURYYYY####")
    body = await request.json()
    #print(body)

    image_base64 = body.get("image", None)
    text_query = body.get("text", None)
    threshold = body.get("threshold", 0.01)  # Default threshold is 0.7
    limit = body.get("limit", 5)
   
    print(image_base64 is None)
   
    
    start_time0 = datetime.datetime.now() 
    if image_base64:
        image_bytes = base64.b64decode(image_base64)
        image = Image(image_bytes)
    
        embeddings = model.get_embeddings(image=image)
        embeddings = embeddings.image_embedding
        print(f"Image Embedding: {embeddings}")
        
    elif text_query is not None:
        embeddings = model.get_embeddings(contextual_text=text_query)
        embeddings = embeddings.text_embedding
        print(f"Text Embedding: {embeddings}")
    end_time0 = datetime.datetime.now()
    time_diff = (end_time0 - start_time0)
    latency_embedding = time_diff.total_seconds() * 1000
    print(f'latency_multimodal_ranking {latency_embedding}')
    
    
    start_time = datetime.datetime.now()
    matches = index_endpoint.find_neighbors(
        deployed_index_id="product_similarity_1",
        queries=[embeddings],
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

    # Filter matches based on threshold
    filtered_matches = [match for match in formated_response if match['similarity'] >= threshold]

    # Prepare images and text for multimodal model if matches exceed threshold
    if len(filtered_matches) > 0:
        parts = []
        for idx, match in enumerate(filtered_matches):
            if idx >= limit:  
                break
            # Use GCS URI directly
            image_uri = f"gs://doit-image-similarity/{match['id']}"
            parts.append(f"({image_uri})")
            parts.append(Part.from_uri(uri=image_uri, mime_type="image/jpeg"))

        prompt = None

        if image_base64:
            print("using image prompt")
            prompt = f"""We have a product database and we need to find similar products. Given the following product images, return the ones that are the same.
            Return a JSON in the following format:
            {{
                "matching_product_urls": []
            }}"""
        elif text_query is not None:
            print("using text prompt")
            prompt = f"""We have a product database and we need to find similar products. Given the following product images and search query, return the ones that are the same.
            search query: {text_query}
            
            Return a JSON in the following format:
            {{
                "matching_product_urls": []
            }}"""

        generation_config = {
            "max_output_tokens": 8192,
            "top_p": 0.95,
        }

        safety_settings = {
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        # Add prompt as the final part in the parts list
        parts.append(prompt)

        start_time2 = datetime.datetime.now()
        responses = gen_model.generate_content(
            parts,
            generation_config=generation_config,
            safety_settings=safety_settings,
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
