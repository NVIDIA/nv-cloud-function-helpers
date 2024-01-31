## sample container

This is a sample container that showcases how to use nvcf helper functions in an inference container.

Steps:    
1. Build inference container: ```docker build -t sample_container .```
2. Run the inference container: ```docker run --gpus device=0 --rm -it --network host --ipc host -v $PWD/tests:/var/inf/inputAssets/ad8345e2-fada-11ed-be56-0242ac120002 -v $PWD/tests/output:/var/inf/response/ad8345e2-fada-11ed-be56-0242ac120002 sample_container```
4. Send a request to the inference server: ```python3 client.py```

Notice that we are mounting ```$PWD/tests``` at ```/var/inf/inputAssets/ad8345e2-fada-11ed-be56-0242ac120002``` and ```$PWD/tests/output``` at ```/var/inf/response/ad8345e2-fada-11ed-be56-0242ac120002``` to mock NVCF asset API behavior. Please read the client.py to better understand how the NVCF headers communicate the input paths, output paths, and asset id for the request.