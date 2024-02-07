import uuid
import gradio as gr
import traceback
import numpy as np
import requests


def infer(url,
          api_key,
          message,
          delay,
          ):

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        data = {
            "id": str(uuid.uuid4()),
            "inputs": [
                {
                    "name": "message",
                    "shape": [1],
                    "datatype": "BYTES",
                    "data": [message],
                },
                {
                    "name": "response_delay_in_seconds",
                    "shape": [1],
                    "datatype": "FP32",
                    "data": [delay]
                }
            ],
            "outputs": [
                {
                    "name": "echo",
                    "datatype": "BYTES",
                    "shape": [1],
                }
            ],
        }

        response = requests.post(url, json=data, headers=headers)

        print(response.text)

        return response.json()["outputs"][0]["data"][0]

    except Exception as e:
        print(traceback.format_exc(), flush=True)


if __name__ == "__main__":

    iface = gr.Interface(fn=infer,
                         inputs=[
                             gr.Textbox(label="url", value="http://192.168.2.101:8000/v2/models/echo/infer"),
                             gr.Textbox(label="api_key"),
                             gr.Textbox(label="message"),
                             gr.Slider(0.1, 10, value=1, step=0.1, label="Delay in seconds"),
                         ],
                         outputs=[gr.Text(label="Echoed message")],
                         title="ECHO Echo echo",
                         description="Sample App"
                         )
    iface.launch(server_name="0.0.0.0")
