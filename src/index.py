from flask import Flask, jsonify, request
import requests
import os
from openai_model_user import OpenAiModelUser

app = Flask(__name__)

#model = OpenAiModelUser()

intro_path = "intro.txt"

# Store user chat sessions in a dictionary for now. TODO (ZO): Improve this.
# Resets after every deployment
user_sessions = {}

with open(intro_path, 'r') as file:
    intro = file.read()

@app.route("/")
def hello_world():
    return "Hellooooo2"

@app.route("/create-workflow", methods = ['POST'])
def create_workflow():

    print(user_sessions)

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

@app.route("/gmail-auth-callback")
def gmail_auth_callback():
    auth_code = request.args.get('code')
    client_id = os.environ.get('GMAIL_CLIENT_ID')
    client_secret = os.environ.get('GMAIL_CLIENT_SECRET')
    redirect_uri = 'https://spoon-app-rh8fm.ondigitalocean.app/gmail-auth-callback'
    token_url = 'https://oauth2.googleapis.com/token'

    print("AUTH CODE: " + auth_code)
    print("CLIENT ID: " + client_id)

    data = {
        'code': auth_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    response = requests.post(token_url, data)
    
    if response.status_code == 200:
        tokens = response.json()
        print(tokens)
    else:
        print ("BAD RESPONSE")

    

    return "Real s"

    

    

@app.route("/gmail-send-email", methods = ['GET', 'POST']) #??
def gmail_send_email():
    pass