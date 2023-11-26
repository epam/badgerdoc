FROM python:3.8 as build

# Installing necessary packages
RUN pip install tensorflow tensorflow_hub fastapi numpy
WORKDIR /embeddings
# Downloading the TensorFlow embedding model
RUN python -c "import tensorflow_hub as hub; hub.load('https://www.kaggle.com/models/google/universal-sentence-encoder/frameworks/TensorFlow2/variations/qa/versions/2')"
RUN python -c "import tensorflow_hub as hub; hub.load('https://www.kaggle.com/models/google/universal-sentence-encoder/frameworks/TensorFlow2/variations/universal-sentence-encoder/versions/2')"

COPY embeddings embeddings
#COPY main.py /app/
#WORKDIR /app
CMD uvicorn embeddings.main:app --host 0.0.0.0 --port 8080
EXPOSE 8080

#CMD ["python", "main.py"]
