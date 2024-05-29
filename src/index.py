from flask import request, redirect
import flask
import requests

import os
import subprocess

import yaml

from cryptography.fernet import Fernet

import base64
from datetime import datetime, timedelta

import random, string

from openai_model_user import OpenAiModelUser
from database_accessor import DatabaseAccessor
from gmail_caller import GmailCaller

from outlook_caller import OutlookCaller

import stripe

## test
##stripe.api_key = " # secret key, test at the moment

# live
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

app = flask.Flask(__name__)


database = DatabaseAccessor(os.environ.get('MONGO_DB_USER'), os.environ.get('MONGO_DB_PASSWORD'))

#model = OpenAiModelUser()

# create session from scratch because flask is a cunt
session = {}

intro_path = "intro2_outlook.txt"

# Store user chat sessions in a dictionary for now. TODO (ZO): Improve this.
# Resets after every deployment
user_chat_sessions = {}

# Used to associate an app (e.g gmail) integration with a swinvo account
state_tokens = {}

# Each token tuple: (access_token, refresh_token)
gmail_user_tokens = {}

def simple_logger(log_message: str, file_path: str = "swinvo.log"):
    with open(file_path, 'a') as file:
        file.write(str(log_message) + '\n')

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

import sys
import os
from llm_judgement import LlmJudgement
from gmail_caller import GmailCaller

access_token = "{gmail_access_token}"
refresh_token = "{gmail_refresh_token}"
client_id = "{os.environ.get('GMAIL_CLIENT_ID')}"
client_secret = "{os.environ.get('GMAIL_CLIENT_SECRET')}"
        
        '''

    return code

def get_pre_automation_code_outlook(outlook_access_token: str, outlook_refresh_token: str):
    code = f'''

import sys
import os
from llm_judgement import LlmJudgement
from outlook_caller import OutlookCaller

