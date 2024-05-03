import googleapiclient
import google
import google.oauth2.credentials
import google.auth.transport.requests
import googleapiclient.discovery
import base64
import datetime
import time
import os

from bs4 import BeautifulSoup

from database_accessor import DatabaseAccessor

def html_to_plain_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    plain_text = soup.get_text()
    return plain_text

##unused currently
def short_time_ago_string() -> str:
    short_time_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=800)
    short_time_ago_str = short_time_ago.strftime('%Y/%m/%d %H:%M:%S')
    return short_time_ago_str

class GmailCaller:
  def __init__(self, access_token: str, refresh_token: str, client_id: str, client_secret: str):
    
    # Initialize credentials object
    credentials = google.oauth2.credentials.Credentials(
      token=access_token,
      refresh_token=refresh_token,
      client_id=client_id,
      client_secret=client_secret,
      token_uri='https://oauth2.googleapis.com/token',
      scopes=["https://www.googleapis.com/auth/gmail.modify"]
    )

    # Check if the access token is expired, and refresh if necessary
    if credentials.expired and credentials.refresh_token:
        print("refresh")
        credentials.refresh(google.auth.transport.requests.Request())

    self.gmail_service = googleapiclient.discovery.build('gmail', 'v1', credentials = credentials)

  def CheckForNewEmail(self) -> str: # Currently able to process just one email ( i think )
    try:
        # Get the list of messages
        #print(short_time_ago_string())
        #query = f'after:{short_time_ago_string()}'
        query = "newer_than:1d"

        response = self.gmail_service.users().messages().list(userId='me', labelIds=['INBOX'], q=query).execute()
        messages = response.get('messages', [])

        if messages:
            #print("New messages received:")
            for message in messages:
                #print(message)
                msg = self.gmail_service.users().messages().get(userId='me', id=message['id']).execute()

                # Ignore email if it's older than 30 seconds ago
                time_of_email = round(int(msg['internalDate']) / 1000)
                #print(time_of_email)
                time_now = round(time.time())
                #print(time_now)
                if (time_now - time_of_email) > 30:
                    return # nasty but will fix

                payload = msg['payload']
                headers = payload.get('headers', [])
                subject = ""
                for header in headers:
                    if header['name'] == 'Subject':
                        subject = header['value']
                        break
                email_text = ""
                if 'data' in payload['body']:
                  email_text += base64.urlsafe_b64decode(payload['body']['data']).decode()
                else:
                  parts = payload.get('parts', [])
                  for part in parts:
                      print(part['mimeType'])
                      if part['mimeType'] == 'text/plain':
                          data = part['body']['data']
                          email_text += base64.urlsafe_b64decode(data).decode()
                      elif part['mimeType'] == 'text/html':
                          data = part['body']['data']
                          decoded = base64.urlsafe_b64decode(data).decode()
                          email_text += html_to_plain_text(decoded)
                print("Subject:", subject)
                print("Email Text:")
                print(email_text)
                print("------------")

                # Here we return the most recent email, this is nasty need to fix
                return subject + "\n" + email_text

    except Exception as e:
        print("An error occurred:", e)

  def QueueSendEmail(self, mongo_obj_id_string: str, address_to: str, subject: str, text: str):
    database = DatabaseAccessor(os.environ.get('MONGO_DB_USER'), os.environ.get('MONGO_DB_PASSWORD')) ###
    database.SaveEmailToWorkflow(mongo_obj_id_string, address_to, subject, text)

  def SendEmail(self, address_to: str, subject: str, text: str) -> bool:
    sender = self.GetEmailAddress()

    message = {
        "raw": base64.urlsafe_b64encode(
            f"From: {sender}\r\nTo: {address_to}\r\nSubject: {subject}\r\n\r\n{text}".encode()
        ).decode()
    }

    try:
        email_message = (
            self.gmail_service.users()
            .messages()
            .send(userId='me', body=message)
            .execute()
        )
        print("Message sent successfully!")
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    

  def GetEmailAddress(self) -> str:
    profile = self.gmail_service.users().getProfile(userId='me').execute()
    email = profile['emailAddress']
    return email
