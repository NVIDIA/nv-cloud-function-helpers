## sample container

This is a sample container that showcases how to use nvcf helper functions in an inference container.

Steps:    
1. Build inference container: ```docker build -t sample_container .```
2. Run the inference container: ```docker run --gpus all -it --rm --network host --ipc host sample_container```
3. ```docker run --gpus all -it --rm --network host -v $PWD/server/optimized:/workspace sdxl_txt2img-optimized-inference-server```
4. Send a request to the inference server: ```python3 client.py```
