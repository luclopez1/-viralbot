#!/usr/bin/env python3
"""
Script para probar solo la subida a YouTube sin generar un nuevo video
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Traer la función upload_to_youtube del script principal
sys.path.insert(0, str(Path(__file__).parent))

from generate_content import upload_to_youtube

# Buscar el último video generado
output_dir = Path("./videos_output")
if not output_dir.exists():
    print("[ERROR] No hay carpeta videos_output")
    sys.exit(1)

videos = sorted(output_dir.glob("video_*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True)
if not videos:
    print("[ERROR] No hay videos en videos_output")
    sys.exit(1)

latest_video = videos[0]
print(f"[*] Usando video: {latest_video}")

# Información de prueba
title = "Test: ¿Este error te roba dinero?"
description = "Video de prueba para verificar la subida a YouTube"
tags = "#test #debug #youtube"

# Intentar subir
result = upload_to_youtube(str(latest_video), title, description, tags)
print(f"\n[{'OK' if result else 'ERROR'}] Resultado: {result}")
