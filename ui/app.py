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

# Add a checkbox to enable the Gemini reranker
enable_gemini_reranker = st.checkbox("Enable Gemini Reranker")

response = None
response_time = None

# Handle image upload case
if uploaded_file is not None:
    with image_col:
        image = Image.open(uploaded_file)
        st.image(image, caption='Reference image to find similar ones.', width=150)

    img_bytes = uploaded_file.getvalue()
    base64_encoded_image = base64.b64encode(img_bytes).decode()

    # Measure response time
    start_time = time.time()
    response = requests.post(f'{API_URL}/query', json={"image": base64_encoded_image, "enableGeminiReranker": enable_gemini_reranker})
    response_time = time.time() - start_time

    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        st.stop()

# Handle text query case
elif text_query and text_query.strip():
    # Measure response time
    start_time = time.time()
    response = requests.post(f'{API_URL}/query', json={"text": text_query, "enableGeminiReranker": enable_gemini_reranker})
    response_time = time.time() - start_time

    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        st.stop()

# Process the response if available
if response is not None:
    response_json = response.json()

    # Extract response times
    embedding_time = response_json["response_times"].get("embedding", 0)
    vector_search_time = response_json["response_times"].get("vector_search", 0)
    multimodal_re_ranking_time = response_json["response_times"].get("multimodal_re_ranking", None)

    # Display individual response times
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric(label="Embedding Time", value=f"{embedding_time:.2f} ms")
    with col2:
        st.metric(label="Vector Search Time", value=f"{vector_search_time:.2f} ms")

    # Only show re-ranking time if Gemini reranker was enabled and re-ranking was done
    if multimodal_re_ranking_time is not None:
        with col3:
            st.metric(label="Multimodal Re-ranking Time", value=f"{multimodal_re_ranking_time:.2f} ms")

    # Conditionally print response JSON if debug mode is enabled
    if debug_mode:
        st.subheader("Response JSON")
        st.json(response_json)

    # Initialize Google Cloud Storage client
    storage_client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_JSON)
    bucket = storage_client.get_bucket(BUCKET_NAME)

    # Process exact matches and similar matches as before
    signed_images_exact = []
    signed_images_similar = []
    similarities_exact = []
    similarities_similar = []

    matches = response_json.get("formatted_response", [])
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

    # Generate signed URLs for generated AI matches (only if Gemini reranker was applied)
    signed_images_gen_ai = []
    gen_ai_paths = []

    if enable_gemini_reranker and "multimodal_result" in response_json:
        multimodal_result = response_json["multimodal_result"].get("matching_product_urls", [])
        for url in multimodal_result:
            blob = storage.Blob.from_string(url, client=storage_client)
            signed_url = blob.generate_signed_url(timedelta(hours=1), method='GET')
            signed_images_gen_ai.append(signed_url)
            gen_ai_paths.append(url)

    # Layout for displaying the results
    col1, col2, col3 = st.columns(3)

    with col1:
        st.header("Exact Matches")
        st.markdown("Exact matches with a similarity score of 1.0. Only used when searching based on an image")
        cols = cycle(st.columns(4))
        for idx, filteredImage in enumerate(signed_images_exact):
            col = next(cols)
            col.image(filteredImage, caption=f"ID: {id_list[idx][-20:]} \nSimilarity: {similarities_exact[idx]:.2f}", use_column_width=True)

    with col2:
        st.header("Similar Matches")
        st.markdown("Vector Search results")
        cols = cycle(st.columns(4))
        for idx, filteredImage in enumerate(signed_images_similar):
            col = next(cols)
            col.image(filteredImage, caption=f"ID: {id_list[idx + len(signed_images_exact)][-20:]} \nSimilarity: {similarities_similar[idx]:.2f}", use_column_width=True)


    with col3:
        if enable_gemini_reranker and signed_images_gen_ai:
            st.header("Matches refined using Gemini model")
            st.markdown("Matches returned from the similarity search are passed to Google's multimodal model. This step refines the results.")
            cols = cycle(st.columns(4))
            for idx, filteredImage in enumerate(signed_images_gen_ai):
                col = next(cols)
                col.image(filteredImage, caption=f"Path: {gen_ai_paths[idx][-20:]}", use_column_width=True)

    