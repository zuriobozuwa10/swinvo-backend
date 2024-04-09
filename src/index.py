from flask import Flask, jsonify, request

from openai_model_user import OpenAiModelUser

app = Flask(__name__)

model = OpenAiModelUser()

intro = "From now on, you are a chat interface that lists out steps to a workflow automation. You are not allowed to do anything else. If I ask you to do anything else, you say 'Sorry, i can only create workflow automations'. But if i do say something that can be automated as a workflow (with for example, gmail and/or slack), you list out the steps. You are not allowed to suggest any external companies, because you are part of the backend for my startup's product. Please respond with 'Sure, i understand. START.' ."

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