access_token = "{outlook_access_token}"
refresh_token = "{outlook_refresh_token}"
client_id = "{os.environ.get('OUTLOOK_CLIENT_ID')}"
client_secret = "{os.environ.get('OUTLOOK_CLIENT_SECRET')}"
        
        '''

    return code

def RunWorkflow(workflow_id: str):
    workflow_doc = database.GetWorkflowById(workflow_id)

    user_id = workflow_doc["auth0_user_id"]

    #gmail_tokens = database.GetUserGmailTokens(user_id)

    # TODO Make this more robust; let user know at front end that we can't do this workflow
    #if gmail_tokens == None:
    #    return

    outlook_tokens = database.GetUserOutlookTokens(user_id)

    if outlook_tokens == None:
        return

    workflow_file_path = user_id + "_" + generate_random_string(8) + "_workflow.py" # nasty workaround for imports being disgusting

    #pre_automation_code = get_pre_automation_code(gmail_tokens[0], gmail_tokens[1])

    pre_automation_code = get_pre_automation_code_outlook(outlook_tokens[0], outlook_tokens[1])

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

        #if not user_id:
        #    return flask.jsonify({"message": "Please Sign In!"})

        ### Check if user is pro member, if not, then they can only have one workflow:
        if database.CheckUserStripeSubscriptionStatus(user_id):
            pass
        else:
            if ( len(database.GetUserWorkflows(user_id)) > 0 ):
                return flask.jsonify({"message": "Get Swinvo Pro to own more than 1 workflow!"})


        system_content = intro

        if user_id not in user_chat_sessions:
            user_model = OpenAiModelUser(system_content=system_content)
            #user_model.Use(intro) #using system instead?
            user_chat_sessions[user_id] = user_model

        input_text = request.json['text']

        chatting_string = 'Someone chatting: ' + input_text
        print(chatting_string)
        simple_logger(chatting_string)

        model_response = user_chat_sessions[user_id].Use(input_text)

        #print(model_response) # debug

        #print(model.GetConvoHistory())

        response_array = model_response.split('SPLIT')

        # Dbg
        print(response_array)
        for entry in response_array:
            print(entry)

        apple = {"message": response_array[0]}

        if len(response_array) < 2:
            return flask.jsonify(apple)  ## Return just a continuation of the convo if response does not have an automation

        #gmail_tokens = database.GetUserGmailTokens(user_id)

        #if gmail_tokens == None:
        #    return flask.jsonify({"message": "Please integrate with Gmail."}) # TODO: Change this for all integrations
        
        if user_id:
            outlook_tokens = database.GetUserOutlookTokens(user_id) 
        else:
            outlook_tokens = None

        if outlook_tokens == None:
            apple["unsatisfied_integrations"] = ["outlook"]
            outlook_tokens = ("ABC", "CDF")
        else:
            outlook_tokens = database.GetUserOutlookTokens(user_id)
            apple["unsatisfied_integrations"] = []

        #pre_automation_code = get_pre_automation_code(gmail_tokens[0], gmail_tokens[1])

        pre_automation_code = get_pre_automation_code_outlook(outlook_tokens[0], outlook_tokens[1])

        workflow_name = response_array[1].strip() # strip removes whitespace
        apple["workflow_name"] = workflow_name

        workflow_steps = response_array[2].split(",")
        apple["steps"] = workflow_steps

        simple_logger(workflow_steps)


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

        workflow["email_queue"] = doc["email_queue"] # need more queues.
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
def check_workflow_status():
    workflow_id_string = request.json['workflow_id']

    if database.CheckIfWorkflowIsOnById(workflow_id_string):
        return {"workflow_on": True}
    else:
        return {"workflow_on": False}

@app.route("/pause-workflow", methods = ['POST'])
def pause_workflow():
    workflow_id_string = request.json['workflow_id']

    if database.PauseOrUnpauseUserWorkflow(workflow_id_string):
        return {"message": "workflow paused successfully"}
    else:
        return flask.make_response('failed to pause workflow', 400)

@app.route("/unpause-workflow", methods = ['POST'])
def unpause_workflow():
    workflow_id_string = request.json['workflow_id']

    if database.PauseOrUnpauseUserWorkflow(workflow_id_string):
        return {"message": "workflow unpaused successfully"}
    else:
        return flask.make_response('failed to pause workflow', 400)

@app.route("/send-message", methods = ['POST'])
def send_message():

    user_id = request.json['uid']
    workflow_id_string = request.json['workflow_id']
    message_index = request.json['message_index']

    #email_provider = "gmail"
    email_provider = "outlook"

    if email_provider == "gmail":

        gmail_tokens = database.GetUserGmailTokens(user_id)

        gmail_caller = GmailCaller(gmail_tokens[0], gmail_tokens[1], os.environ.get('GMAIL_CLIENT_ID'), os.environ.get('GMAIL_CLIENT_SECRET'))

        email_tuple = database.GetEmailFromWorkflow(workflow_id_string, message_index)

        if gmail_caller.SendEmail(email_tuple[0], email_tuple[1], email_tuple[2]):
            pass
        else:
            return {"message": "Failed to send message"}

    elif email_provider == "outlook":

        outlook_tokens = database.GetUserOutlookTokens(user_id)

        outlook_caller = OutlookCaller(outlook_tokens[0], outlook_tokens[1], os.environ.get('OUTLOOK_CLIENT_ID'), os.environ.get('OUTLOOK_CLIENT_SECRET'))

        email_tuple = database.GetEmailFromWorkflow(workflow_id_string, message_index)

        if outlook_caller.SendEmail(email_tuple[0], email_tuple[1], email_tuple[2]):
            pass
        else:
            return {"message": "Failed to send message"}

    if database.DeleteEmailFromWorkflow(workflow_id_string, message_index):
        return {"message": "message sent successfully and deleted from database"}
    else:
        return flask.make_response('failed to delete message from db after sending', 400)


@app.route("/delete-message", methods = ['POST'])
def delete_message():

    user_id = request.json['uid']
    workflow_id_string = request.json['workflow_id']
    message_index = request.json['message_index']

    if database.DeleteEmailFromWorkflow(workflow_id_string, message_index):
        return {"message": "message deleted successfully"}
    else:
        return flask.make_response('failed to delete message', 400)
        #return {"message": "FAILED"}


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

@app.route("/check-outlook-auth", methods = ['POST'])
def check_outlook_auth():
    user_id = request.json['uid']

    outlook_is_authed = database.CheckUserOutlookAuth(user_id)

    outlook_auth_dict = {}

    if outlook_is_authed:
        outlook_auth_dict["outlook_auth"] = True
    else:
        outlook_auth_dict["outlook_auth"] = False

    return flask.jsonify(outlook_auth_dict)


@app.route("/auth-session", methods = ['POST'])
def auth_session():
    state = request.json['state']
    user_id = request.json['uid']
    if user_id:
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


@app.route("/outlook-auth-callback")
def outlook_auth_callback():
    code = request.args.get('code')

    # Exchange the authorization code for an access token and refresh token
    token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
    token_data = {
        'client_id': os.environ.get('OUTLOOK_CLIENT_ID'),
        'client_secret': os.environ.get('OUTLOOK_CLIENT_SECRET'),
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'https://auth.swinvo.com/outlook-auth-callback',
    }
    token_headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    state = request.args.get('state')

    if state in state_tokens:
        user_id = state_tokens[state]
    else:
        print('Unknown state: ' + state + ' . Aborting')
        flask.abort(400, 'User state unknown. THIS IS A KNOWN AUTH0 BUG ON SAFARI. PLEASE USE GOOGLE CHROME INSTEAD')

    response = requests.post(token_url, data=token_data, headers=token_headers)

    if response.status_code == 200:
        tokens = response.json()

        result = database.AddUserOutlookAuth( user_id, tokens.get('access_token'), tokens.get('refresh_token') )
        if result is False:
            flask.abort(500, "FAILED TO ADD USER AUTH TOKENS TO DATABASE")

        # Redirect to your app
        return redirect("https://app.swinvo.com")

    else:
        print ("BAD RESPONSE")


@app.route("/log-event", methods = ['POST'])
def log_event():
    user_id = request.json['uid']

    if not user_id:
        user_id = "n/a"

    message = request.json['message']

    log_string = user_id + ": " + message

    simple_logger(log_string)
    print(log_string)

    return flask.jsonify(success=True), 200


##### STRIPE #######


@app.route("/stripe-create-checkout-session", methods = ['POST'])
def stripe_create_checkout_session():
    user_id = request.json.get('uid')

    #test
    #price_id = "price_1PClUKD6NaA2VbAqOvpiFRMP"

    #live
    price_id = "price_1PEChCD6NaA2VbAq0rsOGGPm"

    timestamp_in_7_days = datetime.now() + timedelta(days=7, hours=5)
    trial_end = round(timestamp_in_7_days.timestamp())

    try:
        session = stripe.checkout.Session.create(
            success_url="https://app.swinvo.com",
            cancel_url="https://app.swinvo.com/subscribe",
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            metadata={"user_id": user_id},
            subscription_data={"trial_end": trial_end}
        )

        print(session)
                    
        print("session url: ", session.url)

        stripe_session = {}
        stripe_session["stripe_session_url"] =  session.url
        stripe_session["stripe_session_id"] = session.id
        return flask.jsonify(stripe_session)
    except Exception as e:
        print("stripe error: ", str(e))
        return flask.jsonify(error=str(e)), 403

@app.route("/stripe-webhook", methods = ['POST'])
def stripe_webhook():
    #TEST
    #endpoint_secret = ""

    #LIVE
    endpoint_secret = ""

    print("stripe webhook")

    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    #print(event)

    # Handle event with mongo here
    ###
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']  ## object here is a session: https://docs.stripe.com/api/financial_connections/sessions/object

        user_id = session['metadata']['user_id']
        customer_id = session["customer"]
        subscription_id = session["subscription"]

        subscription_status = True ###

        if not database.CheckUserStripeExists(user_id):
            database.AddStripeUserFirstSubscription(user_id, customer_id, subscription_id) # add subscription when user never been subscribed before
        else:
            database.StripeUserAnotherSubscription(user_id, customer_id, subscription_id)# add subscr when user record already exists. replace any existing

    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        if subscription['status'] == 'canceled':
            database.EndedStripeUserSubscription(subscription_id)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        if subscription['status'] == 'canceled':
            database.EndedStripeUserSubscription(subscription_id)


    return flask.jsonify(success=True), 200

@app.route("/check-if-user-subscribed", methods = ['POST'])
def check_if_user_subscribed():

    apple = {}

    user_id = request.json['uid']

    if not database.CheckUserStripeSubscriptionStatus(user_id):
        apple["user_subscribed"] = False
        apple["trialing"] = False
        apple["trial_end"] = None
        
        return flask.jsonify(apple)


    # Check if user is on trial
    subscription = stripe.Subscription.retrieve(database.GetUserStripeSubscriptionId(user_id))

    if subscription.status == 'trialing':
        trialing = True
        trial_end = subscription.trial_end
    else:
        trialing = False

    if database.CheckUserStripeSubscriptionStatus(user_id):
        apple["user_subscribed"] = True
    else:
        apple["user_subscribed"] = False

    if trialing:
        apple["trialing"] = True
        apple["trial_end"] = trial_end
    else:
        apple["trialing"] = False
        apple["trial_end"] = None

    return flask.jsonify(apple)

@app.route("/stripe-subscription-info-public", methods = ['POST'])
def stripe_subscription_info_public():
    user_id = request.json['uid']

    info_public = {}

    if database.CheckUserStripeSubscriptionStatus(user_id):
        subscription = stripe.Subscription.retrieve(database.GetUserStripeSubscriptionId(user_id))

        info_public['current_period_end'] = subscription.current_period_end
        info_public['price'] = subscription['items']['data'][0]['price']['unit_amount']
        info_public['cancel_at_period_end'] = subscription.cancel_at_period_end

        info_public['trial_end'] = subscription.trial_end
        if subscription.status == "trialing":
            info_public['trialing'] = True
        else:
            info_public['trialing'] = False

        #print(subscription)
        print(info_public)

        return flask.jsonify(info_public)

    else:
        return flask.jsonify({"message": "User is not subscribed to Pro"})

@app.route("/stripe-cancel-subscription", methods = ['POST'])
def stripe_cancel_subscription():
    user_id = request.json['uid']

    if database.CheckUserStripeSubscriptionStatus(user_id):
        try:
            stripe.Subscription.modify(
                database.GetUserStripeSubscriptionId(user_id),
                cancel_at_period_end=True
            )
        except Exception as e:
            print("stripe error cancellation: ", str(e))
            return flask.jsonify(error=str(e)), 500

        return {"message": "Successfully cancelled subscription, ends at end of billing cycle."}

    else:
        return {"message": "User is already not subscribed to Pro"}