from flask import request, redirect, session
import flask
import requests

import os
import subprocess

import yaml

import random, string

from openai_model_user import OpenAiModelUser
from database_accessor import DatabaseAccessor

app = flask.Flask(__name__)

app.secret_key = 'iu4g87g23bi329032hr23'

database = DatabaseAccessor(os.environ.get('MONGO_DB_USER'), os.environ.get('MONGO_DB_PASSWORD'))

#model = OpenAiModelUser()

intro_path = "intro2.txt"

# Store user chat sessions in a dictionary for now. TODO (ZO): Improve this.
# Resets after every deployment
user_chat_sessions = {}

# Used to associate an app (e.g gmail) integration with a swinvo account
state_tokens = {}

# Each token tuple: (access_token, refresh_token)
gmail_user_tokens = {}

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

with open(intro_path, 'r') as file:
    intro = file.read()

# Save workflow


@app.route("/")
def hello_world():
    return "Hellooooo2"

@app.route("/test-session")
def test_session():
    if 'visits' in session:
        session['visits'] = session.get('visits') + 1  # Increment the number of visits
    else:
        session['visits'] = 1  # Start counting from 1
    print(f'Number of visits: {session["visits"]}')
    return f'Number of visits: {session["visits"]}'

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

    #print(model_response) # debug

    #print(model.GetConvoHistory())

    response_array = model_response.split('SPLIT')

    # Dbg
    print(response_array)
    for entry in response_array:
        print(entry)

    apple = {"message": response_array[0]}

    gmail_tokens = database.GetUserGmailTokens(user_id)

    pre_automation_code = f'''

from llm_judgement import LlmJudgement
from gmail_caller import GmailCaller

access_token = "{gmail_tokens[0]}"
refresh_token = "{gmail_tokens[1]}"
client_id = "{os.environ.get('GMAIL_CLIENT_ID')}"
client_secret = "{os.environ.get('GMAIL_CLIENT_SECRET')}"
    
    '''

    workflow_name = response_array[1].strip() # strip removes whitespace
    apple["workflow_name"] = workflow_name

    workflow_steps = response_array[2].split(",")
    apple["steps"] = workflow_steps

    automation_code = response_array[3]

    full_automation_code = pre_automation_code + automation_code

    print("FULL AUTOMATION CODE: ")
    print("-----------")
    print(full_automation_code)

    user_directory = os.path.join('user_workflows', user_id)

    if not os.path.exists(user_directory):
        os.mkdir(user_directory)

    #workflow_file_path = os.path.join(user_directory, generate_random_string(8) + ".workflow")
    workflow_file_path = user_id + "_" + generate_random_string(8) + "_workflow.py" # nasty workaround for imports being disgusting

    with open(workflow_file_path, "w") as workflow_file:
        workflow_file.write(full_automation_code)
    
    subprocess.Popen(["python3", "workflow_runner.py", workflow_file_path])

    return flask.jsonify(apple)

@app.route("/save-workflow-for-later", methods = ['POST'])
def save_workflow_for_later():
    # save workflow
    pass

@app.route("/run-workflow")
def run_workflow():
    # save workflow then run workflow
    pass

@app.route("/list-workflows")
def list_workflows():
    # list user's workflows
    pass

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