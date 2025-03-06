# Simple fastapi application for non-LLM models Named Entity Recognition

## Description

This is very simple HTTP web server running on python fastapi and uvicorn. It accepts POST request with 4 post request parameters:

 - model_id: ID of the model to run
 - threshold: Threshold parameter for the NER model (used in gliner type models). Value should be float in range <0, 1>
 - labels: List of labels(entities) to search for in text
 - text: Text to process

Workflow of the server is simple:
 - You send POST request with json containing 4 mentioned parameters
 - Server checks if model with given ID already downloaded and initialized. If yes, it's retrieved from cache. If not, model is downloaded, initialized and cached. Which may take some time, therefore if it's first run with this model, request might time out.
 - Server runs model with other parameters from the request.
 - Wraps result generation (usually it's a list of dictionaries with found entities) into dict with "entities" key
 - Returns response to the client

## How to run

1. Make sure you have python>=3.12, pip and poetry>=2.0 installed
1. Install run dependencies with poetry in editable mode

    ```bash
    poetry install --no-root --only main
    ```

1. Project needs dependencies from artifactory base image specified in Dockerfile.  

    To run app locally you should also install 'tenant_dependency' from **lib/tenants** folder

1. Run uvicorn application

    ```bash
    uvicorn main:app --reload
    ```