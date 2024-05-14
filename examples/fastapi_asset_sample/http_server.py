import os
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, status, Request
from nv_cloud_function_helpers.nvcf_container import helpers


app = FastAPI()
logger = helpers.get_logger()


class HealthCheck(BaseModel):
    status: str = "OK"


@app.get("/health", tags=["healthcheck"], summary="Perform a Health Check",
         response_description="Return HTTP Status Code 200 (OK)", status_code=status.HTTP_200_OK,
         response_model=HealthCheck)
def get_health() -> HealthCheck:
    return HealthCheck(status="OK")


@app.post("/rotate_image")
async def rotate(request: Request):
    body = await request.json()
    response = dict()

    logger.info("getting request headers")
    request_parameters_dict = helpers._uppercase_dict_keys(
        request.headers
    )

    logger.info("printing headers")
    for k in request_parameters_dict.keys():
        print(f"{k} : {request_parameters_dict.get(k, None)}")
    input_path = helpers.get_input_path(request_parameters_dict)
    output_path = helpers.get_output_path(request_parameters_dict)

    logger.info(
        "getting request body values from inference request"
    )
    req_data = request
    logger.info("printing request body")
    for k in req_data.keys():
        print(f"{k} : {req_data.get(k, None)}")

    # get the asset id for the image
    # you can read it from the body if passed in as a part of the request
    # or read it from the header NVCF-FUNCTION-ASSET-IDS
    asset_ids = helpers.get_asset_ids(request_parameters_dict)
    image_asset_id = body["image"]

    logger.info("got values from inference request")
    # read the image from disk using image and input_path
    image = helpers.load_image(
        image_asset_id, input_path, has_transparency=False
    )
    logger.info("starting inference")
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
    logger.info("inference done")

    # we can return the image through base64 encoded string
    # or drop it to disk to return as a presigned download URL
    # encode_image_to_base64
    logger.info("encoding image to base64")
    image_encoded = helpers.encode_image_to_base64(
        image=image, image_format="PNG"
    )

    # check image size and if greater, save; else return bytestring
    if len(image_encoded) < helpers.get_max_msg_size(
            request_parameters_dict
    ):
        # return image as bytestring
        logger.info("returning image as bytestring")
        response["image_generated"] = image_encoded
    else:
        # save image to disk as image.png and return an empty numpy array
        logger.info("saving prediction numpy array to disk")
        # create output folder
        if output_path is not None:
            os.makedirs(output_path, exist_ok=True)
        save_path = helpers.save_image_with_directory(
            image=image, path=output_path, image_format="PNG"
        )
        logger.info("returning empty response")
        response["image_generated"] = image_encoded

    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
