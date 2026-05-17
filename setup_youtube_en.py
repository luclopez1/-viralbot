#!/usr/bin/env python3
"""
Script para generar el token OAuth para el canal EN de YouTube
Reutiliza las credenciales OAuth del canal principal pero genera un token
especifico para el canal en ingles.

IMPORTANTE: Cuando abra el navegador, asegurate de SELECCIONAR EL CANAL EN INGLES
"""

import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CREDENTIALS_FILE = 'youtube_credentials.json'  # Reutiliza credenciales existentes
TOKEN_FILE = 'youtube_token_en.json'  # Token NUEVO para canal EN


def main():
    print("="*60)
    print("CONFIGURACION DE CANAL EN INGLES - YOUTUBE")
    print("="*60)
    print()

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"[ERROR] No se encuentra {CREDENTIALS_FILE}")
        print("       Necesitas tener el archivo de credenciales OAuth del canal principal")
        return False

    print("[*] Iniciando flujo de autenticacion...")
    print()
    print("IMPORTANTE: Cuando abra el navegador:")
    print("  1. Inicia sesion con tu cuenta de Google")
    print("  2. SELECCIONA EL CANAL EN INGLES (ViralBot EN)")
    print("  3. Acepta los permisos")
    print()
    input("Presiona ENTER para continuar...")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

        # Guardar token
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())

        print()
        print("="*60)
        print(f"[OK] Token guardado en: {TOKEN_FILE}")
        print("="*60)
        print()
        print("PROXIMO PASO:")
        print(f"  1. Abre el archivo {TOKEN_FILE}")
        print(f"  2. Copia TODO su contenido")
        print(f"  3. Ve a GitHub: Settings -> Secrets -> Actions")
        print(f"  4. Crea un secret llamado: YOUTUBE_TOKEN_EN")
        print(f"  5. Pega el contenido del archivo")
        print()
        print(f"  6. Crea otro secret llamado: YOUTUBE_CREDENTIALS_EN")
        print(f"  7. Copia el contenido de youtube_credentials.json")
        print()
        return True

    except Exception as e:
        print(f"[ERROR] Error en autenticacion: {e}")
        return False


if __name__ == "__main__":
    main()
