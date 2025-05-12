import os
import io
import re
import base64
import json
import sys
import logging
import codecs
import numpy as np
from PIL import Image
import requests

DEFAULT_MAX_NVCF_MSG_SIZE = 5 * 1000 * 1000  # 5MB
IMAGE_FORMAT = "JPEG"
IMAGE_QUALITY = 90

b64_pattern = re.compile(
    "^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$"
)

def upload_file(filename, url, headers, timeout=30):
    """
    Upload a file.

    Returns a dictionary containing a "status_code" and "response".

    A 200 or 201 status code will indicate a success.

    Example Usage:
        headers = { "Content-Type": "image/jpg" }
        try:
            reponse = upload.upload_file("image.jpg", some_s3_url, headers)
        except:
            # Handle exception
            response = None

        if response is not None and response["status_code"] in (200, 201):
            # Success
        else:
            # Failure
    """
    with open(filename, "rb") as _f:
        response = upload(_f, url, headers, timeout)

    return response

def upload(stream, url, headers, timeout=30):
    """
    Upload file/byte stream to S3.

    Returns a dictionary containing a "status_code" and "response".

    A 200 or 201 status code will indicate a success.

    Example Usage:
        headers = { "Content-Type": "image/jpg" }
        try:
            with open("image.jpg", "rb") as f:
                response = upload.upload(_f, some_s3_url, headers)
        except:
            # Handle exception
            response = None

        if response is not None and response["status_code"] in (200, 201):
            # Success
        else:
            # Failure
    """
    response = requests.put(url, headers=headers, data=stream, timeout=timeout)

    return {
        "status_code": response.status_code,
        "response": response.text,
    }

def _uppercase_dict_keys(d: dict) -> dict:
    """
    Converts all keys in a dictionary to upper case
    :param d: the target dictionary
    :return:
    """
    return {k.upper(): v for k, v in d.items()}


def get_logger() -> logging.Logger:
    """
    gets a Logger that logs in a format compatible with NVCF
    :return: logging.Logger
    """
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [INFERENCE] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger(__name__)
    return logger


def update_progress_file(
    request_parameters: dict, progress_value: int, partial_response: dict = {}
):
    """
    A function that creates a file in the format NVCF expects to report process of a long-running function
    :param request_parameters: a dict of the parameters passed to the function
    :param progress_value: an integer value from 0 to 100 that describes the progress currently is
    :param partial_response: an optional dict of information to pass
    :return:
    """
    p = get_output_path(request_parameters)
    structure = {
        "id": get_request_id(request_parameters),
        "progress": progress_value,
    }

    structure.update({"partialResponse": partial_response})

    with open(os.path.join(p, "progress"), "w") as outfile:
        # Write the dictionary to the file in JSON format
        json.dump(structure, outfile)


def get_scalar_inputs(request, pairs: list) -> list:
    """
    A function built for use within the Triton Inference Server Python-backend
    that converts tensor request object into numpy values or default values
    :param request: Triton request Tensor object
    :param pairs: list of tuple key/default value or single key
    :return:
    """
    import triton_python_backend_utils as pb_utils  # only available inside Triton container

    inputs = []
    for p in pairs:
        # split pair into key and value
        if len(p) == 2:
            k, v = p
        elif len(p) == 1:
            # if only one value is given, treat as a key
            k, v = p[0], None
        else:
            raise ValueError(f"Incorrect pair (f{p}) was passed to get input")

        input = pb_utils.get_input_tensor_by_name(request, k)
        if input is None:
            # set value as default
            input = v
        else:
            # get numpy value
            input = input.as_numpy().item()

        # handle byte input
        if isinstance(input, bytes):
            input = codecs.decode(input, "utf-8", "ignore")

        inputs.append(input)
    return inputs


def get_output_path(request_parameters: dict) -> str:
    """
    Gets the storage location (file path)
    to save a large generated output assets to be retrieved by the client (NVCF-LARGE-OUTPUT-DIR)
    from the function invocation message
    :param request_parameters: a dict of the parameters passed to the function
    :return: asset output path string
    """
    request_parameters = _uppercase_dict_keys(request_parameters)
    request_id = get_request_id(request_parameters)
    output_path = request_parameters.get(
        "NVCF-LARGE-OUTPUT-DIR", f"/var/inf/response/{request_id}"
    )
    return output_path


