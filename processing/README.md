## Running via docker-compose

For local manual testing use docker-compose.

1. Set environment variables. They are mapped to package/processing/config.py
2. `docker-compose up --build . .`

Run a browser with an address http://0.0.0.0:8080/doc
There is an example of post-request. In minio create bucket, i.e. "annotation". Create there a folder "file" and put
document "train.pdf" from tests directory, accordingly post-request. Create in a bucket folder "ocr" and put here "
1.json" file from tests directory. Execute post-request. Review the results in the browser.

## Building via make

1 Set environment variables.

2a. Run `make build` for creating a docker image with a target build.

2b. Run make test for creating a docker image with a target test. It is using in a CI pipeline.

License: The default license for code repositories is: Apache 2.0 Read more [here] (./package/README.md)

# processing text merger

This microservice takes bordered boxes (bboxes) with words and bboxes-annotations then merges them.

## Example

__input__

- bbox_1: place: [1, 1, 40, 10], text: "word1 "
- bbox_2: place: [11, 1, 80, 10], text: "word2"
- bbox-annotation: place [1, 1, 80, 10], text: ""

__output__

- then, updated merged bbox-annotation is: place [1, 1, 80, 10], text: "word1 word2"

# How to run tests

You can read in `./tests/integration/readme.md`.
