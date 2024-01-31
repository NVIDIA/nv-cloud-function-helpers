import os
import numpy as np
from pytriton.model_config import ModelConfig, Tensor
from pytriton.triton import Triton, TritonConfig
from nv_cloud_function_helpers.nvcf_container import helpers
from PIL import Image


class PyTritonServer:
    """triton server for sample_container"""

    def __init__(self):
        self.logger = helpers.get_logger()
        self.model_name = "sample_container"

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

            self.logger.info("got values from inference request")
            # read the image from disk using image and input_path
            image = helpers.load_image(
                image_asset_id, input_path, has_transparency=False
            )
            self.logger.info("starting inference")
            # rotate the image 180 degrees, saving partial progress
            for i in range(1, 181):
                # rotate the image 1 degree
                temp_image = image.rotate(i)
                progress_scaled_to_100 = (i / 180) * 100
                # update partial response
                helpers.update_progress_file(
                    request_parameters=request_parameters_dict,
                    progress_value=progress_scaled_to_100,
                    partial_response={},
                )
            image = temp_image
            self.logger.info("inference done")

            # we can return the image through base64 encoded string
            # or drop it to disk to return as a presigned download URL
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
                    {"image_generated": np.empty(shape=[1], dtype=np.bytes_)}
                )
        return responses

    def run(self):
        """run triton server"""
        with Triton(
            config=TritonConfig(
                http_header_forward_pattern="nvcf-*",
                http_port=8000,
                grpc_port=8001,
                metrics_port=8002,
            )
        ) as triton:
            triton.bind(
                model_name="sample_container",
                infer_func=self._infer_fn,
                inputs=[
                    Tensor(name="image", dtype=np.bytes_, shape=(-1,)),
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