def get_input_path(request_parameters: dict) -> str:
    """
    Gets the storage location (file path) where large input assets sent to the function (NVCF-ASSET-DIR)
    from the function invocation message
    :param request_parameters: a dict of the parameters passed to the function
    :return: asset input path string
    """
    request_parameters = _uppercase_dict_keys(request_parameters)
    request_id = get_request_id(request_parameters)
    input_assets_path_base = request_parameters.get(
        "NVCF-ASSET-DIR", f"/var/inf/inputAssets/{request_id}"
    )
    return input_assets_path_base


def get_max_msg_size(request_parameters: dict) -> int:
    """
    Gets the maximum size in bytes of data
    that can be returned as part of an HTTP response of the function (NVCF-MAX-RESPONSE-SIZE-BYTES)
    from the function invocation message
    :param request_parameters: a dict of the parameters passed to the function
    :return: max returned bytes size in int
    """
    request_parameters = _uppercase_dict_keys(request_parameters)
    max_response_size = request_parameters.get("NVCF-MAX-RESPONSE-SIZE-BYTES")
    if max_response_size is None:
        l = get_logger()
        l.warning(
            "Could not find 'NVCF-MAX-RESPONSE-SIZE-BYTES' in request parameters "
            f"defaulting to {DEFAULT_MAX_NVCF_MSG_SIZE}!"
        )
        max_response_size = DEFAULT_MAX_NVCF_MSG_SIZE

    return int(max_response_size)


def get_nca_id(request_parameters: dict) -> str:
    """
    Get the ncaId of the invocation (NVIDIA Cloud Account ID) from the function invocation message
    :param request_parameters: a dict of the parameters passed to the function
    :return: ncaId string
    """
    request_parameters = _uppercase_dict_keys(request_parameters)
    return request_parameters.get("NVCF-NCAID", "")


def get_request_id(request_parameters: dict) -> str:
    """
    Get the reqId of the invocation (NVCF-REQID) from the function invocation message
    :param request_parameters: a dict of the parameters passed to the function
    :return: request id string
    """
    request_parameters = _uppercase_dict_keys(request_parameters)
    return request_parameters.get("NVCF-REQID", "")


def get_asset_ids(request_parameters: dict) -> list:
    """
    Get the asset_ids of the invocation (NVCF-FUNCTION-ASSET-IDS) from the function invocation message
    :param request_parameters: a dict of the parameters passed to the function
    :return: list of asset ids
    """
    request_parameters = _uppercase_dict_keys(request_parameters)
    s = request_parameters.get("NVCF-FUNCTION-ASSET-IDS", "")
    ids = s.split(",")
    return ids


def get_properties_sub(request_parameters: dict) -> str:
    """
    Get the sub properties of the invocation of the invocation (NVCF-SUB) from the function invocation message
    :param request_parameters: a dict of the parameters passed to the function
    :return: sub properties string
    """
    request_parameters = _uppercase_dict_keys(request_parameters)
    return request_parameters.get("NVCF-SUB", "")


def get_function_id(request_parameters: dict) -> str:
    """
    Get the function ID of the invocation (NVCF-FUNCTION-ID) from the function invocation message
    :param request_parameters: a dict of the parameters passed to a function
    :return: function ID str
    """
    request_parameters = _uppercase_dict_keys(request_parameters)
    return request_parameters.get("NVCF-FUNCTION-ID", "")


def get_function_name(request_parameters: dict) -> str:
    """
    Get the function name (NVCF-FUNCTION-NAME) from the function invocation message
    :param request_parameters: a dict of the parameters passed to a function
    :return: function name string
    """
    request_parameters = _uppercase_dict_keys(request_parameters)
    return request_parameters.get("NVCF-FUNCTION-ID", "")


def get_config_value(value_name: str, model_config: dict = None) -> str:
    """
    returns a value from Triton's model config or from environment variable with the priority given to the environment
    """
    if model_config is None:
        return os.environ[value_name]
    else:
        return os.environ.get(
            value_name, model_config["parameters"][value_name]["string_value"]
        )


