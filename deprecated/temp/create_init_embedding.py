import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel

# TODO(developer): Update values for project_id, image_path & contextual_text
vertexai.init(project='sascha-playground-doit', location="us-central1")

model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")

Image._as_base64_string()
image = Image.load_from_file('/Users/sascha/Desktop/development/image-similarity-search/temp/init.jpeg')
print(image)
#model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")

embeddings = model.get_embeddings(
    image=image,
)
print(f"Image Embedding: {embeddings.image_embedding}")