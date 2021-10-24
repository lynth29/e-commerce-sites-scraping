#!/usr/bin/env python
# coding: utf-8

# Install essential libraries
from __future__ import print_function
import os.path
import io
import re
from pathlib import Path
from datetime import date
import logging
from rich.logging import RichHandler
from rich.progress import track
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload


# Parameters
SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS = 'credentials/credentials.json'
TOKEN = 'token'
API_NAME = 'drive'
API_VERSION = 'v3'
FOLDER_ID = "put_your_folder_id_in_dictionary"
PROJECT_PATH = Path(__file__).absolute().parents[1]
os.chdir(PROJECT_PATH)
CURRENT_MONTH = str(date.today().strftime("%m"))
DATE = str(date.today())

# Setting up logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")

# Define main functions
def main():
    """Upload clean_csv to Google Drive."""
    global service
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN + '/token.json'):
        creds = Credentials.from_authorized_user_file(TOKEN + '/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN + '/token.json', 'w') as token:
            token.write(creds.to_json())

    service = build(API_NAME, API_VERSION, credentials=creds)

    # Call the Drive v3 API
    for site in FOLDER_ID:
        QUERY = f"'{FOLDER_ID[site]}' in parents"
        results = service.files().list(q=QUERY,fields="nextPageToken, files(id, name)").execute()
        folders = results.get('files', [])
        if site == 'vinmart':
            file_to_upload = f"{site}_{DATE}_hn_clean.csv"
        else:
            file_to_upload = f"{site}_{DATE}_clean.csv"
        # List files in folder and download
        if not folders:
            log.info('No folders found.')
        else:
            log.info(f'Folders in {site}:')
            for folder in folders:
                log.info(f"Proceed to folder {folder['name']}.")
                qr = f"'{folder['id']}' in parents"
                if str(folder['name']) == CURRENT_MONTH:
                    response = service.files().list(q=qr,fields="nextPageToken, files(id, name)").execute()
                    items = response.get('files', [])
                    for item in items:
                        # List files' name and id
                        if item['name'] == file_to_upload:
                            log.info(f"{file_to_upload} was already uploaded.")
                        else:
                            upload_file(file_to_upload, site, folder['id'])
                            log.info(f"Uploaded {file_to_upload} to Google Drive.")
                            break
                    break
            log.info('---'*13)
            log.info('---'*13)

def upload_file(filename, site, folder_id):
    file_metadata = {'name': filename,
                     'parents': [folder_id]}
    os.chdir(str(PROJECT_PATH) + '/clean_csv/' + site)
    media = MediaFileUpload(filename, mimetype='text/csv', resumable=True)
    file = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()

if __name__ == '__main__':
    main()
