from flask import request, redirect
import flask
import requests

import os
import subprocess

import yaml

from cryptography.fernet import Fernet

import base64

import random, string

from openai_model_user import OpenAiModelUser
from database_accessor import DatabaseAccessor

app = flask.Flask(__name__)

database = DatabaseAccessor(os.environ.get('MONGO_DB_USER'), os.environ.get('MONGO_DB_PASSWORD'))

#model = OpenAiModelUser()

# create session from scratch because flask is a cunt
session = {}

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

def encrypt_message(message):
    ## Encrypts a message with fernet
    key = os.environ.get('FERNET_KEY')
    f = Fernet(key)
    encrypted_message = f.encrypt(message.encode())
    return base64.urlsafe_b64encode(encrypted_message).decode()

def decrypt_message(encrypted_message):
    ## Decrypts a message with fernet
    key = os.environ.get('FERNET_KEY')
    f = Fernet(key)
    decrypted_message = f.decrypt(base64.urlsafe_b64decode(encrypted_message)).decode()
    return decrypted_message

with open(intro_path, 'r') as file:
    intro = file.read()

# Big stuff under here

def get_pre_automation_code(gmail_access_token: str, gmail_refresh_token: str):
    code = f'''

from llm_judgement import LlmJudgement
from gmail_caller import GmailCaller

access_token = "{gmail_access_token}"
refresh_token = "{gmail_refresh_token}"
client_id = "{os.environ.get('GMAIL_CLIENT_ID')}"
client_secret = "{os.environ.get('GMAIL_CLIENT_SECRET')}"
        
        '''

    return code

def RunWorkflow(workflow_id: str):
    workflow_doc = database.GetWorkflowById(workflow_id)

    user_id = workflow_doc["auth0_user_id"]

    gmail_tokens = database.GetUserGmailTokens(user_id)

    workflow_file_path = user_id + "_" + generate_random_string(8) + "_workflow.py" # nasty workaround for imports being disgusting

    pre_automation_code = get_pre_automation_code(gmail_tokens[0], gmail_tokens[1])

    full_automation_code = pre_automation_code + workflow_doc["automation_code"]

    with open(workflow_file_path, "w") as workflow_file:
        workflow_file.write(full_automation_code)
    
    subprocess.Popen(["python3", "workflow_runner.py", workflow_file_path, workflow_id])

        print("WORKFLOW RUNNING: " + workflow_file_path)

def RunAllWorkflowsOnStartup():
    all_workflows_list = database.GetAllWorkflows()

    for workflow_doc in all_workflows_list:
        RunWorkflow(str(workflow_doc["_id"]))

# STARTUP (no pun intended)
RunAllWorkflowsOnStartup()

@app.route("/")
def hello_world():
    return "Hellooooo2"

@app.route("/workflow-action", methods = ['POST'])
def workflow_action():

    workflow_action = request.json['workflow_action']

    if workflow_action == "create" or workflow_action == None or workflow_action == "":

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

        if len(response_array) == 0:
            return flask.jsonify(apple)  ## Return just a continuation of the convo if response does not have an automation

        gmail_tokens = database.GetUserGmailTokens(user_id)

        pre_automation_code = get_pre_automation_code(gmail_tokens[0], gmail_tokens[1])

        workflow_name = response_array[1].strip() # strip removes whitespace
        apple["workflow_name"] = workflow_name

        workflow_steps = response_array[2].split(",")
        apple["steps"] = workflow_steps

        automation_code = response_array[3]

        full_automation_code = pre_automation_code + automation_code

        print("FULL AUTOMATION CODE: ")
        print("-----------")
        print(full_automation_code)

        #### SESSION

        # create session for this workflow we've made

        user_temp_data = {}
        user_temp_data['current_workflow_name'] = workflow_name
        user_temp_data['current_workflow_steps'] = workflow_steps
        user_temp_data['current_workflow_automation_code'] = automation_code
        user_temp_data['current_workflow_full_automation_code'] = full_automation_code
        user_temp_data['user_id'] = user_id

        session_id = generate_random_string(10)
        session[session_id] = user_temp_data

        apple["session_id"] = encrypt_message(session_id)

        return flask.jsonify(apple)
    
    elif workflow_action == "run":
        session_id = decrypt_message(request.json['session_id'])

        user_temp_data = session[session_id]

        workflow_id = database.SaveUserWorkflow(user_temp_data['user_id'], user_temp_data['current_workflow_name'], user_temp_data['current_workflow_steps'], user_temp_data['current_workflow_automation_code'], True)
        
        RunWorkflow(workflow_id)

        return {"message": "workflow running successfully"}

    elif workflow_action == "save":
        session_id = decrypt_message(request.json['session_id'])
        user_temp_data = session[session_id]

        workflow_id = database.SaveUserWorkflow(user_temp_data['user_id'], user_temp_data['current_workflow_name'], user_temp_data['current_workflow_steps'], user_temp_data['current_workflow_automation_code'], False)

        RunWorkflow(workflow_id) # running but workflow is paused
        
        return {"message": "workflow saved successfully"}

@app.route("/list-workflows", methods = ['POST'])
def list_workflows():
    # list user's workflows
    user_id = request.json['uid']

    user_workflows_document_list = database.GetUserWorkflows(user_id)

    workflows_list = []

    for doc in user_workflows_document_list:
        workflow = {}
        workflow["workflow_name"] = doc["workflow_name"]
        workflow["workflow_steps"] = doc["workflow_steps"]
        workflow["workflow_id"] = str(doc["_id"])
        # TODO: could return automation code in future
        # TODO: we have to return something that can help us pause the workflow
        workflows_list.append(workflow)

    return flask.jsonify({"workflows": workflows_list})

@app.route("/delete-workflow", methods = ['POST'])
def delete_workflow():
    workflow_id_string = request.json['workflow_id']

    if database.DeleteUserWorkflow(workflow_id_string):
        return {"message": "workflow deleted successfully"}
    else:
        return flask.make_response('failed to delete workflow', 400)


@app.route("/check-workflow-status", methods = ['POST'])
def delete_workflow():
    workflow_id_string = request.json['workflow_id']

    if database.CheckIfWorkflowIsOnById(workflow_id_string):
        return {"workflow_on": True}
    else:
        return {"workflow_on": False}

@app.route("/pause-workflow", methods = ['POST'])
def delete_workflow():
    workflow_id_string = request.json['workflow_id']

    if database.PauseOrUnpauseUserWorkflow(workflow_id_string):
        return {"message": "workflow paused successfully"}
    else:
        return flask.make_response('failed to pause workflow', 400)

@app.route("/unpause-workflow", methods = ['POST'])
def delete_workflow():
    workflow_id_string = request.json['workflow_id']

    if database.PauseOrUnpauseUserWorkflow(workflow_id_string):
        return {"message": "workflow unpaused successfully"}
    else:
        return flask.make_response('failed to pause workflow', 400)

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