import uvicorn
from transformers import CLIPModel, CLIPProcessor,AutoProcessor
import os
from fastapi import Request, FastAPI, Response
from fastapi.responses import JSONResponse
from io import StringIO
from PIL import Image
import base64
import io

app = FastAPI(title="Image Similarity Embedding Service")

model = CLIPModel.from_pretrained("../model")
processor = CLIPProcessor.from_pretrained("../model")


import torch
print(torch.cuda.is_available())
print(torch.cuda.device_count())
print(torch.cuda.get_device_name(0))

AIP_HEALTH_ROUTE = os.environ.get('AIP_HEALTH_ROUTE', '/health')
AIP_PREDICT_ROUTE = os.environ.get('AIP_PREDICT_ROUTE', '/predict')

@app.get(AIP_HEALTH_ROUTE, status_code=200)
async def health():
    return {'health': 'ok'}

@app.post(AIP_PREDICT_ROUTE)
async def predict(request: Request):
    body = await request.json()

    instances = body["instances"]

    image_base64 = instances[0]["image"]

    image_data = base64.b64decode(image_base64)  
    image = Image.open(io.BytesIO(image_data))

    inputs = processor(images=image, return_tensors="pt")
    image_features = model.get_image_features(**inputs)

    embedding = {"embedding": image_features[0].tolist()}

    return {"predictions": [embedding]}