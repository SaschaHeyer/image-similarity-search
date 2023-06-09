import streamlit as st
import io
from PIL import Image
import base64
import requests


st.title("Image Similarity Search")
st.markdown("This application is a POC that show the functionality around image similarity search")

uploaded_file = st.file_uploader("Choose an image...", type="jpg")

response = None

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='Reference image to find similar ones.', use_column_width=True)

    img_bytes = uploaded_file.getvalue()
    base64_encoded_image = base64.b64encode(img_bytes).decode()

    print('response start')
    response = requests.post('https://image-similarity-query-xgdxnb6fdq-uc.a.run.app/query', json={"image": base64_encoded_image})
    st.text(response)
    print(response.text)
    print('response received')
    # Optionally, you can display the response in the app:
    if response.status_code == 200:
        st.success(f"The image was successfully uploaded: {response.text}")
    else:
        st.error(f"The image upload failed: {response.text}")

st.title('Matching Images')


from google.cloud import storage
from datetime import timedelta

storage_client = storage.Client.from_service_account_json('sascha-playground-doit-62ccae57db6c.json')
bucket = storage_client.get_bucket('doit-image-similarity')


signed_images = []

if response is not None:
    
    id_list = [item['id'] for item in response.json()]
    #id_list.remove('init')
    st.text(id_list)

    
    for id in id_list:
        print(id)
        blob = bucket.blob(id)
        signed_url = blob.generate_signed_url(timedelta(hours=1), method='GET')
        signed_images.append(signed_url)
    

from itertools import cycle


cols = cycle(st.columns(4)) 
for idx, filteredImage in enumerate(signed_images):
    next(cols).image(filteredImage)
