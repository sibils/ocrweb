# ocrweb - OCR service online

## Build and deploy the service

The core OCR functionaliy a python wrapper around tessearct.
The functionality is made available from a fastAPI python web service calling tesseract.
Tesseract and fastAPI application are embedded in a docker image.
```shell
# build the docker image
./scripts/docker.build

# run the docker image
./scripts/docker.run
```
To declare the OCR service as a regular service on a Debian GNU/Linux 11 (bullseye) platform, do
```shell

```




The fastAPI internal service is proxied
