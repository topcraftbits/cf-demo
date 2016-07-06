import os
import redis
import numpy as np
from flask import Flask, request
from PIL import Image, ImageOps
from keras.models import model_from_json
from keras.optimizers import RMSprop

app = Flask(__name__)
r = redis.StrictRedis(host="127.0.0.1", port=6379, db=0)

def get_model(redis):
    """Get model from redis and compile it."""
    model = model_from_json(redis.get("model").decode("UTF-8"))
    weights = redis.get("weights")
    with open("mnist_mlp_weights.h5", "wb") as f:
        f.write(weights)
    model.load_weights("mnist_mlp_weights.h5")
    os.remove("mnist_mlp_weights.h5")
    model.compile(loss="categorical_crossentropy",
              optimizer=RMSprop())
    return model

def convert_image(image):
    """Invert the image and then transform it to 1-d vector."""
    img = Image.open(image).convert("L")
    inverted_img = ImageOps.invert(img)
    data = np.asarray(inverted_img, dtype="int32")
    rescaled_data = (data/255).reshape(28,28)
    stacked_data = np.vstack([rescaled_data.reshape(-1)])
    return stacked_data

@app.route("/")
def main():
    return "Hello World!"

@app.route("/prediction", methods=["POST"])
def prediction():
    """
    curl -i -X POST -F files=@four_test.png http://127.0.0.1:5000/prediction
    """
    if request.method == "POST":
        image = request.files["files"]
        data = convert_image(image)
        model = get_model(r)
        prediction = model.predict_classes(data)
        return str(prediction[0])

if __name__ == "__main__":
    app.run(debug=True)