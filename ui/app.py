import streamlit as st
import io
from PIL import Image
import base64
import requests
from google.cloud import storage
from datetime import timedelta
from itertools import cycle
import time

# Set page layout to wide
st.set_page_config(layout="wide")

st.title("DoiT Find Similar Products Demo")
st.markdown("This application is a POC that shows the functionality around image similarity search")

# Create two columns for the upload section
upload_col, image_col = st.columns([1, 1])

with upload_col:
    uploaded_file = st.file_uploader("Choose an image...", type="jpg")

response = None

if uploaded_file is not None:
    with image_col:
        image = Image.open(uploaded_file)
        st.image(image, caption='Reference image to find similar ones.', width=150)  # Set the width as desired

    img_bytes = uploaded_file.getvalue()
    base64_encoded_image = base64.b64encode(img_bytes).decode()

    # Measure response time
    start_time = time.time()
    #print('response start')
    response = requests.post('https://image-similarity-query-xgdxnb6fdq-uc.a.run.app/query', json={"image": base64_encoded_image})
    response_time = time.time() - start_time
    st.text(response)
    #print(response.text)
    #print('response received')
    st.write(f"Response time: {response_time:.2f} seconds")
    
    #if response.status_code == 200:
    #    st.success(f"The image was successfully uploaded: {response.text}")
    #else:
    #    st.error(f"The image upload failed: {response.text}")

st.title('Matching Images')

if response is not None:
    storage_client = storage.Client.from_service_account_json('sascha-playground-doit-a4e18c1806bd.json')
    bucket = storage_client.get_bucket('doit-image-similarity')

    signed_images_exact = []
    signed_images_similar = []
    similarities_exact = []
    similarities_similar = []

    response_json = response.json()
    id_list = [item['id'] for item in response_json]
    similarities = [item['similarity'] for item in response_json]

    for idx, id in enumerate(id_list):
        blob = bucket.blob(id)
        signed_url = blob.generate_signed_url(timedelta(hours=1), method='GET')
        if similarities[idx] >= 0.99:
            signed_images_exact.append(signed_url)
            similarities_exact.append(similarities[idx])
        else:
            signed_images_similar.append(signed_url)
            similarities_similar.append(similarities[idx])

    col1, col2 = st.columns(2)

    with col1:
        st.header("Exact Matches")
        cols = cycle(st.columns(4))
        for idx, filteredImage in enumerate(signed_images_exact):
            col = next(cols)
            col.image(filteredImage, caption=f"ID: {id_list[idx][-20:]} \nSimilarity: {similarities_exact[idx]:.2f}", use_column_width=True)

    with col2:
        st.header("Similar Matches")
        cols = cycle(st.columns(4))
        for idx, filteredImage in enumerate(signed_images_similar):
            col = next(cols)
            col.image(filteredImage, caption=f"ID: {id_list[idx + len(signed_images_exact)][-20:]} \nSimilarity: {similarities_similar[idx]:.2f}", use_column_width=True)
