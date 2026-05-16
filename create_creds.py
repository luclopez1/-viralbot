#!/usr/bin/env python3
import os
import json

def clean_and_write(env_var, path):
    raw = os.environ[env_var].strip().strip("'\"")
    print(f"[DEBUG] Raw length for {env_var}: {len(raw)} chars")
    print(f"[DEBUG] First 50 chars: {raw[:50]}")
    parsed = json.loads(raw)
    with open(path, 'w') as f:
        f.write(raw)
    print(f"[OK] {path} creado exitosamente")

clean_and_write('YOUTUBE_TOKEN', 'youtube_token.json')
clean_and_write('YOUTUBE_CREDENTIALS', 'youtube_credentials.json')
print('[OK] Credenciales escritas correctamente')
