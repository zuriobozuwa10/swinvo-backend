import pymongo

from bson import ObjectId

class DatabaseAccessor:
  def __init__(self, username: str, password: str):
    self.connection_string = f"mongodb+srv://{username}:{password}@swinvocluster0.pbydvg1.mongodb.net/?retryWrites=true&w=majority&appName=SwinvoCluster0"
    self.client = client = pymongo.MongoClient(self.connection_string)

    try:
      # Try listing databases to check connection status
      database_names = self.client.list_database_names()
      #print("MongoDB Connection successful. Available databases:", database_names)
    except pymongo.errors.ServerSelectionTimeoutError as err:
      print("MongoDB Connection failed:", err)

  def AddUserGmailAuth(self, user_id: str, access_token: str, refresh_token: str) -> bool:
    database = self.client["swinvo-database"]
    gmail_user_auths_collection = database["user-gmail-auths"]

    gmail_auth_document = {
      "auth0_user_id": user_id,
      "gmail_access_token": access_token,
      "gmail_refresh_token": refresh_token
    }

    insert_result = gmail_user_auths_collection.insert_one(gmail_auth_document)
    
    return insert_result

  def CheckUserGmailAuth(self, user_id: str) -> bool:
    database = self.client["swinvo-database"]
    gmail_user_auths_collection = database["user-gmail-auths"]

    find_user = gmail_user_auths_collection.find_one({"auth0_user_id": user_id})

    if find_user:
      return True
    else:
      return False

  def GetUserGmailTokens(self, user_id: str) -> (str, str): # access, refresh
    database = self.client["swinvo-database"]
    gmail_user_auths_collection = database["user-gmail-auths"]

    user_document = gmail_user_auths_collection.find_one({"auth0_user_id": user_id})

    if user_document:
      tokens = (user_document["gmail_access_token"], user_document["gmail_refresh_token"])
    else:
      return None

    return tokens

  def AddUserOutlookAuth(self, user_id: str, access_token: str, refresh_token: str) -> bool:
    database = self.client["swinvo-database"]
    outlook_user_auths_collection = database["user-outlook-auths"]

    outlook_auth_document = {
      "auth0_user_id": user_id,
      "outlook_access_token": access_token,
      "outlook_refresh_token": refresh_token
    }

    insert_result = outlook_user_auths_collection.insert_one(outlook_auth_document)
    
    return insert_result

  def CheckUserOutlookAuth(self, user_id: str) -> bool:
    database = self.client["swinvo-database"]
    outlook_user_auths_collection = database["user-outlook-auths"]

    find_user = outlook_user_auths_collection.find_one({"auth0_user_id": user_id})

    if find_user:
      return True
    else:
      return False

  def GetUserOutlookTokens(self, user_id: str) -> (str, str): # access, refresh
    database = self.client["swinvo-database"]
    outlook_user_auths_collection = database["user-outlook-auths"]

    user_document = outlook_user_auths_collection.find_one({"auth0_user_id": user_id})

    if user_document:
      tokens = (user_document["outlook_access_token"], user_document["outlook_refresh_token"])
    else:
      return None

    return tokens

  def RefreshUserOutlookTokens(self, old_refresh_token: str, new_access_token: str, new_refresh_token: str) -> (str, str): # access, refresh
    database = self.client["swinvo-database"]
    outlook_user_auths_collection = database["user-outlook-auths"]

    query = {"outlook_refresh_token": old_refresh_token}

    user_document = outlook_user_auths_collection.find_one(query)

    update_data = {'$set': {'outlook_access_token': new_access_token, 'outlook_refresh_token': new_refresh_token}}  # pause workflow

    update_result = outlook_user_auths_collection.update_one(query, update_data)

    if update_result.matched_count == 1:
      return True
    else:
      return False

  def SaveUserWorkflow(self, user_id: str, workflow_name: str, workflow_steps: [str], automation_code: str, on: bool) -> str: # returns id of inserted workflow document
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    user_workflow_document = {
      "auth0_user_id": user_id,
      "workflow_name": workflow_name,
      "workflow_steps": workflow_steps,
      "automation_code": automation_code,
      "on": 1 if on else 0,
      "email_queue": [],
      "error_lock": 0,
      "error": False
    }

    result = user_workflows_collection.insert_one(user_workflow_document)
    
    return str(result.inserted_id)

  def SaveEmailToWorkflow(self, mongo_obj_id_string: str, address_to: str, subject: str, text: str) -> bool:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    query = {"_id": obj_id}

    user_email_document = {
      "address_to": address_to,
      "subject": subject,
      "text": text,
    }

    update_data =  {'$push': {'email_queue': user_email_document}}

    update_result = user_workflows_collection.update_one(query, update_data)

    if update_result.matched_count == 1:
      return True
    else:
      return False


  def GetEmailFromWorkflow(self, mongo_obj_id_string: str, message_index: int) -> (str, str, str): #(address_to, subject, text)
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    query = {"_id": obj_id}

    workflow_doc = user_workflows_collection.find_one(query)

    try:
      message = workflow_doc['email_queue'][message_index]
      return (message['address_to'], message['subject'], message['text'])

    except Exception as e:
      print("Error getting Email", e)
      return None

  def DeleteEmailFromWorkflow(self, mongo_obj_id_string: str, message_index: int) -> bool:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    query = {"_id": obj_id}

    workflow_doc = user_workflows_collection.find_one(query)

    del workflow_doc['email_queue'][message_index]

    update_data = {'$set': {'email_queue': workflow_doc['email_queue']}}

    update_result = user_workflows_collection.update_one(query, update_data)

    if update_result.matched_count == 1:
      return True
    else:
      return False

  def GetUserWorkflows(self, user_id: str) -> list:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    user_workflows_documents_cursor = user_workflows_collection.find({"auth0_user_id": user_id})

    user_workflows_documents_list = []

    for doc in user_workflows_documents_cursor:
      user_workflows_documents_list.append(doc)
      #print(doc) # debug
    
    return user_workflows_documents_list

  def GetAllWorkflows(self) -> list:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    all_workflows_documents_cursor = user_workflows_collection.find()

    all_workflows_documents_list = []

    for doc in all_workflows_documents_cursor:
      all_workflows_documents_list.append(doc)
      #print(doc) # debug
    
    return all_workflows_documents_list

  def GetWorkflowById(self, mongo_obj_id_string) -> dict:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    workflow_doc = user_workflows_collection.find_one({"_id": obj_id})

    return workflow_doc

  def CheckIfWorkflowIsOnById(self, mongo_obj_id_string) -> bool:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    workflow_doc = user_workflows_collection.find_one({"_id": obj_id})

    if workflow_doc == None:
      #print("Workflow does not exist")
      return False

    if workflow_doc['on'] == 1:
      return True
    else:
      return False

  def PauseOrUnpauseUserWorkflow(self, mongo_obj_id_string: str) -> bool:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    query = {"_id": obj_id}

    workflow_doc = user_workflows_collection.find_one(query)

    if workflow_doc['on'] == 1:
      update_data = {'$set': {'on': 0}}  # pause workflow

    else:
      update_data = {'$set': {'on': 1}}  # turn on workflow

    update_result = user_workflows_collection.update_one(query, update_data)

    if update_result.matched_count == 1:
      return True
    else:
      return False

  def SetWorkflowToGood(self, mongo_obj_id_string: str) -> bool:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    query = {"_id": obj_id}

    workflow_doc = user_workflows_collection.find_one(query)

    update_data = {'$set': {'error': False}}  # Good

    update_result = user_workflows_collection.update_one(query, update_data)

    if update_result.matched_count == 1:
      return True
    else:
      return False

  def SetWorkflowToError(self, mongo_obj_id_string: str) -> bool:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    query = {"_id": obj_id}

    workflow_doc = user_workflows_collection.find_one(query)

    update_data = {'$set': {'error': True}}  # Good

    update_result = user_workflows_collection.update_one(query, update_data)

    if update_result.matched_count == 1:
      return True
    else:
      return False

  def CheckWorkflowError(self, mongo_obj_id_string: str) -> bool:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    workflow_doc = user_workflows_collection.find_one({"_id": obj_id})

    if workflow_doc == None:
      #print("Workflow does not exist")
      return True # error

    if workflow_doc['error_lock'] == 1:
      return True

    return workflow_doc['error']

  def DeleteUserWorkflow(self, mongo_obj_id_string: str) -> bool:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    result = user_workflows_collection.delete_one({"_id": obj_id})

    if result.deleted_count == 1:
      return True
    else:
      return False

  #### Stripe

  def AddStripeUserFirstSubscription(self, user_id: str, customer_id: str, subscription_id: str, subscription_status: bool = True) -> bool:
    # Sets subscription status to True in this method
    database = self.client["swinvo-database"]
    user_stripe_collection = database["user-stripe"]

    user_stripe_doc = {}
    user_stripe_doc["auth0_user_id"] = user_id
    user_stripe_doc["stripe_customer_id"] = customer_id
    user_stripe_doc["stripe_subscription_id"] = subscription_id
    user_stripe_doc["stripe_subscription_status"] = subscription_status

    user_stripe_collection.insert_one(user_stripe_doc)

    return True

  def CheckUserStripeExists(self, user_id: str) -> bool:
    database = self.client["swinvo-database"]
    user_stripe_collection = database["user-stripe"]

    find_user = user_stripe_collection.find_one({"auth0_user_id": user_id})

    if find_user:
      return True
    else:
      return False

  def CheckUserStripeSubscriptionStatus(self, user_id: str) -> bool:
    database = self.client["swinvo-database"]
    user_stripe_collection = database["user-stripe"]

    user_stripe_doc = user_stripe_collection.find_one({"auth0_user_id": user_id})

    if user_stripe_doc == None:
      #print("Stripe document does not exist")
      return False

    if (user_stripe_doc['stripe_subscription_status']):
      return True
    else:
      return False

  def ToggleStripeSubscription(self, user_id: str) -> bool:
    database = self.client["swinvo-database"]
    user_stripe_collection = database["user-stripe"]

    query = {"auth0_user_id": user_id}

    user_stripe_doc = user_stripe_collection.find_one(query)

    if user_stripe_doc == None:
      #print("Stripe document does not exist")
      return False

    if user_stripe_doc['stripe_subscription_status'] == True:
      update_data = {'$set': {'stripe_subscription_status': False}}  # Set subscription off

    else:
      update_data = {'$set': {'stripe_subscription_status': True}}  # Set subscription on

    update_result = user_stripe_collection.update_one(query, update_data)

    if update_result.matched_count == 1:
      return True
    else:
      return False

  def StripeUserAnotherSubscription(self, user_id: str, customer_id: str, subscription_id: str, subscription_status: bool = True) -> bool:
    # Sets subscription status to True in this method
    database = self.client["swinvo-database"]
    user_stripe_collection = database["user-stripe"]

    ####

    return None

  def GetUserStripeSubscriptionId(self, user_id: str):
    database = self.client["swinvo-database"]
    user_stripe_collection = database["user-stripe"]

    user_stripe_doc = user_stripe_collection.find_one({"auth0_user_id": user_id})

    return user_stripe_doc['stripe_subscription_id']

  def EndedStripeUserSubscription(self, subscription_id: str) -> bool:
    database = self.client["swinvo-database"]
    user_stripe_collection = database["user-stripe"]

    query = {"stripe_subscription_id": subscription_id}

    user_stripe_doc = user_stripe_collection.find_one(query)

    if user_stripe_doc['stripe_subscription_status'] == True:
      update_data = {'$set': {'stripe_subscription_status': False}} 
    else:
      print("We shouldn't be here. Tried to end user sub thats already inactive.")
      update_data = {'$set': {'stripe_subscription_status': False}} 

    update_result = user_stripe_collection.update_one(query, update_data)

    if update_result.matched_count == 1:
      return True
    else:
      return False