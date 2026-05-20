#!/usr/bin/env python3
import os
from pathlib import Path

workflow_content = """name: ViralBot - Generar y Subir Short

on:
  schedule:
    - cron: '0 7 * * *'
    - cron: '0 11 * * *'
    - cron: '0 15 * * *'
    - cron: '0 18 * * *'
    - cron: '0 21 * * *'
  workflow_dispatch:

env:
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
  PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}

jobs:
  generate-and-upload:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Instalar FFmpeg
        run: sudo apt-get install -y ffmpeg

      - name: Instalar Python y dependencias
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Instalar paquetes
        run: pip install -r requirements.txt

      - name: Crear archivos de credenciales
        env:
          YOUTUBE_TOKEN: ${{ secrets.YOUTUBE_TOKEN }}
          YOUTUBE_CREDENTIALS: ${{ secrets.YOUTUBE_CREDENTIALS }}
        run: python3 create_creds.py && mkdir -p temp videos_output logs

      - name: Verificar archivos de credenciales
        run: python3 -c "import json; json.load(open('youtube_token.json')); json.load(open('youtube_credentials.json')); print('[OK] Credenciales válidas')"

      - name: Crear .env
        run: |
          echo "GEMINI_API_KEY=${GEMINI_API_KEY}" > .env
          echo "YOUTUBE_API_KEY=${YOUTUBE_API_KEY}" >> .env
          echo "PEXELS_API_KEY=${PEXELS_API_KEY}" >> .env
          echo "OUTPUT_DIR=./videos_output" >> .env
          echo "TEMP_DIR=./temp" >> .env
          echo "VIDEO_DURATION_SECONDS=58" >> .env
          echo "VIDEO_RESOLUTION=1080x1920" >> .env

      - name: Generar y subir video
        run: python generate_content.py
"""

# Eliminar archivo viejo
workflow_file = Path(".github/workflows/viralbot.yml")
if workflow_file.exists():
    workflow_file.unlink()
    print("[OK] Archivo viejo eliminado")

# Crear archivo nuevo
workflow_file.parent.mkdir(parents=True, exist_ok=True)
with open(workflow_file, 'w') as f:
    f.write(workflow_content)
print("[OK] Archivo nuevo creado")

# Commit y push
os.system("git add .github/workflows/viralbot.yml")
os.system('git commit -m "Recrear workflow limpio"')
os.system("git push")
print("[OK] Cambios subidos a GitHub")