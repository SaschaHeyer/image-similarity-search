import streamlit as st
from PIL import Image
import base64
import requests
from google.cloud import storage
from datetime import timedelta
from itertools import cycle
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
API_URL = os.getenv('API_URL')
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON')
BUCKET_NAME = os.getenv('BUCKET_NAME')

st.set_page_config(layout="wide")

st.title("DoiT Find Similar Products Demo")
st.markdown("This application is a POC that shows the functionality around image similarity and text to image search")

# Create two columns for the upload section
upload_col, image_col = st.columns([1, 1])

with upload_col:
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png"])
    text_query = st.text_input("If you don't have an image you can enter text to search...", "")
    debug_mode = st.checkbox("Enable Debugging")

response = None
response_time = None

# Handle image upload case
if uploaded_file is not None:
    with image_col:
        image = Image.open(uploaded_file)
        st.image(image, caption='Reference image to find similar ones.', width=150)  # Set the width as desired

    img_bytes = uploaded_file.getvalue()
    base64_encoded_image = base64.b64encode(img_bytes).decode()

    # Measure response time
    start_time = time.time()
    response = requests.post(f'{API_URL}/query', json={"image": base64_encoded_image})
    response_time = time.time() - start_time

    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        st.stop()

# Handle text query case
elif text_query and text_query.strip():
    # Measure response time
    start_time = time.time()
    response = requests.post(f'{API_URL}/query', json={"text": text_query})
    response_time = time.time() - start_time

    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        st.stop()

# Process the response if available
if response is not None:
    response_json = response.json()
    embedding_time = response_json["response_times"]["embedding"]
    vector_search_time = response_json["response_times"]["vector_search"]
    multimodal_re_ranking_time = response_json["response_times"]["multimodal_re_ranking"]
    
    # Display individual response times in one row
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric(label="Embedding Time", value=f"{embedding_time:.2f} ms")
    with col2:
        st.metric(label="Vector Search Time", value=f"{vector_search_time:.2f} ms")
    with col3:
        st.metric(label="Multimodal Re-ranking Time", value=f"{multimodal_re_ranking_time:.2f} ms")
    

    # Conditionally print response JSON if debug mode is enabled
    if debug_mode:
        st.subheader("Response JSON")
        st.json(response_json)

    st.title('Matching Images')

    # Initialize Google Cloud Storage client
    storage_client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_JSON)
    bucket = storage_client.get_bucket(BUCKET_NAME)

    signed_images_exact = []
    signed_images_similar = []
    similarities_exact = []
    similarities_similar = []

    matches = response_json.get("formatted_response", [])
    multimodal_result = response_json.get("multimodal_result", {}).get("matching_product_urls", [])

    id_list = [item['id'] for item in matches]
    similarities = [item['similarity'] for item in matches]

    for idx, id in enumerate(id_list):
        blob = bucket.blob(id)
        signed_url = blob.generate_signed_url(timedelta(hours=1), method='GET')
        if similarities[idx] >= 0.99:
            signed_images_exact.append(signed_url)
            similarities_exact.append(similarities[idx])
        else:
            signed_images_similar.append(signed_url)
            similarities_similar.append(similarities[idx])

    # Generate signed URLs for generated AI matches
    signed_images_gen_ai = []
    gen_ai_paths = []
    for url in multimodal_result:
        blob = storage.Blob.from_string(url, client=storage_client)
        signed_url = blob.generate_signed_url(timedelta(hours=1), method='GET')
        signed_images_gen_ai.append(signed_url)
        gen_ai_paths.append(url)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.header("Exact Matches")
        st.markdown("Exact matches with a similarity score of 1.0. Only used when searching based on an image")
        cols = cycle(st.columns(4))
        for idx, filteredImage in enumerate(signed_images_exact):
            col = next(cols)
            col.image(filteredImage, caption=f"ID: {id_list[idx][-20:]} \nSimilarity: {similarities_exact[idx]:.2f}", use_column_width=True)

    with col2:
        st.header("Matches refined using Gemini model")
        st.markdown("Matches returned from the similarity search are passed to Googles multimodal model. This step can be extended to use additional product meta data if available. Using the top 5 results found my Vector Search.")
        cols = cycle(st.columns(4))
        for idx, filteredImage in enumerate(signed_images_gen_ai):
            col = next(cols)
            col.image(filteredImage, caption=f"Path: {gen_ai_paths[idx][-20:]}", use_column_width=True)

    with col3:
        st.header("Similar Matches")
        st.markdown("Vector Search results")
        cols = cycle(st.columns(4))
        for idx, filteredImage in enumerate(signed_images_similar):
            col = next(cols)
            col.image(filteredImage, caption=f"ID: {id_list[idx + len(signed_images_exact)][-20:]} \nSimilarity: {similarities_similar[idx]:.2f}", use_column_width=True)
