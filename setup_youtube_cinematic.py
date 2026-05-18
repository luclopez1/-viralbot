#!/usr/bin/env python3
"""
SETUP YOUTUBE CINEMATIC CHANNEL
Genera el token OAuth para el nuevo canal cinematografico
Ejecutar UNA VEZ localmente, luego subir token a GitHub secret
"""

import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CREDENTIALS_FILE = 'youtube_credentials_cinematic.json'
TOKEN_FILE = 'youtube_token_cinematic.json'


def main():
    print("\n" + "=" * 60)
    print("YOUTUBE OAUTH SETUP - CINEMATIC CHANNEL")
    print("=" * 60 + "\n")

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"[ERROR] No se encuentra {CREDENTIALS_FILE}")
        print("\nPASOS:")
        print("1. Ve a https://console.cloud.google.com/")
        print("2. Crea un proyecto (o usa uno existente)")
        print("3. Activa YouTube Data API v3")
        print("4. Crea credenciales OAuth 2.0 (Desktop app)")
        print("5. Descarga el JSON")
        print(f"6. Renombra a '{CREDENTIALS_FILE}' y ponlo aqui")
        print("\nLuego ejecuta este script de nuevo.\n")
        return

    print(f"[*] Usando credenciales: {CREDENTIALS_FILE}")
    print("[*] Se abrira el navegador para autorizar")
    print("[*] IMPORTANTE: Inicia sesion con la cuenta del CANAL CINEMATOGRAFICO NUEVO\n")

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())

    print(f"\n[OK] Token guardado en: {TOKEN_FILE}")

    # Print contents for easy copy to GitHub secret
    print("\n" + "=" * 60)
    print("AHORA SUBE ESTOS 2 SECRETS A GITHUB:")
    print("=" * 60)
    print("\nGitHub repo -> Settings -> Secrets and variables -> Actions")
    print("\n--- Secret 1: YOUTUBE_TOKEN_CINEMATIC ---")
    with open(TOKEN_FILE) as f:
        print(f.read())

    print("\n--- Secret 2: YOUTUBE_CREDENTIALS_CINEMATIC ---")
    with open(CREDENTIALS_FILE) as f:
        print(f.read())

    print("\n[OK] Copia y pega cada bloque en GitHub Secrets")
    print("[OK] Ya esta listo para automatizar el canal\n")


if __name__ == "__main__":
    main()
