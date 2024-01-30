import os
import numpy as np
from pytriton.model_config import ModelConfig, Tensor
from pytriton.triton import Triton, TritonConfig
from nv_cloud_function_helpers.nvcf_container import helpers


class PyTritonServer:
    """triton server for sample_container"""

    @staticmethod
    def numpy_array_to_variable(numpy_array):
        """Convert received values into actual values."""
        if not isinstance(numpy_array, np.ndarray):
            return numpy_array

        if numpy_array.size == 2 and numpy_array.shape == (1, 2):
            # If the array contains two elements and has shape (1, 2), return them as a tuple
            value = tuple(numpy_array[0])
        elif numpy_array.size != 1:
            raise ValueError("Input array must have a single element")
        else:
            value = numpy_array.item()

            if numpy_array.dtype.kind in ("S", "O"):
                # If it's a binary string, decode it to a regular string
                value = value.decode("utf-8")

        return value

    def __init__(self):
        self.logger = helpers.get_logger()
        self.model_name = "sample_container"

    def _infer_fn(self, requests):
        responses = []
        for req in requests:
            # deal with header dict keys being lowerscale
            request_parameters_dict = PyTritonServer.uppercase_keys(
                req.parameters
            )
            input_path = helpers.get_input_path(request_parameters_dict)
            output_path = helpers.get_output_path(request_parameters_dict)

            self.logger.info("getting values from inference request")
            req_data = req.data
            # get the asset id for the image
            asset_ids = helpers.get_asset_ids(request_parameters_dict)
            prompts = req_data.get("image", None)
            self.logger.info("got values from inference request")
            # read the image from disk using image nad input_path
            image = helpers.load_image(image, input_path, has_transparency=False)
            self.logger.info("starting inference")
            # rotate the image 180 degrees, saving partial progress
            #encode_image_to_base64
            #save_image_with_directory
            # create output folder
            if output_path is not None:
                os.makedirs(output_path, exist_ok=True)

            self.logger.info("inference done")
            # resize image if it needs to be resized

            image_encoded = helpers.encode_image_to_base64(
                image, image_format="PNG"
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
                self.logger.info("saving prediction numpy array to disk")
                image.save(os.path.join(output_path, "image.png"))
                self.logger.info("returning empty response")
                responses.append(
                    {"image_generated": np.empty(shape=[1], dtype=np.bytes_)}
                )
        return responses

    def run(self):
        """run triton server"""
        with Triton(
            config=TritonConfig(
                http_header_forward_pattern="NVCF-*",
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
