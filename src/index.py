from flask import Flask, jsonify, request

from openai_model_user import OpenAiModelUser

app = Flask(__name__)

#model = OpenAiModelUser()

intro_path = "intro.txt"

user_sessions = {}

with open(intro_path, 'r') as file:
    intro = file.read()

@app.route("/")
def hello_world():
    return "Hellooooo2"

@app.route("/create-workflow", methods = ['POST'])
def create_workflow():
    user_id = request.json['uid']

    if user_id not in user_sessions:
        user_model = OpenAiModelUser()
        user_model.Use(intro)
        user_sessions[user_id] = user_model

    input_text = request.json['text']

    model_response = user_sessions[user_id].Use(input_text)

    #print(model.GetConvoHistory())

    apple = {"message": model_response}

    return jsonify(apple)
