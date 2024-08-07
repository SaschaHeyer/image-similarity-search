import requests
import base64

# Function to encode an image file to base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

# Define the API endpoint
api_url = "http://0.0.0.0:8000/query"

# Path to the image you want to send
image_path = "/Users/sascha/Desktop/development/image-similarity-search/products/png/1a4117fbcf8144d5aedad35331fed3c0.png"

# Encode the image
encoded_image = encode_image_to_base64(image_path)

# Create the payload
payload = {
    "image": encoded_image,
    "threshold": 0.7,  # Optional, defined the similarity score threshold for images to be defined as similar
    "rerankerLimit": 5 # Optional, defines the number of vector matches passed to the multimodal re-ranker 
}

# Set the headers
headers = {
    "Content-Type": "application/json"
}

# Make the POST request
response = requests.post(api_url, json=payload, headers=headers)

# Print the response
if response.status_code == 200:
    print("Response from API:")
    print(response.json())
else:
    print(f"Failed to get a response. Status code: {response.status_code}")
    print(response.text)
