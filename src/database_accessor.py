import pymongo

from bson import ObjectId

class DatabaseAccessor:
  def __init__(self, username: str, password: str):
    self.connection_string = f"mongodb+srv://{username}:{password}@swinvocluster0.pbydvg1.mongodb.net/?retryWrites=true&w=majority&appName=SwinvoCluster0"
    self.client = client = pymongo.MongoClient(self.connection_string)

    try:
      # Try listing databases to check connection status
      database_names = self.client.list_database_names()
      print("MongoDB Connection successful. Available databases:", database_names)
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

    tokens = (user_document["gmail_access_token"], user_document["gmail_refresh_token"])

    return tokens

  def SaveUserWorkflow(self, user_id: str, workflow_name: str, workflow_steps: [str], automation_code: str, on: bool) -> str: # returns id of inserted workflow document
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    user_workflow_document = {
      "auth0_user_id": user_id,
      "workflow_name": workflow_name,
      "workflow_steps": workflow_steps,
      "automation_code": automation_code,
      "on": 1 if on else 0
    }

    result = user_workflows_collection.insert_one(user_workflow_document)
    
    return str(result.inserted_id)

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

    if workflow_doc['on'] == 1:
      return True
    else:
      return False

  def PauseOrUnpauseUserWorkflow(self, mongo_obj_id_string: str) -> bool:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    query = {"_id": obj_id}

    if workflow_document['on'] == 1:
      update_data = {'$set': {'on': 0}}  # pause workflow

    else:
      update_data = {'$set': {'on': 1}}  # turn on workflow

    update_result = collection.update_one(query, update_data)

    if update_result.matched_count == 1:
      return True
    else:
      return False

  def DeleteUserWorkflow(self, mongo_obj_id_string: str) -> bool:
    database = self.client["swinvo-database"]
    user_workflows_collection = database["user-workflows"]

    obj_id = ObjectId(mongo_obj_id_string)

    result = user_workflows_collection.delete_one({"_id": obj_id})

    if result.deleted_count == 1:
      return True
    else:
      return False


