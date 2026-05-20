#!/usr/bin/env python3
"""
HUGGING FACE VIDEO HELPER
Anima imagenes estaticas usando Stable Video Diffusion (SVD)
Gratis con token HF - genera clips de ~4 segundos por imagen
"""

import os
import time
import requests
from pathlib import Path


HF_SVD_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-video-diffusion-img2vid-xt"
HF_TOKEN = os.getenv("HF_API_TOKEN", "")


def animate_image(
    image_path: str,
    output_path: str,
    hf_token: str = None,
    max_retries: int = 4,
    timeout: int = 300,
) -> bool:
    """
    Anima una imagen estatica usando SVD de Hugging Face
    Genera ~25 frames a 6fps = ~4.2 segundos de video

    Args:
        image_path: Ruta a la imagen de entrada (JPG/PNG)
        output_path: Ruta donde guardar el video (.mp4)
        hf_token: Token de Hugging Face (o usa env var HF_API_TOKEN)
        max_retries: Reintentos si el modelo esta cargando
        timeout: Segundos maximos de espera por request

    Returns:
        True si se animo correctamente, False si fallo
    """
    token = hf_token or HF_TOKEN
    if not token:
        print("[WARN] No HF_API_TOKEN encontrado")
        return False

    headers = {"Authorization": f"Bearer {token}"}

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    for attempt in range(max_retries):
        try:
            print(f"[*] HF SVD animando imagen (intento {attempt+1}/{max_retries})...")
            response = requests.post(
                HF_SVD_URL,
                headers=headers,
                data=image_bytes,
                timeout=timeout
            )

            if response.status_code == 200:
                # Guardar video
                with open(output_path, "wb") as f:
                    f.write(response.content)
                size_kb = len(response.content) / 1024
                if size_kb > 10:  # Video valido (>10KB)
                    print(f"[OK] Video animado: {output_path} ({size_kb:.0f}KB)")
                    return True
                else:
                    print(f"[WARN] Video muy pequeño ({size_kb:.1f}KB), reintentando...")

            elif response.status_code == 503:
                # Modelo cargando - esperar
                wait = 30 * (attempt + 1)
                print(f"[WAIT] Modelo cargando, esperando {wait}s...")
                time.sleep(wait)

            elif response.status_code == 429:
                # Rate limit
                print(f"[WAIT] Rate limit, esperando 60s...")
                time.sleep(60)

            else:
                print(f"[WARN] HTTP {response.status_code}: {response.text[:200]}")
                time.sleep(10)

        except requests.exceptions.Timeout:
            print(f"[WARN] Timeout en intento {attempt+1}, reintentando...")
            time.sleep(15)
        except Exception as e:
            print(f"[WARN] Error: {e}")
            time.sleep(10)

    print(f"[ERROR] No se pudo animar imagen tras {max_retries} intentos")
    return False


def animate_batch(
    image_paths: list,
    output_dir: str,
    hf_token: str = None,
    prefix: str = "clip",
) -> list:
    """
    Anima un batch de imagenes
    Retorna lista de paths a los videos generados (o None si fallo)
    Incluye Ken Burns como fallback si HF falla
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    failed = []

    for i, img_path in enumerate(image_paths):
        clip_path = output_dir / f"{prefix}_{i+1:02d}.mp4"
        print(f"\n[*] Animando escena {i+1}/{len(image_paths)}: {Path(img_path).name}")

        if animate_image(img_path, str(clip_path), hf_token=hf_token):
            results.append(str(clip_path))
        else:
            print(f"[WARN] HF fallo para escena {i+1}, se usara Ken Burns")
            results.append(None)  # Marcamos como fallido para Ken Burns
            failed.append(i)

    success = len(image_paths) - len(failed)
    print(f"\n[OK] {success}/{len(image_paths)} clips animados con HF")
    if failed:
        print(f"[INFO] Escenas {[f+1 for f in failed]} usaran Ken Burns")

    return results


if __name__ == "__main__":
    print("Test HF Video Animation")
    if not HF_TOKEN:
        print("[ERROR] Necesitas HF_API_TOKEN en .env o como variable de entorno")
        print("Obtenlo en: https://huggingface.co/settings/tokens")
    else:
        print(f"[OK] Token encontrado: {HF_TOKEN[:8]}...")
