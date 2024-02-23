import numpy as np
import base64
from PIL import Image
from io import BytesIO
import os
import requests
import boto3

# Set up the S3 client to use LocalStack
s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',  # Adjust the port as per your LocalStack configuration
    aws_access_key_id='dummy-access-key',              # These are test credentials since LocalStack doesn't require real AWS credentials
    aws_secret_access_key='dummy-secret-key',
)

bucket_name = 'b-strap-predictions'
object_key = 'image.jpg'

presigned_url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': bucket_name, 'Key': object_key},
    ExpiresIn=36000  # Adjust the expiration time as per your requirement
)

print("Presigned URL:", presigned_url)

input_asset_filename = (
    "df034fb3-ec73-4d92-a190-d85d797ab5f0"  # small enough to be returned
)
# input_asset_filename = "rg034fb3-ec73-4d92-a190-d85d797ab5f0"  # too big to be returned

model_name = "sample_container"
model_version = "1"
url = f"http://localhost:8000/v2/models/{model_name}/infer"


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
        {
            "name": "resultUploadUrl",
            "shape": [1],
            "datatype": "BYTES",
            "data": [presigned_url],
        }
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
