import numpy as np
import base64
from PIL import Image
from io import BytesIO
import os
import requests
import boto3
from botocore.client import Config
import json
from pytriton.client import ModelClient
import argparse
import numpy as np
from pytriton.client import ModelClient
from PIL import Image
from io import BytesIO
import base64

# load aws creds from env
aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_endpoint_url = os.environ.get("AWS_ENDPOINT_URL")


def encode_string(string_to_encode: str):
    s = np.array([string_to_encode])
    return np.char.encode(s, "utf-8")


def variable_to_numpy_array(variable, dtype):
    return np.array([variable], dtype=dtype)


def gen_presigned_url():
    s3 = boto3.client(
        "s3",
        endpoint_url=aws_endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        config=Config(signature_version="s3v4"),
    )
    # Specify the bucket name and the object key
    bucket_name = "nvidia"
    object_key = "image.jpg"

    # Generate a pre-signed URL for uploading the object
    presigned_url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": bucket_name, "Key": object_key},
        ExpiresIn=3600,  # Expiration time in seconds (1 hour in this case)
    )

    print("Pre-signed URL for uploading: ", presigned_url)
    return presigned_url


with ModelClient("localhost", "sample_container", init_timeout_s=600) as client:
    input_asset_filename = (
        "df034fb3-ec73-4d92-a190-d85d797ab5f0"  # small enough to be returned
    )
    headers = {
        # added by NVCF Proxy
        "NVCF-REQID": "ad8345e2-fada-11ed-be56-0242ac120002",
        "NVCF-SUB": "<sub from the message>",
        "NVCF-NCAID": "<ncaId - NVIDIA Cloud Account ID from the message>",
        "NVCF-FUNCTION-NAME": "sample_container",
        "NVCF-FUNCTION-ID": "c515b8c0-fada-11ed-be56-0242ac120002",
        "NVCF-ASSET-DIR": "/var/inf/inputAssets/ad8345e2-fada-11ed-be56-0242ac120002",
        "NVCF-LARGE-OUTPUT-DIR": "/var/inf/response/ad8345e2-fada-11ed-be56-0242ac120002",
        "NVCF-MAX-RESPONSE-SIZE-BYTES": "5000000",
        # must be specified by client
        "NVCF-INPUT-ASSET-REFERENCES": f"{input_asset_filename},",
    }

    parameters = {}
    image = encode_string("df034fb3-ec73-4d92-a190-d85d797ab5f0")
    resultUploadUrl = encode_string(gen_presigned_url())
    result_dict = client.infer_sample(
        image=image,
        resultUploadUrl=resultUploadUrl,
        parameters=parameters,
        headers=headers,
    )

    print(result_dict)
    if len(result_dict.get("image_generated")) < 512:
        exit()

    # Get the binary image data from the result_dict
    binary_image_data = result_dict["image_generated"][0]

    # Decode the base64 string to bytes
    image_bytes = base64.b64decode(binary_image_data)

    # Create an in-memory binary stream from the decoded bytes
    image_stream = BytesIO(image_bytes)

    # Open the image using Pillow (PIL)
    image = Image.open(image_stream)

    # Specify the path where you want to save the image
    output_image_path = "output_image.png"

    # Save the image to disk
    image.save(output_image_path)

    # Close the image stream
    image_stream.close()

    print(f"Image saved to {output_image_path}")
