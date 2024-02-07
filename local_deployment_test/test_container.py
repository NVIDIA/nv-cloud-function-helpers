import urllib.parse
import json
import requests
import requests
import docker
import time
import subprocess
import click


# health endpoints
"""
GET v2/health/live

GET v2/health/ready

GET v2/models/${MODEL_NAME}[/versions/${MODEL_VERSION}]/ready
"""


class ContainerSmokeTest:
    default_port = 18080
    wait_iterations = 100

    def launch_container(self, image_name, container_port, command=None, volumes=None):
        docker_kwargs = {
            "image": image_name,
            "ports": {
                container_port: ("127.0.0.1", self.default_port),
            },
            "auto_remove": True,
        }

        if command:
            docker_kwargs.update({"command": command})

        if volumes:
            docker_kwargs.update({"volumes ": volumes})

        print(docker_kwargs)

        container = docker.from_env().containers.run(
            **docker_kwargs, device_requests=[docker.types.DeviceRequest(count=-1, capabilities=[["gpu"]])], detach=True
        )

        return container

    def check_http_health_endpoint(self, container, health_endpoint, seconds_to_wait_for_healthy=60):
        health_url = urllib.parse.urljoin(f"http://localhost:{self.default_port}", health_endpoint)

        print(f"Looking for health signal at {health_url}")

        health_success = False

        # Check if the health endpoint returns 200
        for _ in range(self.wait_iterations):
            try:
                response = requests.get(health_url)
                response.raise_for_status()
                if response.status_code == 200:
                    print(f"{health_url} returned 200 OK")
                    health_success = True
                    break
                else:
                    print(f"{health_url} returned {response.status_code}")
            except Exception as e:
                print(f"Found the following exception, but continuing... {e}")
            finally:
                pass

            time.sleep(seconds_to_wait_for_healthy // self.wait_iterations)

        if not health_success:
            raise Exception(
                "Health check did not complete successfully in time. "
                "Please refer to your container logs for troubleshooting "
                f"{container.logs()}"
            )
        else:
            print("Health Check succeed!")

    def test_http_inference(self, container, inference_endpoint, payload):
        inference_url = urllib.parse.urljoin(f"http://localhost:{self.default_port}", inference_endpoint)

        print(f"Sending payload to {inference_url}...")

        try:
            response = requests.post(inference_url, json=payload)
        except Exception as e:
            print(f"There was an error while sending the payload: {e}")
            if click.confirm("Would you like to see your containers logs?"):
                print(f"{container.logs()}")
            return False

        print(f"Here is the server's response: {response.json()}")

    def test_container(
        self,
        image_name,
        inference_endpoint,
        container_port,
        protocol,
        health_endpoint,
        seconds_to_wait_for_healthy,
    ):
        # grpc not implemented yet
        if protocol == "grpc":
            raise NotImplementedError("grpc container checking not implemented yet")

        container = None
        try:
            # Launch the container
            container = self.launch_container(
                image_name=image_name,
                container_port=container_port,
            )

            # Check if the health endpoints returns 200
            self.check_http_health_endpoint(
                container, health_endpoint, seconds_to_wait_for_healthy=seconds_to_wait_for_healthy
            )

            # test inference
            while True:
                if click.confirm("Do you want to test inference?"):
                    if inference_endpoint:
                        payload = click.edit("Please enter an http payload as a JSON dict")
                        try:
                            print(payload)
                            payload = json.loads(payload)
                        except json.decoder.JSONDecodeError as e:
                            print(f"There was an error decoding your message, please try again. {e}")
                            continue
                        self.test_http_inference(container, inference_endpoint, payload)
                    else:
                        print("Please specify --inference-endpoint when starting the test!")
                        break
                else:
                    break

        finally:
            if container:
                print("Shutting down container and cleaning up...")
                container.stop(timeout=5)


@click.command()
@click.option(
    "--image-name",
    prompt="What is the name of docker image?",
    help="the name of the server docker image",
)
@click.option(
    "--inference-endpoint",
    help="inference endpoint exposed by the server",
)
@click.option(
    "--container-port",
    default="8000",
    help="port that the server listening on. default is 8000",
)
@click.option(
    "--protocol",
    default="http",
    type=click.Choice(["http", "grpc"], case_sensitive=False),
    help="protocol that the server is running at. default is http. can be http or grpc",
)
@click.option(
    "--health-endpoint",
    default="/v2/health/ready",
    help="health endpoint exposed by the server, default is v2/health/ready",
)
@click.option(
    "--seconds-to-wait-for-healthy",
    default=600,
    help="how long to wait for the health endpoint to be ready, default is 600 seconds",
)
def main(
    image_name,
    inference_endpoint,
    container_port,
    protocol,
    health_endpoint,
    seconds_to_wait_for_healthy,
):
    # grpc not implemented yet
    if protocol == "grpc":
        raise NotImplementedError("grpc container checking not implemented yet")

    cst = ContainerSmokeTest()
    cst.test_container(
        image_name,
        inference_endpoint,
        container_port,
        protocol,
        health_endpoint,
        seconds_to_wait_for_healthy,
    )


if __name__ == "__main__":
    main()
