



from database_accessor import DatabaseAccessor

import os
import requests
import json

from datetime import datetime, timedelta

from bs4 import BeautifulSoup

def html_to_plain_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    plain_text = soup.get_text()
    return plain_text


class OutlookCaller:
  def __init__(self, access_token: str, refresh_token: str, client_id: str, client_secret: str):
    self.access_token = access_token
    self.refresh_token = refresh_token
    self.client_id = client_id
    self.client_secret = client_secret

    self.database = DatabaseAccessor(os.environ.get('MONGO_DB_USER'), os.environ.get('MONGO_DB_PASSWORD'))

  def RefreshAccessToken(self):
    old_refresh_token = self.refresh_token

    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'client_id': self.client_id,
        'client_secret': self.client_secret,
        'refresh_token': self.refresh_token,
        'grant_type': 'refresh_token',
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        new_tokens = response.json()
        self.access_token = new_tokens['access_token']
        if 'refresh_token' in new_tokens:
          # unexpected but would be cool
          self.database.RefreshUserOutlookTokens(old_refresh_token, new_tokens['access_token'], new_tokens['refresh_token'])
          self.refresh_token = new_tokens['refresh_token']
          print("NEW REFRESH TOKEN SOMEHOW!!!!! ")
        else:
          # expected
          self.database.RefreshUserOutlookTokens(old_refresh_token, new_tokens['access_token'], old_refresh_token)
          #print("outlook token refreshed!")
        return True
    else:
        print(f"Error refreshing token: {response.status_code}")
        print(response.json())
        return False
    

  def CheckForNewEmail(self) -> str:
    self.RefreshAccessToken()

    url = "https://graph.microsoft.com/v1.0/me/sendMail"
    headers = {
        'Authorization': f'Bearer {self.access_token}',
        'Content-Type': 'application/json'
    }

    now = datetime.utcnow()
    yesterday = now - timedelta(days=15)
    yesterday_str = yesterday.strftime('%Y-%m-%dT%H:%M:%SZ')

    url = f'https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages'
    params = {
        '$filter': f'receivedDateTime ge {yesterday_str}',
        '$select': 'subject,receivedDateTime,from,body',
        '$orderby': 'receivedDateTime DESC'
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        emails_list = response.json()['value']

        if not emails_list:
          return

        # Just get most recent one for now
        most_recent_email = emails_list[0]

        #print(most_recent_email.keys())
        #print(type(most_recent_email["body"]))
        #print(most_recent_email["body"])
        #print(most_recent_email["body"].keys())

        body = most_recent_email["body"]

        text = None

        if body["contentType"] == "html":
            text = html_to_plain_text(body["content"])
        elif body["contentType"] == "text":
            text = body["content"]

        if text:
            email = {}
            email["text"] = most_recent_email["subject"] + "\n" + text
            email["from"] = most_recent_email["from"]["emailAddress"]["address"]
            #print(email["from"])
            return email
        else:
            print("no text!!!")
            return None
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return
    

  def QueueSendEmail(self, mongo_obj_id_string: str, address_to: str, subject: str, text: str):
    self.database.SaveEmailToWorkflow(mongo_obj_id_string, address_to, subject, text)

  def SendEmail(self, address_to: str, subject: str, text: str) -> bool:
    self.RefreshAccessToken()

    url = "https://graph.microsoft.com/v1.0/me/sendMail"
    headers = {
        'Authorization': f'Bearer {self.access_token}',
        'Content-Type': 'application/json'
    }
    
    email_msg = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": text
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": address_to
                    }
                }
            ]
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(email_msg))
    
    if response.status_code == 202:
        print("Email sent successfully.")
        return True
    else:
        print(f"Error sending email: {response.status_code}")
        print(response.json())
        return False

