import json

import sseclient
import gradio as gr
import traceback
import requests


def infer(
    url,
    api_key,
    message,
):
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "text/event-stream",
        }
        data = {
            "new_inputs": message,
        }

        response = requests.post(
            url,
            json=data,
            headers=headers,
            stream=True,
        )

        output = []
        for event in sseclient.SSEClient(response).events():
            output.append(json.loads(event.data)["response"])

        return "".join(output)

    except Exception as e:
        print(traceback.format_exc(), flush=True)


if __name__ == "__main__":
    iface = gr.Interface(
        fn=infer,
        inputs=[
            gr.Textbox(
                label="url",
                value="http://192.168.2.101:8000/v2/models/DialoGPT/generate_stream",
            ),
            gr.Textbox(label="api_key"),
            gr.Textbox(label="message", value="hello there"),
        ],
        outputs=[gr.Text(label="Response")],
        title="Chatbot",
        description="Sample App",
    )
    iface.launch(server_name="0.0.0.0")