def load_npz(input_str: str, root_dir: str, array_name: str):
    """
    Loads an nzp from a path
    :param input_str: path to npz
    :param root_dir: directory where asset are saved
    :return: a numpy array
    """
    if os.path.exists(os.path.join(root_dir, input_str)):
        try:
            data = np.load(os.path.join(root_dir, input_str))
            return data[array_name]
        except Exception as e:
            raise Exception(
                f"{input_str} was not a file path of an npz file. {e}"
            )
    else:
        raise Exception(f"Unsure what {input_str} is!")


def load_image(input_str: str, root_dir: str, has_transparency: bool = False):
    """
    Loads an image from a b64 string or from a path
    :param input_str: b64 string or path to image
    :param root_dir: directory where images are saved
    :param has_transparency: if the alpha channel should be kept.
    :return: a PIL Image
    """
    if os.path.exists(os.path.join(root_dir, input_str)):
        # image exists in path
        try:
            i = Image.open(os.path.join(root_dir, input_str))
        except Exception as e:
            raise Exception(f"{input_str} was not a file path of an image. {e}")
    elif b64_pattern.match(input_str):
        # image might be a b64 string
        try:
            i = Image.open(
                io.BytesIO(base64.decodebytes(bytes(input_str, "utf-8")))
            )
        except Exception as e:
            raise Exception(
                f"{input_str} was not a b64 encoded image string. {e}"
            )
    else:
        raise Exception(f"Unsure what {input_str} is!")

    if has_transparency:
        return i.convert("RGBA")
    else:
        return i.convert("RGB")


def encode_bytes_base64_to_str(b: bytes) -> bytes:
    return base64.b64encode(b)


def encode_image_to_base64(
    image: Image, image_format: str = "JPEG", image_quality: int = IMAGE_QUALITY
):
    """
    accepts an PIL Image and returns a base64 encoded representation of image
    """
    raw_bytes = io.BytesIO()
    if image_format == "JPEG":
        image.save(
            raw_bytes, image_format, quality=image_quality, optimize=True
        )
    elif image_format == "PNG":
        image.save(raw_bytes, image_format, optimize=True)
    else:
        image.save(raw_bytes, image_format)
    raw_bytes.seek(0)  # return to the start of the buffer
    return encode_bytes_base64_to_str(raw_bytes.read())


def decode_base64_str_to_bytes(base64_str: str):
    return io.BytesIO(base64.decodebytes(base64_str))


def decode_base64_to_image(base64_str: str, has_transparency: bool = False):
    """
    accepts base64 encoded representation of image and returns PIL Image
    :param base64_str: a string of image file bytes encoded in base64
    :param has_transparency: if the alpha channel should be kept.
    :return: a PIL Image
    """
    i = Image.open(decode_base64_str_to_bytes(base64_str))
    if has_transparency:
        return i.convert("RGBA")
    else:
        return i.convert("RGB")


def save_image_with_directory(
    image: Image,
    path: str = "",
    image_format: str = "JPEG",
    image_quality: int = IMAGE_QUALITY,
):
    """
    Saves an image at the specified path, creating any directories that do not exist.
    """
    # Make sure the directory and parent directories exist
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    if image_format == "JPEG":
        extension = "jpg"
    elif image_format == "PNG":
        extension = "png"
    else:
        raise ValueError(
            "Unexpected image format {}. Currently only JPEG or PNG is supported!"
        )

    save_path = os.path.join(path, f"image.{extension}")
    if image_format == "JPEG":
        image.save(
            save_path, image_format, quality=image_quality, optimize=True
        )
    else:
        image.save(save_path, image_format)
    return save_path


def get_secrets() -> dict:
    """
    Reads secrets from the secrets.json file located at /var/secrets/secrets.json.
    The secrets file should be a JSON file containing key-value pairs.

    Documentation: https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/secrets.html
    
    Returns:
        dict: A dictionary containing the secrets
        
    Raises:
        FileNotFoundError: If the secrets file doesn't exist
        json.JSONDecodeError: If the secrets file contains invalid JSON
    """
    try:
        with open(SECRETS_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Secrets file not found at {SECRETS_PATH}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in secrets file: {str(e)}", e.doc, e.pos)

