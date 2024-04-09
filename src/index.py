from flask import Flask, jsonify, request

from openai_model_user import OpenAiModelUser

app = Flask(__name__)

model = OpenAiModelUser()

@app.route("/")
def hello_world():
    return "Hellooooo2"

@app.route("/create-workflow", methods = ['POST'])
def create_workflow():
    input_text = request.json['text']
    print(input_text)

    model_response = OpenAiModelUser.Use(input_text)
    apple = {"message": model_response}
    return jsonify(apple)
