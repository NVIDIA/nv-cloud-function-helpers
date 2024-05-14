# Image Asset Rotator Sample

This is a sample container that showcases how to use nvcf helper functions in an inference container.

It accepts an image and returns the image rotated 180 degrees.

Steps:    
1. Build inference container: ```docker build -t image_rotator_sample .```
2. Run the inference container: ```docker run --rm -it --network host --ipc host -v $PWD/client:/var/inf/inputAssets/ad8345e2-fada-11ed-be56-0242ac120002 -v $PWD/output:/var/inf/response/ad8345e2-fada-11ed-be56-0242ac120002 image_rotator_sample```
3. Send a request to the inference server: ```cd client && python3 client.py```

Notice that we are mounting ```$PWD/client``` at ```/var/inf/inputAssets/ad8345e2-fada-11ed-be56-0242ac120002``` and ```$PWD/output``` at ```/var/inf/response/ad8345e2-fada-11ed-be56-0242ac120002``` to mock NVCF asset API behavior. 
Please read the client.py to better understand how the NVCF headers communicate the input paths, output paths, and asset id for the request.