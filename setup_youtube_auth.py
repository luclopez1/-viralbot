#!/usr/bin/env python3
"""
Ejecuta este script UNA VEZ para autenticarte con YouTube.
Abrira el navegador para que des permiso. Guarda el token en youtube_token.json.
"""

import os
import ssl
import urllib3

# Bypass SSL para redes corporativas
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests
from unittest.mock import patch
original_request = requests.Session.request
def patched_request(self, *args, **kwargs):
    kwargs['verify'] = False
    return original_request(self, *args, **kwargs)
requests.Session.request = patched_request

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CREDS_FILE = 'youtube_credentials.json'
TOKEN_FILE = 'youtube_token.json'

if not os.path.exists(CREDS_FILE):
    print("[ERROR] No se encontro youtube_credentials.json")
    print("   Descargalo desde Google Cloud Console -> Credenciales -> OAuth 2.0")
    exit(1)

print("[*] Abriendo navegador para autenticacion con YouTube...")
print("   Inicia sesion con la cuenta del canal ViralBot\n")

flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
creds = flow.run_local_server(port=0)

with open(TOKEN_FILE, 'w') as token:
    token.write(creds.to_json())

print(f"\n[OK] Autenticacion completada!")
print(f"[OK] Token guardado en: {TOKEN_FILE}")
print(f"\nYa puedes ejecutar: python generate_content.py")
