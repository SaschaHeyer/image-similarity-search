import os
import requests
import pandas as pd
from urllib.parse import urlparse
from google.cloud import storage
import logging

# Initialize a Google Cloud Storage client
storage_client = storage.Client()

# Define your bucket name here
bucket_name = 'doit-image-similarity'
bucket = storage_client.get_bucket(bucket_name)

# Set up logging
logging.basicConfig(filename='download_log.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

# Read the CSV file into a pandas dataframe
df = pd.read_csv('product_images.csv')

# Function to download and save the image
def download_image(row):
    url = row['online_image']

    # Skip if the URL is NaN
    if pd.isna(url):
        logging.info(f"Skipping due to NaN URL")
        return

    # Parse the URL to get the original filename
    path = urlparse(url).path
    filename = path.split('/')[-1]

    response = requests.get(url)
    
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)

        # Upload the file to GCS
        blob = bucket.blob('images/' + filename)
        blob.upload_from_filename(filename)

        logging.info(f"{filename} downloaded and uploaded to {bucket_name}.")

        # remove the file from local after uploading
        os.remove(filename)
        
    else:
        logging.error(f"Failed to download image from URL: {url}")

# Apply the function to each row in your dataframe
df.apply(download_image, axis=1)
