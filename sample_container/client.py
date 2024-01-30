import argparse
import numpy as np
from pytriton.client import ModelClient
import base64
from PIL import Image
from io import BytesIO


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default="localhost",
        help=(
            "Url to Triton server (ex. grpc://localhost:8001)."
            "HTTP protocol with default port is used if parameter is not provided"
        ),
        required=False,
    )
    parser.add_argument(
        "--init-timeout-s",
        type=float,
        default=600.0,
        help="Server and model ready state timeout in seconds",
        required=False,
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of requests per client.",
        required=False,
    )
    parser.add_argument(
        "--results-path",
        type=str,
        default="results",
        help="Path to folder where images should be stored.",
        required=False,
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()

    with ModelClient(
        args.url, "sdxl_txt2img", init_timeout_s=args.init_timeout_s
    ) as client:

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
        }

        parameters = {}
        # prompt = encode_string("A picture of a shaggy unkempt jack russel terrier")
        prompts = map(
            encode_string,
            [
                "A picture of a shaggy unkempt jack russel terrier",
                "Jack russel is standing on a red box",
            ],
        )
        prompts = np.concatenate(list(prompts))
        prompt_weights = np.array([1.0, 1.0], dtype=np.float32)
        # image = encode_string("0dae35f2-113e-4a7c-bd52-7f3c1b6e08eb")

        result_dict = client.infer_sample(
            prompts=prompts,
            prompt_weights=prompt_weights,
            parameters=parameters,
            headers=headers,
        )

        print(result_dict)
        if len(result_dict.get("image_generated")[0]) < 512:
            print("exiting")
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


if __name__ == "__main__":
    main()
