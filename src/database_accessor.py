import pymongo

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



    

  