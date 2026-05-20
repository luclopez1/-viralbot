#!/usr/bin/env python3
"""
PRUEBA DE POLLINATIONS + KEN BURNS
Genera 3 imagenes IA + crea un video de prueba con efecto Ken Burns
NO toca el sistema actual - solo prueba
"""

import os
import subprocess
import urllib.parse
import requests
from pathlib import Path

# Carpeta de salida de prueba
TEST_DIR = Path("test_pollinations_output")
TEST_DIR.mkdir(exist_ok=True)

# Prompts de prueba - estilo cinematografico viral
PROMPTS = [
    "cinematic shot of a futuristic robot working at a computer with multiple screens, dramatic blue lighting, hyperrealistic, 4k, professional photography",
    "stack of golden coins and dollar bills on dark wooden table, cinematic lighting, depth of field, luxury aesthetic, 4k photorealistic",
    "young entrepreneur celebrating success in modern penthouse office at night, city lights through window, cinematic style, dramatic lighting, professional",
]


def generate_pollinations_image(prompt: str, output_path: Path, width: int = 1080, height: int = 1920):
    """
    Genera una imagen usando Pollinations.ai (gratis, sin API key)
    Modelo: flux (mejor calidad cinematografica)
    """
    print(f"[*] Generando: {prompt[:60]}...")

    # Encode prompt para URL
    encoded = urllib.parse.quote(prompt)

    # URL de Pollinations - modelo flux para calidad cinematografica
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&model=flux&nologo=true&enhance=true"

    try:
        response = requests.get(url, timeout=120)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"[OK] Guardada: {output_path}")
            return True
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def find_ffmpeg():
    """Busca el binario de FFmpeg"""
    candidates = [
        r"C:\ffmpeg\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        "ffmpeg",
    ]
    for c in candidates:
        if c == "ffmpeg" or os.path.exists(c):
            return c
    return "ffmpeg"


def create_ken_burns_video(images: list, output_path: Path, duration_per_image: float = 5.0):
    """
    Crea un video con efecto Ken Burns (zoom + paneo) sobre cada imagen
    Resultado: video vertical 1080x1920 (formato Short)
    """
    print(f"\n[*] Creando video Ken Burns con {len(images)} imagenes...")

    ffmpeg = find_ffmpeg()
    W, H = 1080, 1920
    fps = 30
    total_frames_per_image = int(duration_per_image * fps)

    # Build filter complex con Ken Burns
    # Cada imagen: zoom progresivo de 1.0 a 1.2 + ligero paneo
    inputs = []
    filters = []
    concats = []

    for i, img in enumerate(images):
        inputs.extend(["-loop", "1", "-t", str(duration_per_image), "-i", str(img)])

        # Ken Burns: zoom de 1.0 a 1.15 a lo largo del clip, centro ligero panning
        # zoompan filter: z='zoom+0.0005' por frame
        zoom_expr = f"z='min(zoom+0.0008,1.2)':d={total_frames_per_image}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps}"

        filters.append(
            f"[{i}:v]scale=2160:3840:force_original_aspect_ratio=increase,"
            f"crop=2160:3840,zoompan={zoom_expr}[v{i}]"
        )
        concats.append(f"[v{i}]")

    filter_complex = ";".join(filters) + ";" + "".join(concats) + f"concat=n={len(images)}:v=1:a=0[out]"

    cmd = [ffmpeg, "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        str(output_path)
    ]

    print(f"[*] Ejecutando FFmpeg (puede tardar 30-60s)...")
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
        print(f"[OK] Video creado: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] FFmpeg fallo:")
        print(e.stderr.decode()[:1000])
        return False


def main():
    print("\n" + "=" * 60)
    print("PRUEBA POLLINATIONS + KEN BURNS")
    print("=" * 60 + "\n")

    # 1. Generar imagenes
    image_paths = []
    for i, prompt in enumerate(PROMPTS):
        img_path = TEST_DIR / f"image_{i+1}.jpg"
        if generate_pollinations_image(prompt, img_path):
            image_paths.append(img_path)
        else:
            print(f"[WARN] Imagen {i+1} fallo, continuando...")

    if len(image_paths) < 1:
        print("\n[ERROR] No se genero ninguna imagen")
        return

    print(f"\n[OK] {len(image_paths)} imagenes generadas en: {TEST_DIR.absolute()}")

    # 2. Crear video Ken Burns
    video_path = TEST_DIR / "test_ken_burns.mp4"
    if create_ken_burns_video(image_paths, video_path, duration_per_image=5.0):
        print("\n" + "=" * 60)
        print("[OK] PRUEBA COMPLETADA")
        print("=" * 60)
        print(f"\nVideo de prueba: {video_path.absolute()}")
        print(f"Imagenes generadas: {TEST_DIR.absolute()}")
        print("\nAbre el video para ver el resultado.")
        print("Si te gusta, integramos en el sistema completo.\n")
    else:
        print("\n[ERROR] No se pudo crear el video")


if __name__ == "__main__":
    main()
