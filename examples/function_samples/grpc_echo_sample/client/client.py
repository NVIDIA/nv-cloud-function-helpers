import grpc
import gradio as gr
import traceback
import echo_pb2
import echo_pb2_grpc


def send_request(url,
                 token,
                 function_id,
                 function_version_id,
                 message
                 ):
    try:
        if token:
            with grpc.secure_channel(url, grpc.ssl_channel_credentials()) as channel:
                stub = echo_pb2_grpc.EchoStub(channel)

                metadata = [("function-id", function_id),  # required
                            ("function-version-id", function_version_id),  # optional
                            ("authorization", "Bearer " + token)]  # required

                response = stub.EchoMessage(echo_pb2.EchoRequest(message=message), metadata=metadata)

        else:  # enable running a simple test outside the NVCF environment.
            with grpc.insecure_channel(url) as channel:
                stub = echo_pb2_grpc.EchoStub(channel)
                response = stub.EchoMessage(echo_pb2.EchoRequest(message=message))

        return response.message

    except Exception as e:
        print(traceback.format_exc(), flush=True)


if __name__ == "__main__":
    iface = gr.Interface(fn=send_request,
                         inputs=[
                             gr.Textbox(label="url", value="192.168.2.101:8001"),
                             gr.Textbox(label="access_token"),
                             gr.Textbox(label="function_id"),
                             gr.Textbox(label="function_version_id"),
                             gr.Textbox(label="message"),
                         ],
                         outputs=[gr.Text(label="Echoed message")],
                         title="ECHO Echo echo",
                         description="Sample App"
                         )
    iface.launch(server_name="0.0.0.0")
