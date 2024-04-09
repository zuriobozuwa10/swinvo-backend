from flask import Flask, jsonify, request

from openai_model_user import OpenAiModelUser

app = Flask(__name__)

model = OpenAiModelUser()


intro_path = "intro.txt"

with open(intro_path, 'r') as file:
    intro = file.read()

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
