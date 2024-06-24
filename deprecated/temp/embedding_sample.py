from google.cloud import storage

storage_client = storage.Client()

def read_image_from_storage(bucket_name, file_path):
   
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    
    #return blob
    image_bytes = blob.download_as_bytes()

    return image_bytes


image_bytes = read_image_from_storage("doit-image-similarity", "images/00276a6e000d87f3855c31e39322cc55e348e3ef_mkp1382646.jpegdummy.jpg")


import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel

vertexai.init(project='sascha-playground-doit', location="us-central1")

image = Image(image_bytes)
model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
embeddings = model.get_embeddings(
    image=image
)
print(f"Image Embedding: {embeddings.image_embedding}")