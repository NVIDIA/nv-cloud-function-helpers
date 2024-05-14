import numpy as np
import base64
from PIL import Image
from io import BytesIO
import os
import requests

input_asset_filename = "df034fb3-ec73-4d92-a190-d85d797ab5f0"  # small enough to be returned
# input_asset_filename = "rg034fb3-ec73-4d92-a190-d85d797ab5f0"  # too big to be returned

url = f"http://localhost:8000/rotate_image"


def encode_string(string_to_encode: str):
    s = np.array([string_to_encode])
    return np.char.encode(s, "utf-8")


def variable_to_numpy_array(variable, dtype):
    return np.array([variable], dtype=dtype)


headers = {
    # added by NVCF Proxy
    "NVCF-REQID": "ad8345e2-fada-11ed-be56-0242ac120002",
    "NVCF-SUB": "<sub from the message>",
    "NVCF-NCAID": "<ncaId - NVIDIA Cloud Account ID from the message>",
    "NVCF-FUNCTION-NAME": "sdxl_txt2img",
    "NVCF-FUNCTION-ID": "c515b8c0-fada-11ed-be56-0242ac120002",
    "NVCF-ASSET-DIR": "/var/inf/inputAssets/ad8345e2-fada-11ed-be56-0242ac120002",
    "NVCF-LARGE-OUTPUT-DIR": "/var/inf/response/ad8345e2-fada-11ed-be56-0242ac120002",
    "NVCF-MAX-RESPONSE-SIZE-BYTES": "5000000",
    # must be specified by client
    "NVCF-INPUT-ASSET-REFERENCES": f"{input_asset_filename},",
}
data = {
    "inputs": [
        {
            "name": "image",
            "shape": [1],
            "datatype": "BYTES",
            "data": [input_asset_filename],
        },
    ],
    "outputs": [{"name": "image_generated", "datatype": "BYTES", "shape": [1]}],
}
print(data)
response = requests.post(url, json=data, headers=headers)

if len(response.json().get("outputs")[0].get("data")[0]) < 512:
    print(
        "no image returned, check `output/` for image returned through asset API"
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
    output_image_path = os.path.join("image.png")

    # Save the image to disk
    image.save(output_image_path)

    # Close the image stream
    image_stream.close()

    print(f"Image saved to {output_image_path}")
