FROM python:3.8 as build

# Installing necessary packages
RUN pip install tensorflow tensorflow_hub flask numpy

# Downloading the TensorFlow embedding model
#RUN python -c "import tensorflow_hub as hub; hub.load('https://tfhub.dev/google/universal-sentence-encoder/4')"
RUN python -c "import tensorflow_hub as hub; hub.load('https://www.kaggle.com/models/google/universal-sentence-encoder/frameworks/TensorFlow2/variations/qa/versions/2')"
RUN python -c "import tensorflow_hub as hub; hub.load('https://www.kaggle.com/models/google/universal-sentence-encoder/frameworks/TensorFlow2/variations/universal-sentence-encoder/versions/2')"


COPY main.py /app/
WORKDIR /app
EXPOSE 3334

CMD ["python", "main.py"]