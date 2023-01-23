# ocrweb - OCR service online

## Build and deploy the service

The core OCR functionaliy a python wrapper around tessearct.
The functionality is made available from a fastAPI python web service calling tesseract.
Tesseract and fastAPI application are embedded in a docker image that you can build anr run with:

```shell
# build the docker image
./scripts/docker.build

# run the docker image
./scripts/docker.run
```
To declare the OCR service as a regular linux service on a Debian GNU/Linux 11 (bullseye) platform, do
```shell
cd ./system
systemctl enable $(pwd)/ocrweb.service
systemctl start ocrweb.service
```
The home page of the service is then available on http://localhost:8888/

You can then start, stop or look at the service status with
```shell
systemctl start ocrweb.service
systemctl status ocrweb.service
systemctl stop ocrweb.service
```

To config a caddy service that will make the ocrweb service available to the external world via http and https on default ports, do the following

