import pymongo

class DatabaseAccessor:
  def __init__(self, username: str, password: str):
    self.connection_string = f"mongodb+srv://{username}:{password}@cluster0.ifrrpwr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    self.client = client = pymongo.MongoClient(self.connection_string)

    try:
      # Try listing databases to check connection status
      database_names = self.client.list_database_names()
      print("Connection successful. Available databases:", database_names)
    except pymongo.errors.ServerSelectionTimeoutError as err:
      print("Connection failed:", err)

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



    

  