import argparse
import numpy as np
from pytriton.client import ModelClient
import base64
from PIL import Image
from io import BytesIO
import os
import requests

DEFAULT_MAX_NVCF_MSG_SIZE = 50000000

model_name = "sample_container"
model_version = "1"
url = f"http://localhost:8000/v2/models/{model_name}/infer"


def encode_string(string_to_encode: str):
    s = np.array([string_to_encode])
    return np.char.encode(s, "utf-8")


def variable_to_numpy_array(variable, dtype):
    return np.array([variable], dtype=dtype)


headers = {
    "NVCF-REQID": "ad8345e2-fada-11ed-be56-0242ac120002",
    "NVCF-SUB": "<sub from the message>",
    "NVCF-NCAID": "<ncaId - NVIDIA Cloud Account ID from the message>",
    "NVCF-FUNCTION-NAME": "sdxl_txt2img",
    "NVCF-FUNCTION-ID": "c515b8c0-fada-11ed-be56-0242ac120002",
    "NVCF-ASSET-DIR": "/var/inf/inputAssets/ad8345e2-fada-11ed-be56-0242ac120002",
    "NVCF-LARGE-OUTPUT-DIR": "/var/inf/response/ad8345e2-fada-11ed-be56-0242ac120002",
    "NVCF-MAX-RESPONSE-SIZE-BYTES": str(DEFAULT_MAX_NVCF_MSG_SIZE),
}
data = {
    "id": "42",
    "inputs": [
        {
            "name": "image",
            "shape": [1],
            "datatype": "BYTES",
            "data": ["df034fb3-ec73-4d92-a190-d85d797ab5f0"],
        },
    ],
    "outputs": [{"name": "image_generated", "datatype": "BYTES", "shape": [1]}],
}
print(data)
response = requests.post(url, json=data, headers=headers)

if len(response.json().get("outputs")[0].get("data")[0]) < 512:
    print(
        "no image returned, check test/outputs for image returned through asset API"
    )
else:
    # Get the binary image data from the result_dict
    binary_image_data = response.json().get("outputs")[0].get("data")[0]

    # Decode the base64 string to bytes
    image_bytes = base64.b64decode(binary_image_data)

    # Create an in-memory binary stream from the decoded bytes
    image_stream = BytesIO(image_bytes)

    # Open the image using Pillow (PIL)
    image = Image.open(image_stream)

    # Specify the path where you want to save the image
    output_image_path = os.path.join("tests", "output", "image.png")

    # Save the image to disk
    image.save(output_image_path)

    # Close the image stream
    image_stream.close()

    print(f"Image saved to {output_image_path}")
