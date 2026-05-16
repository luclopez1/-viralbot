#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import requests

# Test loading the token file
print("[*] Verificando credenciales...")
try:
    with open('youtube_token.json', 'r') as f:
        token_data = json.load(f)
        print('[OK] youtube_token.json es JSON válido')
        print(f'    Tiene token: {"token" in token_data}')
        print(f'    Tiene refresh_token: {"refresh_token" in token_data}')
        print(f'    Tiene client_id: {"client_id" in token_data}')
        print(f'    Tiene client_secret: {"client_secret" in token_data}')
        expiry = token_data.get("expiry", "N/A")
        print(f'    Expiry: {expiry}')

        # Check if expired
        if expiry != "N/A":
            from datetime import datetime
            expiry_dt = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
            now = datetime.now(expiry_dt.tzinfo)
            if now > expiry_dt:
                print(f'    [WARN] TOKEN EXPIRADO (hace {(now - expiry_dt).total_seconds() / 3600:.1f} horas)')
            else:
                print(f'    [OK] Token válido (expira en {(expiry_dt - now).total_seconds() / 3600:.1f} horas)')
except Exception as e:
    print(f'[ERROR] Error al leer youtube_token.json: {e}')
    sys.exit(1)

# Test loading credentials file
try:
    with open('youtube_credentials.json', 'r') as f:
        creds_data = json.load(f)
        print('[OK] youtube_credentials.json es JSON válido')
        print(f'    Tiene installed: {"installed" in creds_data}')
except Exception as e:
    print(f'[ERROR] Error al leer youtube_credentials.json: {e}')
    sys.exit(1)

# Test creating Credentials object
try:
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    print('[OK] Credentials object creado exitosamente')
    print(f'    Expirado: {creds.expired}')
    print(f'    Tiene refresh_token: {creds.refresh_token is not None}')

    # Test token refresh
    if creds.expired and creds.refresh_token:
        print('[*] Intentando renovar token...')
        try:
            refresh_session = requests.Session()
            refresh_session.verify = False
            creds.refresh(Request(session=refresh_session))
            print('[OK] Token renovado exitosamente')
            print(f'    Nuevo expiry: {creds.expiry}')
        except Exception as refresh_error:
            print(f'[ERROR] Error al renovar token: {refresh_error}')
    else:
        print('[OK] Token no necesita renovación')

except Exception as e:
    print(f'[ERROR] Error al crear Credentials: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

print('[OK] Todas las verificaciones pasaron')
