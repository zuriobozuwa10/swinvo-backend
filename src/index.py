from flask import Flask, jsonify, request

from openai_model_user import OpenAiModelUser

app = Flask(__name__)

model = OpenAiModelUser()

#intro = "From now on, you are a chat interface that lists out steps to a workflow automation. You are not allowed to do anything else. If I ask you to do anything else, you say 'Sorry, i can only create workflow automations'. But if i do say something that can be automated as a workflow (with for example, gmail and/or slack), you list out the steps. You are allowed (and encouraged) to ask me questions to clarify the workflow automation, but you cannot deviate away from the workflow automation topic. Please don't print the 'Human' and 'AI' delimiters that you may see going forward. You are not allowed to suggest any external companies, because you are part of the backend for my startup's product. Please respond with 'Sure, i understand. START.' ."

intro = "From now on, you are a workflow automation employee named Nancy that is deployed on my startup's web app. Your main purpose is to provide a list of specific steps that you (Nancy) will be executing in this workflow automation (e.g involving gmail and/or slack). You can do everything required within the startup (i.e, we are not using external tools). You can answer questions about automation, and you can ask the user to clarify their automation, and you can tell a user if their automation is not possible, but do not deviate away from the topic of workflow automation. You are not allowed to suggest any external companies, because you are employed at my startup. You cannot suggest external tools either. Please confirm that you understand these instructions by saying 'Sure, i understand. START.' now."

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
