import time
import numpy as np
import triton_python_backend_utils as pb_utils

from nvcf_helper_functions import helpers, image_encoding

DEFAULT_DELAY = 0.1


class TritonPythonModel:
    def initialize(self, args):
        pass

    def execute(self, requests):
        responses = []
        for request in requests:
            [
                message,
                delay,
            ] = helpers.get_scalar_inputs(
                request,
                [
                    ["message"],
                    ["response_delay_in_seconds", DEFAULT_DELAY],
                ],
            )

            time.sleep(int(delay))

            inference_response = pb_utils.InferenceResponse(
                output_tensors=[pb_utils.Tensor("echo", np.array(message).astype(np.bytes_))]
            )

            responses.append(inference_response)
        return responses

    def finalize(self):
        pass
