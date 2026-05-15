#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from pathlib import Path

OUTPUT_DIR = Path("./videos_output")
TEMP_DIR = Path("./temp")

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

def create_demo_image():
    """Crea una imagen de prueba usando PIL"""
    print("[IMG] Creando imagen demo...")
    try:
        from PIL import Image, ImageDraw

        img = Image.new('RGB', (1080, 1920), color='#0a0a0a')
        d = ImageDraw.Draw(img)

        colors = ['#1a1a2e', '#16213e', '#0f3460']
        for i in range(len(colors)):
            start_y = int((i * 1920) / len(colors))
            end_y = int(((i + 1) * 1920) / len(colors))
            d.rectangle([(0, start_y), (1080, end_y)], fill=colors[i])

        text1 = "YOUTUBE IA"
        text2 = "Automation System"
        text3 = "Video generado automaticamente"

        d.multiline_text((540, 800), text1, fill="white", anchor="mm")
        d.text((540, 900), text2, fill="#00ff00", anchor="mm")
        d.text((540, 1100), text3, fill="#aaaaaa", anchor="mm")

        img.save(TEMP_DIR / "demo_image.png")
        print("[OK] Imagen creada: demo_image.png")
        return str(TEMP_DIR / "demo_image.png")
    except ImportError:
        print("[WARN] PIL no instalada, creando imagen solida...")
        from PIL import Image
        img = Image.new('RGB', (1080, 1920), color='#000000')
        img.save(TEMP_DIR / "demo_image.png")
        return str(TEMP_DIR / "demo_image.png")

def create_demo_audio():
    """Crea un audio de prueba usando text-to-speech"""
    print("[AUDIO] Generando audio demo...")
    try:
        import edge_tts
        import asyncio

        texto = "Bienvenido al sistema automatico de generacion de videos para YouTube. Este es un video de demostracion creado con inteligencia artificial."

        async def generate():
            communicate = edge_tts.Communicate(texto, voice="es-ES-AlvaroNeural")
            await communicate.save(str(TEMP_DIR / "demo_audio.mp3"))

        asyncio.run(generate())
        print("[OK] Audio creado: demo_audio.mp3")
        return str(TEMP_DIR / "demo_audio.mp3")
    except Exception as e:
        print(f"[WARN] Error generando audio: {e}")
        print("   Generando audio silencioso de 5 segundos...")
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", "5", str(TEMP_DIR / "demo_audio.mp3")
        ]
        subprocess.run(cmd, capture_output=True)
        return str(TEMP_DIR / "demo_audio.mp3")

def create_video_with_ffmpeg(image: str, audio: str, output: str):
    """Crea video a partir de imagen y audio"""
    print("[VIDEO] Creando video con FFmpeg...")

    try:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", "5", "-i", image,
            "-i", audio,
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            output
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"[OK] Video creado: {output}")
            return True
        else:
            print(f"[ERROR] Error FFmpeg: {result.stderr}")
            return False

    except FileNotFoundError:
        print("[ERROR] FFmpeg no encontrado!")
        print("   Descargalo de: https://ffmpeg.org/download.html")
        print("   O en Windows: choco install ffmpeg")
        return False

def main():
    print("\n" + "="*60)
    print("DEMO - YouTube IA Automation")
    print("="*60 + "\n")

    image_path = create_demo_image()
    audio_path = create_demo_audio()

    video_path = OUTPUT_DIR / "demo_video.mp4"
    success = create_video_with_ffmpeg(image_path, audio_path, str(video_path))

    if success:
        print("\n" + "="*60)
        print("[OK] DEMO COMPLETADA")
        print("="*60)
        print(f"\nArchivo generado: {video_path}")
        print(f"Tamaño: {os.path.getsize(video_path) / 1024 / 1024:.1f} MB")
        print(f"\nProximos pasos:")
        print(f"   1. Edita .env con tus API keys")
        print(f"   2. Ejecuta: python generate_content.py")
        print(f"   3. Para automatizar: npm install -g n8n")
        print("\n")
    else:
        print("\n[ERROR] Error creando video. Verifica FFmpeg.\n")

if __name__ == "__main__":
    main()
