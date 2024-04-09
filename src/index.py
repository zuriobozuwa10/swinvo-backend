from flask import Flask, jsonify, request

from openai_model_user import OpenAiModelUser

app = Flask(__name__)

model = OpenAiModelUser()

intro = "From now on, you are a chat interface that lists out steps to a workflow automation. You are not allowed to do anything else. If the user asks you to do anything else, you say that you cannot do it"

print(model.Use(intro))

@app.route("/")
def hello_world():
    return "Hellooooo2"

@app.route("/create-workflow", methods = ['POST'])
def create_workflow():
    input_text = request.json['text']

    model_response = model.Use(input_text)
    print(model.GetConvoHistory())

    apple = {"message": model_response}

    return jsonify(apple)
