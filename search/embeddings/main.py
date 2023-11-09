from flask import request
from flask import Flask
import tensorflow_hub as hub
import json
import numpy as np
import tensorflow as tf

class CustomEncoder(json.JSONEncoder):
    def encode(self, obj):
        return json.dumps(obj, default=lambda x: x.__dict__, ensure_ascii=False)


app = Flask(__name__)
app.json_encoder = CustomEncoder

embed_qa = hub.load("https://www.kaggle.com/models/google/universal-sentence-encoder/frameworks/TensorFlow2/variations/qa/versions/2")
embed = hub.load("https://www.kaggle.com/models/google/universal-sentence-encoder/frameworks/TensorFlow2/variations/universal-sentence-encoder/versions/2")
print("module loaded")


@app.route('/api/use', methods=['POST'])
def text_use():
    data = json.loads(request.data)
    texts = data.get('instances', None)
    if not texts:
        raise ValueError("invalid parameters")
    return {"predictions": np.array(embed(texts)).tolist()}


@app.route('/api/use-question', methods=['POST'])
def text_question():
    data = json.loads(request.data)
    query_text = data.get('text', None)
    if not query_text:
        raise ValueError("invalid parameters")
    query_embedding = embed_qa.signatures['question_encoder'](tf.constant([query_text]))['outputs'][0]

    return {"predictions": np.array(query_embedding).tolist()}


@app.route('/api/use-responses', methods=['POST'])
def text_response():
    data = json.loads(request.data)
    responses = data.get('responses', None)
    response_batch = [r['sentence'] for r in responses]
    context_batch = [c['context'] for c in responses]
    if not responses:
        raise ValueError("invalid parameters")
    encodings = embed_qa.signatures['response_encoder'](
        input=tf.constant(response_batch),
        context=tf.constant(context_batch)
    )
    ret = []
    for batch_index, batch in enumerate(response_batch):
        ret.append({"sentence": batch, "encodings":  np.array(encodings['outputs'][batch_index]).tolist()});

    return {"embedings": ret}


@app.errorhandler(ValueError)
def handle_bad_request(e):
    return 'invalid request parameters!', 400


if __name__ == '__main__':
    app.run('0.0.0.0', 3334, debug=False)
