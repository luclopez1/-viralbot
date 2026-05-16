#!/usr/bin/env python3
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import requests

# Load token
with open('youtube_token.json', 'r') as f:
    token_data = json.load(f)

# Create credentials and refresh
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
creds = Credentials.from_authorized_user_info(token_data, SCOPES)

if creds.expired and creds.refresh_token:
    print('[*] Renovando token...')
    refresh_session = requests.Session()
    refresh_session.verify = False
    creds.refresh(Request(session=refresh_session))

    # Save refreshed token
    with open('youtube_token.json', 'w') as f:
        f.write(creds.to_json())
    print('[OK] Token renovado y guardado')
    print(f'    Nuevo expiry: {creds.expiry}')
