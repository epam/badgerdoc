ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as build

# Installing necessary packages
RUN pip install tensorflow tensorflow_hub fastapi numpy uvicorn python-dotenv
WORKDIR /embeddings
# Downloading the TensorFlow embedding model
RUN python -c "import tensorflow_hub as hub; hub.load('https://www.kaggle.com/models/google/universal-sentence-encoder/frameworks/TensorFlow2/variations/qa/versions/2')"
RUN python -c "import tensorflow_hub as hub; hub.load('https://www.kaggle.com/models/google/universal-sentence-encoder/frameworks/TensorFlow2/variations/universal-sentence-encoder/versions/2')"

COPY embeddings embeddings
COPY .env ./
#COPY main.py /app/
#WORKDIR /app
CMD ["uvicorn", "embeddings.main:app", "--host", "0.0.0.0", "--port", "8080"]
EXPOSE 8080

#CMD ["python", "main.py"]
