from flask import request, redirect
import flask
import requests
import os

import yaml

from openai_model_user import OpenAiModelUser
from database_accessor import DatabaseAccessor

app = flask.Flask(__name__)

database = DatabaseAccessor(os.environ.get('MONGO_DB_USER'), os.environ.get('MONGO_DB_PASSWORD'))

#model = OpenAiModelUser()

intro_path = "intro.txt"

# Store user chat sessions in a dictionary for now. TODO (ZO): Improve this.
# Resets after every deployment
user_chat_sessions = {}

# Used to associate an app (e.g gmail) integration with a swinvo account
state_tokens = {}

# Each token tuple: (access_token, refresh_token)
gmail_user_tokens = {}

with open(intro_path, 'r') as file:
    intro = file.read()

@app.route("/")
def hello_world():
    return "Hellooooo2"

@app.route("/create-workflow", methods = ['POST'])
def create_workflow():

    print(user_chat_sessions)

    user_id = request.json['uid']

    if user_id not in user_chat_sessions:
        user_model = OpenAiModelUser()
        user_model.Use(intro)
        user_chat_sessions[user_id] = user_model

    input_text = request.json['text']

    model_response = user_chat_sessions[user_id].Use(input_text)
    print(model_response)

    #print(model.GetConvoHistory())

    apple = {"message": model_response}

    return flask.jsonify(apple)


@app.route("/check-gmail-auth", methods = ['POST'])
def check_gmail_auth():
    user_id = request.json['uid']

    gmail_is_authed = database.CheckUserGmailAuth(user_id)

    gmail_auth_dict = {}

    if gmail_is_authed:
        gmail_auth_dict["gmail_auth"] = True
    else:
        gmail_auth_dict["gmail_auth"] = False

    return flask.jsonify(gmail_auth_dict)


@app.route("/auth-session", methods = ['POST'])
def auth_session():
    state = request.json['state']
    user_id = request.json['uid']
    if user_id != "N/A":
        state_tokens[state] = user_id
    else:
        print("NO USER ID!")
        flask.abort(400, "Error: no user ID received.")

    print(state_tokens)

    return ''


@app.route("/gmail-auth-callback")
def gmail_auth_callback():
    auth_code = request.args.get('code')
    client_id = os.environ.get('GMAIL_CLIENT_ID')
    client_secret = os.environ.get('GMAIL_CLIENT_SECRET')
    redirect_uri = 'https://auth.swinvo.com/gmail-auth-callback'
    token_url = 'https://oauth2.googleapis.com/token'

    if auth_code and client_id:
        print("AUTH CODE: " + auth_code)
        print("CLIENT ID: " + client_id)

    data = {
        'code': auth_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    state = request.args.get('state')

    if state in state_tokens:
        user_id = state_tokens[state]
    else:
        print('Unknown state: ' + state + ' . Aborting')
        flask.abort(400, 'User state unknown')

    response = requests.post(token_url, data)
    
    if response.status_code == 200:
        tokens = response.json()
        gmail_user_tokens[user_id] = (tokens.get('access_token'), tokens.get('refresh_token'))
        print(tokens)
        result = database.AddUserGmailAuth( user_id, tokens.get('access_token'), tokens.get('refresh_token') )
        if result is False:
            flask.abort(500, "FAILED TO ADD USER AUTH TOKENS TO DATABASE")

    else:
        print ("BAD RESPONSE")

    return redirect("https://app.swinvo.com")


@app.route("/check-gmail-permission", methods = ['GET', 'POST']) #??
def check_gmail_permission():
    pass

@app.route("/gmail-send-email", methods = ['GET', 'POST']) #??
def gmail_send_email():
    pass


@app.route("/debug-print")
def debug_print():
    print(user_chat_sessions)
    print(state_tokens)
    print(gmail_user_tokens)
    return ''

@app.route("/debug-endpoint-1")
def debug_endpoint_1():
    print("ENDPOINT 1 REACHED")
    return ''

@app.route("/debug-endpoint-2")
def debug_endpoint_2():
    print("ENDPOINT 2 REACHED")
    return ''