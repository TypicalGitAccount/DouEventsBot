from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from os.path import exists
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

class Gcalendar:
    """
    Manages gcalendar events
    """
    def __init__(self, calendar_id):
        self.__scopes = ['https://www.googleapis.com/auth/calendar']
        self.__credentials = None
        self.__calendar_id = calendar_id
        if exists('token.json'):
            self.__credentials = Credentials.from_authorized_user_file('token.json', self.__scopes)
        if not self.__credentials or not self.__credentials.valid:
            if self.__credentials and self.__credentials.expired and self.__credentials.refresh_token:
                self.__credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.__scopes)
                self.__credentials = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(self.__credentials.to_json())
        self.__service = build('calendar', 'v3', credentials=self.__credentials)
    
    def set_event(self, event_json):
        """
        add event to gcalendar
        """
        event = self.__service.events().insert(calendarId=self.__calendar_id, body=event_json).execute()
        return event['id']

    def delete_event(self, event_id):
        """
        remove event from gcalendar
        """
        self.__service.events().delete(calendarId=self.__calendar_id, eventId=event_id).execute()
