import os
import numpy as np
from pytriton.model_config import ModelConfig, Tensor
from pytriton.triton import Triton, TritonConfig
from nv_cloud_function_helpers.nvcf_container import helpers
import io
import tempfile


class PyTritonServer:
    """triton server for sample_container"""

    def __init__(self):
        self.logger = helpers.get_logger()
        self.model_name = "sample_container"
        self.flag_serialize_before_upload = False

    def _infer_fn(self, requests):
        responses = []
        for req in requests:
            # deal with header dict keys being lowerscale
            self.logger.info("getting request headers")
            request_parameters_dict = helpers._uppercase_dict_keys(
                req.parameters
            )
            self.logger.info("printing headers")
            for k in request_parameters_dict.keys():
                print(f"{k} : {request_parameters_dict.get(k, None)}")
            input_path = helpers.get_input_path(request_parameters_dict)
            output_path = helpers.get_output_path(request_parameters_dict)
            flag_uploaded = False
            self.logger.info(
                "getting request body values from inference request"
            )
            req_data = req.data
            self.logger.info("printing request body")
            for k in req_data.keys():
                print(f"{k} : {req_data.get(k, None)}")

            # get the asset id for the image
            # you can read it from the body if passed in as a part of the request
            # or read it from the header NVCF-FUNCTION-ASSET-IDS
            asset_ids = helpers.get_asset_ids(request_parameters_dict)
            image_asset_id = req_data.get("image", None)[0].decode("utf-8")
            # get the result upload url
            resultUploadUrl = req_data.get("resultUploadUrl", None)[0].decode(
                "utf-8"
            )
            self.logger.info("got values from inference request")
            # read the image from disk using image and input_path
            image = helpers.load_image(
                image_asset_id, input_path, has_transparency=False
            )
            self.logger.info("starting inference")
            image = image.rotate(180)
            self.logger.info("inference done")

            # for this example we will not be returning the image with the response
            # instead we will be uploading the image to a provided presigned upload url
            if resultUploadUrl == None:
                self.logger.info(
                    f"resultUploadUrl not available, not uploading resulting image"
                )
                flag_uploaded = False
            import pdb

            pdb.set_trace()
            if self.flag_serialize_before_upload:
                # this method saves the image to disk and uploads it to the provided url
                # so storage on disk is required
                self.logger.info("saving image to disk")

                with tempfile.TemporaryDirectory() as tmpdirname:
                    print("created temporary directory", tmpdirname)
                    image_path = os.path.join(tmpdirname, "image.jpg")
                    image.save(image_path, format="JPEG")
                    try:
                        headers = {"Content-Type": "image/jpeg"}
                        response = helpers.upload_file(
                            image_path, resultUploadUrl, headers
                        )
                    except Exception as e:
                        # Handle exception
                        response = None
                    if response is not None and response["status_code"] in (
                        200,
                        201,
                    ):
                        # Success, set uploaded flag
                        flag_uploaded = True
                    else:
                        self.logger.info(
                            f"failed to upload image to url {resultUploadUrl}"
                        )
            else:
                # this method saves the image to a byte array and uploads it to the provided url
                # so no storage on disk is required
                headers = {"Content-Type": "image/jpeg"}
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="JPEG")
                img_byte_arr = img_byte_arr.getvalue()
                try:
                    response = helpers.upload(
                        img_byte_arr, resultUploadUrl, headers
                    )
                except Exception as e:
                    # Handle exception
                    response = None
                if response is not None and response["status_code"] in (
                    200,
                    201,
                ):
                    # Success, set uploaded flag
                    flag_uploaded = True
                else:
                    self.logger.info(
                        f"failed to upload image to url {resultUploadUrl}"
                    )

            # return the image as a bytestring if it was not uploaded
            if not flag_uploaded:
                self.logger.info("returning image as bytestring")
                # encode_image_to_base64
                self.logger.info("encoding image to base64")
                image_encoded = helpers.encode_image_to_base64(
                    image=image, image_format="PNG"
                )

                # check image size and if greater, save; else return bytestring
                if len(image_encoded) < helpers.get_max_msg_size(
                    request_parameters_dict
                ):
                    # return image as bytestring
                    self.logger.info("returning image as bytestring")
                    responses.append(
                        {
                            "image_generated": np.array(
                                [image_encoded], dtype=np.bytes_
                            )
                        }
                    )
                else:
                    # save image to disk as image.png and return an empty numpy array
                    self.logger.info("saving prediction numpy array to disk")
                    # create output folder
                    if output_path is not None:
                        os.makedirs(output_path, exist_ok=True)
                    save_path = helpers.save_image_with_directory(
                        image=image, path=output_path, image_format="PNG"
                    )
                    self.logger.info("returning empty response")
                    responses.append(
                        {
                            "image_generated": np.array(
                                save_path, dtype=np.bytes_
                            )
                        }
                    )
            else:
                self.logger.info("returning empty response")
                responses.append(
                    {"image_generated": np.array("", dtype=np.bytes_)}
                )
        return responses

    def run(self):
        """run triton server"""
        with Triton(
            config=TritonConfig(
                allow_metrics=True,
                allow_gpu_metrics=True,
                allow_cpu_metrics=True,
                metrics_interval_ms=500,
                http_header_forward_pattern="(nvcf-.*|NVCF-.*)",
                strict_readiness=True,
                trace_config=[
                    "mode=opentelemetry",
                    "rate=1",
                    "level=TIMESTAMPS",
                    f"opentelemetry,resource=url={os.getenv('NVCF_TRACING_ENDPOINT_HTTP', 'http://localhost:4138/v1/traces')}",
                ],
                log_verbose=0,
            )
        ) as triton:
            triton.bind(
                model_name="sample_container",
                infer_func=self._infer_fn,
                inputs=[
                    Tensor(name="image", dtype=np.bytes_, shape=(-1,)),
                    Tensor(
                        name="resultUploadUrl", dtype=np.bytes_, shape=(-1,)
                    ),
                ],
                outputs=[
                    Tensor(name="image_generated", dtype=np.bytes_, shape=(1,))
                ],
                config=ModelConfig(batching=False),
            )
            triton.serve()


if __name__ == "__main__":
    server = PyTritonServer()
    server.run()
